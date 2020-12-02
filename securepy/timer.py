import multiprocessing
import multiprocessing.pool
import typing as t


class NoDaemonProcess(multiprocessing.Process):
    """
    This class overrides `multiprocessing.Process` in order to make sure
    that `daemon` property will stay False, this is necessary, because
    daemonic processes aren't allowed to have children by multiprocessing.
    """
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


# We obtain the type from `get_context` function because it's different
# depending on the operating system used
class NoDaemonContext(type(multiprocessing.get_context())):
    """
    This makes sure we use non-daemonic process for given
    context (based on running OS), this is necessary, because
    daemonic processes aren't allowed to have children by multiprocessing.
    """
    Process = NoDaemonProcess


# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class NestablePool(multiprocessing.pool.Pool):
    """
    Ensure that all processes within this pool will always stay non-daemonic,
    this is done because daemonic processes aren't allowed to have
    children by multiprocessing.
    """
    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()  # noqa
        super(NestablePool, self).__init__(*args, **kwargs)


def timed_run(time_limit: int, func: t.Callable, args=None, kwargs=None) -> t.Any:
    """
    This function is used as a wrapper for given function `func`, it
    enforces given `time_limit` (in seconds) on the execution of
    this given function.

    If a function takes more time to execute than the specified
    limit, it will be terminated and `TimeoutError` will be raised.
    Otherwise, it's return value will be returned

    It works by running this function concurrently with a timer, using
    multiprocessing, we than wait for given amount of seconds for the function
    to end and return it's value, if this is before the time limit is reached,
    this value will be returned and the branched process will be joined back,
    otherwise, the function process will be terminated and the error will be raised.

    (NOTICE: This is NOT a decorator, only a wrapper, decorator functionality
    can't be added, because multiprocessing uses `pickle` internally which
    tries to import given function (`func`) which wouldn't be the same function
    as the passed one since it would be altered by the decorator itself, causing
    `PicklingError`)
    """
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    pool = NestablePool(processes=1)
    result = pool.apply_async(func, args=args, kwds=kwargs)

    try:
        value = result.get(time_limit)
    except multiprocessing.TimeoutError:
        pool.terminate()
        pool.close()
        pool.join()
        raise TimeoutError(f"Function took longer than the allowed time limit ({time_limit})")

    pool.close()
    pool.join()

    return value
