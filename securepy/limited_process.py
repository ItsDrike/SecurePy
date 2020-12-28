import subprocess
import sys
import threading
import typing as t

from securepy.stdio import MemoryOverflow


class ExcThread(threading.Thread):
    """
    This is an override for general `threading.Thread` class
    in order to provide the ability to store exceptions
    """
    def run(self) -> None:
        """
        Method representing the thread's activity.

        This method runs the provided `_target` function,
        in case any exception occures in it, it will be stored
        as `self.exc`
        """
        try:
            if self._target:  # type: ignore (Pylance doesn't recognize this variable)
                self._target(*self._args, **self._kwargs)  # type: ignore (Pylance doesn't recognize these variables)
        except BaseException as e:
            self.exc = e
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs  # type: ignore (Pylance doesn't recognize these variables)

    def join(self, timeout: t.Optional[float]) -> None:
        """
        In case an exception has occured while the thread was running,
        automatically raise it from this method.
        """
        # We shouldn't be getting any return value, but store it in case of overrides
        ret = super().join(timeout=timeout)
        if hasattr(self, "exc") and self.exc:
            raise self.exc

        return ret


class LimitedProcess(subprocess.Popen):
    _TXT = t.Union[bytes, str]
    _CMD = t.Union[_TXT, t.Sequence[_TXT]]

    def __init__(
        self,
        args: _CMD,
        max_output_size: t.Optional[int],
        read_chunk_size: int,
        **kwargs
    ) -> None:
        super().__init__(args, **kwargs)  # type: ignore (Pylance can't resolve Popen.__init__ properly)

        self.read_chunk_size = read_chunk_size
        self.max_output_size = max_output_size
        self.output_size = 0

    def _readerthread(self, fh, buffer):
        """
        Read from STDOUT/STDERR inside of a thred
        by chunks of `read_chunk_size` until EOF is hit
        or we reach `max_output_size`.
        """
        while True:
            out = fh.read(self.read_chunk_size)
            self.output_size += sys.getsizeof(out)

            if not out:  # "" or None
                break

            if self.max_output_size is not None and self.output_size > self.max_output_size:
                fh.close()
                raise MemoryOverflow(
                    used_memory=self.output_size,
                    max_memory=self.max_output_size
                )

            buffer.append(out)
        fh.close()

    def _communicate(self, input, endtime, orig_timeout):
        # Start reader threads feeding into a list hanging off of this
        # object, unless they've already been started.
        if self.stdout and not hasattr(self, "_stdout_buff"):
            self._stdout_buff = []
            self.stdout_thread = ExcThread(
                target=self._readerthread,
                args=(self.stdout, self._stdout_buff)
            )
            self.stdout_thread.daemon = True
            self.stdout_thread.start()

        if self.stderr and not hasattr(self, "_stderr_buff"):
            self._stderr_buff = []
            self.stderr_thread = ExcThread(
                target=self._readerthread,
                args=(self.stderr, self._stderr_buff)
            )
            self.stderr_thread.daemon = True
            self.stderr_thread.start()

        if self.stdin:
            self._stdin_write(input)  # type: ignore (Pylance doesn't recognize this variable)

        # Wait for the reader threads, or time out. If we time out, the
        # threads remain reading and the fds left open in case the user
        # calls communicate again.
        if self.stdout is not None:
            self.stdout_thread.join(self._remaining_time(endtime))  # type: ignore (Pylance doesn't recognize this function)
            if self.stdout_thread.is_alive():
                raise subprocess.TimeoutExpired(self.args, orig_timeout)
        if self.stderr is not None:
            self.stderr_thread.join(self._remaining_time(endtime))  # type: ignore (Pylance doesn't recognize this function)
            if self.stderr_thread.is_alive():
                raise subprocess.TimeoutExpired(self.args, orig_timeout)

        # Collect the output from and close both pipes, now that we know
        # both have been read successfully.
        stdout = None
        stderr = None
        if self.stdout:
            if self._stdout_buff != []:
                stdout = self._stdout_buff
            self.stdout.close()
        if self.stderr:
            if self._stderr_buff != []:
                stderr = self._stderr_buff
            self.stderr.close()

        # All data exchanged.  Translate lists into strings.
        if stdout is not None:
            stdout = "".join(stdout)
        if stderr is not None:
            stderr = "".join(stderr)

        return (stdout, stderr)
