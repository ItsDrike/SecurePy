import typing as t
from functools import wraps
from multiprocessing import Process


class TimeLimiter():
    """
    This class is used as a decorator to limit function
    execution of the decorated function by specified amount
    of seconds.

    If a function takes more time to execute than the specified
    limit, it will be terminated and `TimeoutError` will be raised.

    Note that any passed function can't have any return value due
    to multiprocessing limitation of sharing values between processes.
    (In case a return value is present, `RuntimeWarning` will be raised
    and the return value will change to `None`).
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
            timer = Process(target=wrapped, args=args, kwargs=kwargs)
            timer.start()
            # Wait for `self.time_limit` and join
            timer.join(self.time_limit)

            if timer.is_alive():
                timer.terminate()
                raise TimeoutError(f"Function `{func.__name__}` took longer than the allowed time limit ({self.time_limit})")
        return inner
