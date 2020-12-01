import typing as t

from securepy.security import RESTRICTED_GLOBALS, SAFE_GLOBALS, UNRESTRICTED_GLOBALS
from securepy.stdcapture import StdCapture
from securepy.timer import TimeLimiter


class Restrictor:
    """
    Prepare isolated python exec session
    """
    def __init__(self, max_exec_time: int, restriction_scope: t.Literal[0, 1, 2, 3] = 2):
        """
        `restriction_level` will determine how restricted will the
        python code execution be. Restriction levels are as follows:
        - 0: No restriction (regular exec)
        - 1: Restricted globals (removed some unsafe globals)
        - 2 (RECOMMENDED): Secure globals (only using relatively safe globals)
        - 3: No globals (very limiting but quite safe)
        `max_exec_time` is the maximum time limit in seconds for which exec function
        will be allowed to run. After this timelimit ends, exec will be terminated
        and `TimeoutError` will be raised.
        """
        self.max_exec_time = max_exec_time
        self.restriction_scope = restriction_scope
        self._set_global_scope(self.restriction_scope)

        self.stdcapture = StdCapture()
        self.time_limiter = TimeLimiter(max_exec_time)

    def _set_global_scope(self, restriction_scope: t.Literal[0, 1, 2, 3]):
        """
        Override builtins in global scope based on given restriction_scope.
        Restriction levels are as follows:
        - 0: No restriction (regular exec)
        - 1: Restricted globals (removed some unsafe globals)
        - 2 (RECOMMENDED): Secure globals (only using relatively safe globals)
        - 3: No globals (very limiting but quite safe)
        """
        if restriction_scope <= 0:
            self.globals = UNRESTRICTED_GLOBALS
        elif restriction_scope == 1:
            self.globals = RESTRICTED_GLOBALS
        elif restriction_scope == 2:
            self.globals = SAFE_GLOBALS
        elif restriction_scope == 3:
            self.globals = {"__builtins__": None}
        else:
            raise TypeError("`restriction_scope` must be a literal value: 0, 1, 2 or 3.")

    def execute(self, code: str) -> t.Tuple[t.Optional[str], t.Optional[BaseException]]:
        """
        Securely execute given `code` securely with specified time-limit
        and using chosen globals (in __init__). Any stdout coming out from
        this program will get captured and returned, in case an error occurs
        it will be returned as second element of the return tuple.

        Return: (`stdout`, `raised exception`)
        """
        exception = None

        with self.stdcapture:
            try:
                self.time_limiter(exec(code, self.globals))
            except BaseException as exc:
                exception = exc

        stdout = self.stdcapture.stdout

        return stdout, exception
