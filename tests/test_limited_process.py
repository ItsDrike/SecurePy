import subprocess
import sys
import unittest

from securepy import LimitedProcess, MemoryOverflow


class LimitedProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.max_out_memory = 1_000  # 1,000 characters maximum
        cls.chunk_read_memory = 10  # Read chunks of 100 characters

        if sys.platform in ["linux", "linux32", "darwin", "win32"]:
            # This process will run without running over maximuim output memory
            cls.safe_str = "hello there"
            cls.safe_args = ["echo", cls.safe_str]

            # This process should fail with `MemoryOverflow` because it ran over
            # maximum allowed output memory (1,000 characters - bytes)
            cls.unsafe_str = "hello" * 10_000
            cls.unsafe_args = ["echo", cls.unsafe_str]
        else:
            # In case we encounter unknown operating system,
            # we can't know what command it uses as print, because
            # of this, we must raise an error
            raise RuntimeError("Unknown operating system")

    def test_short_stdout(self):
        """Run process with short STDOUT not going over given `max_out_memory` limit."""
        proc = LimitedProcess(
            args=self.safe_args,  # type: ignore (Pylance can't resolve args properly)
            max_output_size=self.max_out_memory,
            read_chunk_size=self.chunk_read_memory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate()

        if proc.poll() is None:
            proc.kill()  # If the process didn't end (which it shouldn't here) terminate it with SIGKILL
            self.fail("Process didn't finish after communicate (killed with SIGKILL)")

        self.assertEqual(stdout, self.safe_str + "\n")

    def test_memory_overflow(self):
        """Run process with long STDOUT going over given `max_out_memory` limit."""
        proc = LimitedProcess(
            args=self.unsafe_args,  # type: ignore (Pylance can't resolve args properly)
            max_output_size=self.max_out_memory,
            read_chunk_size=self.chunk_read_memory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        with self.assertRaises(MemoryOverflow):
            stdout, stderr = proc.communicate()

        if proc.poll() is None:
            proc.kill()  # If the process didn't end (which it shouldn't here) terminate it with SIGKILL

        self.assertNotEqual(proc.stdout, self.unsafe_str)
