import multiprocessing
import multiprocessing.pool
import typing as t
from functools import wraps


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
    tries to import given function (`foo`) which wouldn't be the same function
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


class TimedFunction():
    """
    This class is used as a decorator to limit function
    execution of the decorated function by specified amount
    of seconds.

    If a function takes more time to execute than the specified
    limit, it will be terminated and `TimeoutError` will be raised.

    NOTICE: In order to provide a decorator functionality like this
    any passed function can't have any return value because multiprocessing
    has certain limitations for sharing values between processes.
    (In case a return value is present, `RuntimeWarning` will be raised
    and the return value will change to `None`).

    If you need to access the return value, you should use `timed_run` wrapper
    function instead, it works only as a wrapper, not a full decorator, but
    because of this it's able to extract the returned value.
    """

    def __init__(self, time_limit: int):
        self.time_limit = time_limit

    def _capture_return(self, func: t.Callable) -> t.Callable:
        """
        Decorate given function and capture it's return value,
        if this value isn't `None`, raise a `RuntimeWarning` and
        return `None`.

        This is necessary, because  multiprocessing can't handle
        transferring values between processes (apart from ctypes).
        """
        @wraps(func)
        def inner(*args, **kwargs):
            if ret := func(*args, **kwargs) is not None:
                raise RuntimeWarning(
                    f"Function `{func.__name__}` attempted to return a value: `{ret}`, "
                    "but value return isn't supported with TimeLimiter as it's not possible "
                    "to share values between processes."
                )
        return inner

    def __call__(self, func: t.Callable) -> t.Callable:
        """
        Decorate given function and run it concurrently with a timer,
        using multiprocessing. If the timer reaches specified time limit,
        and the function didn't end, raise `TimeoutError`, otherwise return `None`.
        """
        @wraps(func)
        def inner(*args, **kwargs) -> None:
            wrapped = self._capture_return(func)
            proc = multiprocessing.Process(target=wrapped, args=args, kwargs=kwargs)
            proc.start()
            # Wait for `self.time_limit` and join
            # The joining will happen sooner, in case the process ends before the time limit
            proc.join(self.time_limit)

            if proc.is_alive():
                proc.terminate()
                raise TimeoutError(f"Function `{func.__name__}` took longer than the allowed time limit ({self.time_limit})")
        return inner
