import subprocess
import sys
import typing as t
from functools import wraps
from io import StringIO


class MemoryOverflow(Exception):
    def __init__(self, used_memory: int, max_memory: int, message: t.Optional[str] = None, *args, **kwargs) -> None:
        self.used_memory = used_memory
        self.max_memory = max_memory
        if not message:
            message = f"Maximum STDOUT/STDERR memory surpassed ({used_memory} > {max_memory})"
        super().__init__(message, *args, **kwargs)


class LimitedStringIO(StringIO):
    """Override `io.StringIO` and apply a maximum memory limitation"""
    def __init__(self, max_memory: int, initial_value: t.Optional[str] = None, newline: t.Optional[str] = None) -> None:
        super().__init__(initial_value=initial_value, newline=newline)
        self.max_memory = max_memory

    def write(self, __s: str) -> int:
        """Override write method to apply memory limitation."""
        used_memory = sys.getsizeof(__s) + sys.getsizeof(self.getvalue())
        if used_memory < self.max_memory:
            return super().write(__s)
        else:
            raise MemoryOverflow(used_memory, self.max_memory)


class StdCapture:
    """
    This class is used to capture STDOUT & STDERR of given
    function, it can work as a wrapper, decorator or context manager.

    Context Manager:
        captured_std = StdCapture()
        with captured_std:
            print("hello")

        captured_std.stdout  # <-- will contain the captured STDOUT (str)

    Wrapper:
        def foo(*args, **kwargs):
            print("hello")

        captured_std = StdCapture()
        captured_std.capture(foo, args=None, kwargs=None)

        captured_std.stdout  # <-- will contain the captured STDOUT (str)

    Decorator:
        captured_std = StdCapture()

        @captured_std
        def foo(*args, **kwargs):
            print("hello")

        foo(*args, **kwargs)

        captured_std.stdout  # <-- will contain the captured STDOUT (str)

    You can also use captured_std.stderr to obtain captured STDERR.

    If you don't want to lose STDOUT/STDERR captured values after function is done running,
    you can specify `auto_reset=False` on init and run `StdCapture.reset` manually when needed.
    You can also specify `memory_limit=100_000` in bytes (100kB) which will limit saved
    std storage size to that amount.
    """

    def __init__(self, auto_reset: bool = True, memory_limit: int = 100_000):
        self.auto_reset = auto_reset
        self.memory_limit = memory_limit

        self.capturing_stdout = LimitedStringIO(self.memory_limit)
        self.capturing_stderr = LimitedStringIO(self.memory_limit)

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

    @property
    def stdout(self) -> str:
        """
        Return captured STDOUT in form of string. This will
        return empty string in case no STDOUT was captured.
        """
        return self.capturing_stdout.getvalue()

    @property
    def stderr(self) -> str:
        """
        Return captured STDERR in form of string. This will
        return empty string in case no STDERR was captured.
        """
        return self.capturing_stderr.getvalue()

    def __enter__(self) -> None:
        """
        Temporarely override `sys.stdout` and `sys.stderr`
        to use `StringIO` to capture standard output & error.

        Captured STDOUT/STDERR can be obtained by accessing
        `StdCapture.stdout`/`StdCapture.stderr`.
        """
        if self.auto_reset:
            self.reset()

        self.override_std()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Restore the normal printing STDOUT/STDERR capabilities.
        """
        self.restore_std()

    def __call__(self, func: t.Callable) -> t.Any:
        """
        This decorates given `func` and captures it's STDOUT/STDERR
        when it's run.
        Return value will be the original return from `func`.

        STDOUT & STDERR will be captured and can be obtained by doing
        `StdCapture.stdout`/`StdCapture.stderr`.

        The functionality is handeled in `StdCapture.capture`, this method
        serves only as a decorator for given `func`.
        """
        @wraps(func)
        def inner(*args, **kwargs) -> t.Any:
            return self.capture(func, args, kwargs)
        return inner

    def capture(self, func: t.Callable, args=None, kwargs=None) -> t.Any:
        """
        This runs given `func` while capturing it's STDOUT/STDERR.
        Return value will be the original return from `func`.

        STDOUT & STDERR will be captured and can be obtained by doing
        `StdCapture.stdout`/`StdCapture.stderr`.

        This acts as a wrapper for given `func`, it immediately runs it,
        (if you want to decorate, call instance directly - `__call__`)
        """
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()

        if self.auto_reset:
            self.reset()

        with self:
            return func(*args, **kwargs)

    def override_std(self) -> None:
        """
        Override `sys.stdout` and `sys.stderr` to use
        `StringIO` instead to capture standard output & error.
        """
        if not isinstance(sys.stdout, StringIO):
            sys.stdout = self.capturing_stdout
        if not isinstance(sys.stderr, StringIO):
            sys.stderr = self.capturing_stderr

    def restore_std(self) -> None:
        """
        Revert override of `sys.stdout` and `sys.stderr`
        to restore normal printing capabilities without capturing.
        """
        if isinstance(sys.stdout, StringIO):
            sys.stdout = self.old_stdout
        if isinstance(sys.stderr, StringIO):
            sys.stderr = self.old_stderr

    def reset(self) -> None:
        """Reset stored captured stdout & stderr strings."""
        self.capturing_stdout = LimitedStringIO(self.memory_limit)
        self.capturing_stderr = LimitedStringIO(self.memory_limit)

    def __repr__(self) -> str:
        return f"<StdCapture(stdout={self.stdout}, stderr={self.stderr})"


def read_process_std(
    process: subprocess.Popen,
    read_chunk_size: int,
    max_size: int,
) -> t.Tuple[str, str]:
    """
    Start reading from STDOUT and STDERR, stop in case stdout limit is reached or process stops.

    In case output from STDOUT will reach the max limit, the subprocess will be terminated by SIGKILL.
    """
    output_size = 0
    stdout = []
    stderr = []

    while process.poll() is None:
        chars = process.stdout.read(read_chunk_size)
        output_size += sys.getsizeof(chars)
        stdout.append(chars)

        chars = process.stderr.read(read_chunk_size)
        output_size += sys.getsizeof(chars)
        stderr.append(chars)

        if output_size > max_size:
            print("Output exceeded stdout limit, terminating NsJail with SIGKILL")
            process.kill()
            break

    # Wait for process termination
    process.wait()
    return "".join(stdout), "".join(stderr)
