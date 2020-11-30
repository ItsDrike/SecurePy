import re
import subprocess
import textwrap
import typing as t
from pathlib import Path
from tempfile import NamedTemporaryFile

from securepy.stdcapture import read_process_std

# Default values
NSJAIL_PATH = Path("/usr/sbin/nsjail")
PYTHON_PATH = Path("/usr/bin/python")
CGROUP_MEMORY_PATH = Path("/sys/fs/cgroup/memory/NSJAIL")
CGROUP_PIDS_PATH = Path("/sys/fs/cgroup/pids/NSJAIL")

TIME_LIMIT = 6  # 6 seconds
ALLOWED_MEMORY = 64_000_000  # 64 MB
MAX_STDOUT = 1_000_000  # 1 MB
READ_CHUNK_SIZE = 10_000  # chars

NSJAIL_CONFIG = "./config/nsjail.cfg"

NSJAIL_LOG_PATTERN = re.compile(
    r"\[(?P<level>(I)|[DWEF])\]\[.+?\](?(2)|(?P<func>\[\d+\] .+?:\d+ )) ?(?P<msg>.+)"
)
LOG_BLACKLIST = ("Process will be ",)


class Sandbox:
    def __init__(
        self,
        nsjail_path: Path = NSJAIL_PATH,
        python_path: Path = PYTHON_PATH,
        cgroup_memory_path: Path = CGROUP_MEMORY_PATH,
        cgroup_pids_path: Path = CGROUP_PIDS_PATH,
        allowed_memory: int = ALLOWED_MEMORY,
        max_stdout: int = MAX_STDOUT,
        read_chunk_size: int = READ_CHUNK_SIZE,
        time_limit: int = TIME_LIMIT,
    ):
        self.nsjail = nsjail_path
        self.python = python_path
        self.cgroup_memory = cgroup_memory_path
        self.cgroup_pids = cgroup_pids_path

        self.allowed_memory = allowed_memory
        self.max_stdout = max_stdout
        self.read_chunk_size = read_chunk_size
        self.time_limit = time_limit

        self._construct_cgroups()

    def _construct_cgroups(self) -> None:
        """
        Create PIDs and memory cgroups for NsJail.

        This must be done here, because NsJail doesn't usually have
        sufficient privileges.

        Disable memory swapping.
        """
        self.cgroup_memory.mkdir(parents=True, exist_ok=True)

        # minimum swap limit: `memory.limit_in_bytes`
        (self.cgroup_memory / "memory.limit_in_bytes").write_text(str(self.allowed_memory), encoding="utf-8")

        try:
            (self.cgroup_memory / "memory.memsw.limit_in_bytes").write_text(str(self.allowed_memory), encoding="utf-8")
        except PermissionError:
            print(
                "Failed to set memory swap limit for the cgroup"
                "Make sure swap memory is disabled on the system. "
            )

    @staticmethod
    def _get_nsjail_log(received_log: t.Iterable[str]) -> None:
        """Obtain NsJail's log messages."""
        for line in received_log:
            match = NSJAIL_LOG_PATTERN.fullmatch(line)
            if match is None:
                print(f"Failed to parse log line `{line}`")
                continue

            msg = match["msg"]

            if any(msg.startswith(s) for s in LOG_BLACKLIST):
                # Skip blacklisted messages.
                continue

            if match["level"] == "D":
                print(f"DEBUG: {msg}")
            elif match["level"] == "I":
                if msg.startswith("pid="):
                    print(f"INFO: {msg}")
            elif match["level"] == "W":
                print(f"WARNING: {msg}")
            else:
                print(f"ERROR: {msg}")

    def execute(self, code: str) -> subprocess.CompletedProcess:
        """
        Securely execute python code in an isolated sandbox environment
        return a completed process.
        """
        with NamedTemporaryFile() as nsj_log:
            args = (
                self.nsjail,
                "--config", NSJAIL_CONFIG,
                "--log", nsj_log.name,
                "--time_limit", str(self.time_limit),
                f"--cgroup_mem_max={self.allowed_memory}",
                "--cgroup_mem_mount", str(self.cgroup_memory.parent),
                "--cgroup_mem_parent", self.cgroup_memory.name,
                "--cgroup_pids_max=1",
                "--cgroup_pids_mount", str(self.cgroup_pids.parent),
                "--cgroup_pids_parent", self.cgroup_pids.name,
                "--",
                self.python, "-Iqu", "-c", code
            )

            msg = f"Executing code:\n{textwrap.indent(code, '   ')}"

            print(f"INFO: {msg}")

            try:
                nsjail = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            except ValueError:
                return subprocess.CompletedProcess(args, -1, "ValueError: embedded null byte", None)

            stdout, stderr = read_process_std(nsjail, self.read_chunk_size, self.max_stdout)

            # When you send signal `N` to a subprocess to terminate it using Popen, it
            # will return `-N` as it's exit code. As we normally get `N + 128` back, we
            # convert negative exit codes to the `N + 128` form.
            returncode = -nsjail.returncode + 128 if nsjail.returncode < 0 else nsjail.returncode

            log_lines = nsj_log.read().decode("utf-8").splitlines()
            if not log_lines and returncode == 255:
                # NsJail failed to parse arguments so log output will still be in stdout
                log_lines = stdout.splitlines()

            self._get_nsjail_log(log_lines)

        print(f"INFO: nsjail return code: {returncode}")
        return subprocess.CompletedProcess(args, returncode, stdout, stderr)
