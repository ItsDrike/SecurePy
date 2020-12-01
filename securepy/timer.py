import typing as t
from functools import wraps
from multiprocessing import Process


class TimeLimiter():
    def __init__(self, time_limit: int):
        self.time_limit = time_limit

    def _capture_return(self, func: t.Callable) -> t.Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            # Check if function returned some value, if it did
            # raise a runtime warning because multiprocessing can't
            # handle transferring values between processes (apart from ctypes)
            if ret := func(*args, **kwargs):
                raise RuntimeWarning(
                    f"Function `{func.__name__}` attempted to return a value: `{ret}`, "
                    "but value return isn't supported with TimeLimiter as it's not possible "
                    "to share values between processes."
                )
        return inner

    def __call__(self, func: t.Callable) -> t.Callable:
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
