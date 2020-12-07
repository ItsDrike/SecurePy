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
        if used_memory <= self.max_memory:
            return super().write(__s)
        else:
            raise MemoryOverflow(used_memory, self.max_memory)

    def __repr__(self) -> str:
        return f"<LimitedStringIO max_memory={self.max_memory}, value={self.getvalue()}>"


class IOCage:
    """
    This class is used to capture STDOUT and STDERR, while able to simulate STDIN
    to given function it can work as a wrapper, decorator or context manager.

    Context Manager:
        captured_std = IOCage(stdin='bye')  # `stdin` as a param to init. If not specified, `sys.stdin` will not be overrided
        with captured_std:
            print("hello")
            print(input())  # Will print 'bye' to stdout

        captured_std.stdout  # <-- will contain the captured STDOUT (str)

    Wrapper:
        def foo(*args, **kwargs):
            print("hello")

        captured_std = IOCage()
        captured_std.capture(foo, args=None, kwargs=None)  # Can pass `stdin` or it will default to value from init

        captured_std.stdout  # <-- will contain the captured STDOUT (str)

    Decorator:
        captured_std = IOCage()

        @captured_std
        def foo(*args, **kwargs):
            print("hello")

        foo(*args, **kwargs)

        captured_std.stdout  # <-- will contain the captured STDOUT (str)

    You can also use captured_std.stderr to obtain captured STDERR.

    If you don't want to lose STDOUT/STDERR captured values after function is done running,
    you can specify `auto_reset=False` on init and run `IOCage.reset` manually when needed.
    You can also specify `memory_limit=100_000` in bytes (100kB) which will limit saved
    std storage size to that amount.
    """

    def __init__(
        self,
        auto_reset: bool = True,
        memory_limit: int = 100_000,
        stdin: t.Optional[str] = None,
        enable_stdout: bool = True,
        enable_stderr: bool = True,
    ):
        self.auto_reset = auto_reset
        self.memory_limit = memory_limit

        self.stdin = stdin

        self.enable_stdout = enable_stdout
        self.enable_stderr = enable_stderr

        self.stdout_funnel = LimitedStringIO(self.memory_limit)
        self.stderr_funnel = LimitedStringIO(self.memory_limit)

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        self.old_stdin = sys.stdin

    @property
    def stdout(self) -> str:
        """
        Return captured STDOUT in form of string. This will
        return empty string in case no STDOUT was captured.
        """
        return self.stdout_funnel.getvalue()

    @property
    def stderr(self) -> str:
        """
        Return captured STDERR in form of string. This will
        return empty string in case no STDERR was captured.
        """
        return self.stderr_funnel.getvalue()

    def __enter__(self) -> None:
        """
        Temporarely override `sys.stdout`, `sys.stdin` and `sys.stderr`
        to use `LimitedStringIO` to capture standard output & error.

        Captured STDOUT/STDERR can be obtained by accessing
        `IOCage.stdout`/`IOCage.stderr`.
        """
        if self.auto_reset:
            self.reset()

        self.override_std()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Restore the normal STDOUT/STDERR/STDIN capabilities.
        """
        self.restore_std()

    def __call__(self, func: t.Callable, stdin: t.Optional[str] = None) -> t.Any:
        """
        This decorates given `func` and captures it's STDOUT/STDERR
        while simulating it's STDIN, if `self.stdin` is set.
        Return value will be the original return from `func`

        STDOUT & STDERR will be captured and can be obtained by doing
        `IOCage.stdout`/`IOCage.stderr`.

        The functionality is handeled in `IOCage.capture`, this method
        serves only as a decorator for given `func`.
        """
        @wraps(func)
        def inner(*args, **kwargs) -> t.Any:
            return self.capture(func, args, kwargs, stdin)
        return inner

    def capture(self, func: t.Callable, args=None, kwargs=None, stdin: t.Optional[str] = None) -> t.Any:
        """
        This runs given `func` while capturing it's STDOUT/STDERR
        and simulating it's STDIN.
        Return value will be the original return from `func`.

        STDOUT & STDERR will be captured and can be obtained by doing
        `IOCage.stdout`/`IOCage.stderr`.

        This acts as a wrapper for given `func`, it immediately runs it,
        (if you want to decorate, call instance directly - `__call__`)
        """
        old_stdin = self.stdin

        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()
        if stdin is not None:
            self.stdin = stdin

        if self.auto_reset:
            self.reset()

        with self:
            return func(*args, **kwargs)

        self.stdin = old_stdin

    def override_std(self) -> None:
        """
        Override `sys.stdout`, `sys.stdin` and `sys.stderr` to use
        `StringIO` instead to capture standard output & error.
        """
        if not isinstance(sys.stdout, StringIO) and self.enable_stdout:
            sys.stdout = self.stdout_funnel
        if not isinstance(sys.stderr, StringIO) and self.enable_stderr:
            sys.stderr = self.stderr_funnel
        if not isinstance(sys.stdin, StringIO) and self.stdin:
            sys.stdin = StringIO(self.stdin)

    def restore_std(self) -> None:
        """
        Revert override of `sys.stdout` and `sys.stderr`
        to restore normal printing capabilities without capturing.
        """
        if isinstance(sys.stdout, LimitedStringIO):
            sys.stdout = self.old_stdout
        if isinstance(sys.stderr, LimitedStringIO):
            sys.stderr = self.old_stderr
        if isinstance(sys.stdin, StringIO):
            sys.stdin = self.old_stdin

    def reset(self) -> None:
        """Reset stored captured stdout & stderr strings."""
        self.stdout_funnel = LimitedStringIO(self.memory_limit)
        self.stderr_funnel = LimitedStringIO(self.memory_limit)

    def __repr__(self) -> str:
        return f"<IOCage(stdout={self.stdout}, stderr={self.stderr})"


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
