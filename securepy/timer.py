import typing as t
from functools import wraps
from multiprocessing import Process


class TimeLimiter():
    def __init__(self, time_limit: int):
        self.time_limit = time_limit

    def __call__(self, func: t.Callable) -> t.Callable:
        @wraps(func)
        def inner(*args, **kwargs) -> None:
            timer = Process(target=func, args=args, kwargs=kwargs)
            timer.start()
            # Wait for `self.time_limit` and join
            timer.join(self.time_limit)

            if timer.is_alive():
                timer.terminate()
                raise TimeoutError(f"Function `{func.__name__}` took longer than the allowed time limit ({self.time_limit})")
        return inner
