import os
import subprocess
import typing as t

from securepy.limited_process import LimitedProcess
from securepy.stdio import MemoryOverflow


class Restrictor:
    def __init__(
        self,
        restriction_scope: t.Literal[1, 2, 3] = 2,
        time_limit: t.Optional[t.Union[float, int]] = None,  # seconds
        max_process_memory: t.Optional[int] = 20 * 1024 * 1024,  # 10 MB
        max_output_memory: t.Optional[int] = 10_000,  # 10,000 characters (bytes) maximum
        output_chunk_read_size: int = 1_000,  # characters (bytes)
        python_path: str = "python"  # default to `python` in PATH
    ):
        """
        `time_limit` is the maximum time limit in seconds for which exec function
        will be allowed to run. After this timelimit ends, exec will be terminated
        and `TimeoutError` will be raised.

        `restriction_scope` will determine how restricted will the
        python code execution be. Restriction levels are as follows:
        - 0: Unrestricted globals (full builtins as they are in this file)
        - 1: Restricted globals (removed some unsafe builtins)
        - 2 (RECOMMENDED): Secure globals (only using relatively safe builtins)
        - 3: No globals (very limiting but quite safe)

        `max_process_memory` is the total amount of allowed RAM memory single exec process
        canuse. Exceeding this will raise `MemoryOverflow`. In case it's `None`, process
        will run without RAM limitation.

        `max_output_memory` is the maximum allowed memory for STDOUT/STDERR of the process.
        Exceeding this amount will raise `MemoryOverflow`. In case it's `None`, process
        will run without STDOUT/STDERR memory limitation.

        `std_chunk_read_size` is the size (amount of characters) in bytes which will be used
        to read the single output chunk from given process, which will then be added to rest of
        the STDOUT/STDERR.

        `python_path` is the path to python interpreter file which will be called to run the
        specified code.
        """
        self.time_limit = time_limit
        self.restriction_scope = restriction_scope
        self.max_process_memory = max_process_memory if max_process_memory is not None else -1
        self.max_output_memory = max_output_memory
        self.output_chunk_read_size = output_chunk_read_size
        self.python_path = python_path
        self.executable_path = os.path.dirname(os.path.realpath(__file__)) + "/executor.py"

    def execute(self, code: str) -> subprocess.CompletedProcess:
        args = [
            self.python_path, self.executable_path,
            str(self.restriction_scope), str(self.max_process_memory), code
        ]

        process = LimitedProcess(
            args,
            max_output_size=self.max_output_memory,
            read_chunk_size=self.output_chunk_read_size,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            # out = read_process_output(process, self.output_chunk_read_size, self.max_output_memory, self.time_limit)
            stdout, stderr = process.communicate(timeout=self.time_limit)
        except MemoryOverflow as e:
            return subprocess.CompletedProcess(args, returncode=-1, stdout=None, stderr=str(e))
        except subprocess.TimeoutExpired as e:
            return subprocess.CompletedProcess(args, returncode=-1, stdout=None, stderr=str(e))

        return subprocess.CompletedProcess(args, returncode=1, stdout=stdout, stderr=stderr)
