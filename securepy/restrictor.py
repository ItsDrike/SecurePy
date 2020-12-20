import subprocess
import typing as t

from securepy.stdcapture import read_process_output


class Restrictor:
    def __init__(
        self,
        max_exec_time: int,
        restriction_scope: t.Literal[1, 2, 3] = 2,
        max_process_memory: int = 5_000_000,  # 5MB
        max_output_memory: int = 10_000,  # 100kB
        output_chunk_read_size: int = 10_000,  # characters (bytes)
        python_path: str = "python"  # default to `python` in PATH
    ):
        """
        `max_exec_time` is the maximum time limit in seconds for which exec function
        will be allowed to run. After this timelimit ends, exec will be terminated
        and `TimeoutError` will be raised.

        `restriction_scope` will determine how restricted will the
        python code execution be. Restriction levels are as follows:
        - 0: Unrestricted globals (full builtins as they are in this file)
        - 1: Restricted globals (removed some unsafe builtins)
        - 2 (RECOMMENDED): Secure globals (only using relatively safe builtins)
        - 3: No globals (very limiting but quite safe)

        `max_process_memory` is the total amount of allowed memory single exec process can
        use. Exceeding this will raise `MemoryOverflow`

        `max_output_memory` is the maximum allowed memory for STDOUT/STDERR of the process.
        Exceeding this amount will raise `MemoryOverflow`

        `std_chunk_read_size` is the size (amount of characters) in bytes which will be used
        to read the single output chunk from given process, which will then be added to rest of
        the STDOUT/STDERR.

        `python_path` is the path to python interpreter file which will be called to run the
        specified code.
        """
        self.max_exec_time = max_exec_time
        self.restriction_scope = restriction_scope
        self.max_process_memory = max_process_memory
        self.max_output_memory = max_output_memory
        self.output_chunk_read_size = output_chunk_read_size
        self.python_path = python_path

    def execute(self, code: str) -> str:
        process = subprocess.Popen(
            [
                self.python_path, "securepy/executor.py",
                str(self.restriction_scope), code
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        out = read_process_output(
            process,
            self.output_chunk_read_size,
            self.max_output_memory,
        )

        return out
