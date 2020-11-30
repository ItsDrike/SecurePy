import subprocess
import sys
import typing as t
from io import StringIO


class StdCapture:
    def __init__(self):
        self._stdout = None
        self._stderr = None

    @property
    def stdout(self) -> t.Optional[str]:
        if self._stdout is not None:
            return self._stdout.getvalue()

    @property
    def stderr(self) -> t.Optional[str]:
        if self._stderr is not None:
            return self._stderr.getvalue()

    def __enter__(self) -> None:
        """
        Temporarely override `sys.stdout` and `sys.stderr`
        use `StringIO` to capture standard output & error.

        Save the original `sys.stdout` & `sys.stderr` into
        variables: `self.old_stdout` & `self.old_stderr`.
        """
        self._reset()

        self.old_stdout = sys.stdout
        if self._stdout is None:
            self._stdout = StringIO()
        sys.stdout = self._stdout

        self.old_stderr = sys.stderr
        if self._stderr is None:
            self._stderr = StringIO()
        sys.stderr = self._stderr

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Restore the original functionality of `sys.stdout`
        and `sys.stderr`.
        """
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

    def __call__(self, func: t.Callable) -> t.Tuple[t.Optional[str], t.Optional[str], t.Any]:
        """
        Call a provided `func` function while capturing it's
        stdout, stderr and return value.

        Once the function ends, return a tuple of `(stdout, stderr, func_return)`
        """
        self._reset()
        with self:
            out = func()

        return self.stdout, self.stderr, out

    def _reset(self) -> None:
        self._stdout = None
        self._stderr = None


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
