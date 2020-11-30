import typing as t

from securepy.security import RESTRICTED_GLOBALS, SAFE_GLOBALS, UNRESTRICTED_GLOBALS


class Restricted:
    """
    Prepare isolated python exec session
    """
    def __init__(self, restriction_scope: t.Literal[0, 1, 2, 3] = 2):
        """
        `restriction_level` will determine how restricted will the
        python code execution be. Restriction levels are as follows:
        - 0: No restriction (regular exec)
        - 1: Restricted globals (removed some unsafe globals)
        - 2 (RECOMMENDED): Secure globals (only using relatively safe globals)
        - 3: No globals (very limiting but quite safe)
        """
        self.restriction_scope = restriction_scope
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

    def execute(self, code: str) -> t.Any:
        return exec(code, self.globals)
