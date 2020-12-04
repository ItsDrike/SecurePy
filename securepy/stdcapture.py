import subprocess
import sys
import typing as t
from io import StringIO


class StdCapture:
    def __init__(self, auto_reset: bool = True):
        self.auto_reset = auto_reset

        self.capturing_stdout = StringIO()
        self.capturing_stderr = StringIO()

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

    def __call__(self, func: t.Callable) -> t.Tuple[t.Optional[str], t.Optional[str], t.Any]:
        """
        Call a provided `func` function while capturing it's stdout.
        This will return the original function's return value.
        STDOUT & STDERR will be captured and can be obtained by doing
        `StdCapture.stdout`/`StdCapture.stderr`.
        """
        if self.auto_reset:
            self.reset()

        with self:
            return func()

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
        self.capturing_stdout = StringIO()
        self.capturing_stderr = StringIO()

    def __repr__(self) -> str:
        return f"<Restrictor(stdout={self.stdout}, stderr={self.stderr})"


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
