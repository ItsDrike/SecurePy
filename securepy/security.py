import builtins
import typing as t
from copy import deepcopy


class ProtectionBreach(RuntimeError):
    def __init__(self, message: str, *args, **kwargs):
        message += " (SecurePy execution protection)"
        super().__init__(message, *args, **kwargs)


SAFE_TYPES = [
    "str", "int", "float",
    "bool", "tuple", "list",
    "dict", "set", "bytes",

    "type", "object", "super",
    "classmethod", "staticmethod",
    "enumerate", "slice", "range"
]

SAFE_FUNCTIONS = [
    "print", "callable", "next", "zip",
    "divmod", "hash", "id",
    "isinstance", "issubclass",
    "len", "hex", "oct", "chr", "ord",
    "sorted", "repr", "pow", "abs",
    "round", "iter", "hasattr",
    "sum", "max", "min", "all", "any",
    "map", "help"
]

SAFE_EXCEPTIONS = [
    "ArithmeticError", "AssertionError", "AttributeError",
    "BaseException", "BufferError", "BytesWarning",
    "DeprecationWarning", "EOFError", "EnvironmentError",
    "Exception", "FloatingPointError", "FutureWarning",
    "GeneratorExit", "IOError", "ImportError", "ImportWarning",
    "IndentationError", "IndexError", "KeyError", "KeyboardInterrupt",
    "LookupError", "MemoryError", "NameError", "NotImplementedError",
    "OSError", "OverflowError", "PendingDeprecationWarning",
    "ReferenceError", "RuntimeError", "RuntimeWarning", "StopIteration",
    "SyntaxError", "SyntaxWarning", "SystemError", "SystemExit",
    "TabError", "TypeError", "UnboundLocalError", "UnicodeDecodeError",
    "UnicodeEncodeError", "UnicodeError", "UnicodeTranslateError",
    "UnicodeWarning", "UserWarning", "ValueError", "Warning",
    "ZeroDivisionError",
]

SAFE_DUNDERS = [
    "__build_class__", "__name__"
]

SAFE_BUILTINS = SAFE_TYPES + SAFE_FUNCTIONS + SAFE_EXCEPTIONS + SAFE_DUNDERS

UNSAFE_BUILTINS = [
    "dir",  # General purpose introspector
    "compile",  # don't allow producing new code
    # Unsafe access to namespace
    "globals",
    "locals",
    "vars",

    # Don't allow direct I/O
    "execfile",
    "input",
    "open",
    "file",
]


def secure_getattr(object: t.Any, name: str, default=None) -> t.Any:
    if name.startswith("_"):
        raise ProtectionBreach("Sorry, `name` can't start with `_`")
    return getattr(object, name, default)


OVERRIDDEN_VALUES = {
    "getattr": secure_getattr,
}


# Build global scopes
BASE_GLOBALS = {"__builtins__": {}}
UNRESTRICTED_GLOBALS = {"__builtins__": builtins}

SAFE_GLOBALS = deepcopy(BASE_GLOBALS)
for name in SAFE_BUILTINS:
    SAFE_GLOBALS["__builtins__"][name] = getattr(builtins, name)
for name, reference in OVERRIDDEN_VALUES.items():
    SAFE_GLOBALS["__builtins__"][name] = reference

RESTRICTED_GLOBALS = deepcopy(BASE_GLOBALS)
for builtin, reference in vars(builtins).items():
    if builtin not in UNSAFE_BUILTINS:
        RESTRICTED_GLOBALS["__builtins__"][builtin] = reference


def _mutable_copy(x: t.Any) -> t.Any:
    if isinstance(x, (dict, list, set, tuple)):
        return full_copy(x)
    return x


def full_copy(x: t.Any) -> t.Any:
    """
    Replicate `deepcopy` behavior, but in case `TypeError`
    is raised (usually due to pickling error for module),
    go through the mutable datatypes pairs manually.
    """
    try:
        return deepcopy(x)
    except TypeError as e:
        if isinstance(x, dict):
            new_dct = {}
            for key, value in x.items():
                value = _mutable_copy(value)
                new_dct[key] = value
            return new_dct
        elif isinstance(x, list):
            new_lst = []
            for element in x:
                element = _mutable_copy(element)
                new_lst.append(element)
                return new_lst
        elif isinstance(x, set):
            new_set = set()
            for element in x:
                element = _mutable_copy(element)
                new_set.add(element)
            return new_set
        elif isinstance(x, tuple):
            new_tuple = tuple()
            for element in x:
                element = _mutable_copy(element)
                new_tuple += (element, )
            return new_tuple
        else:
            raise e


def get_safe_globals(restriction_level: int) -> dict:
    """
    Get secure globals based on given restriction level:
    - 0: Unrestricted globals (full builtins as they are in this file)
    - 1: Restricted globals (removed some unsafe builtins)
    - 2 (RECOMMENDED): Secure globals (only using relatively safe builtins)
    - 3: No globals (very limiting but quite safe)
    """
    if restriction_level == 0:
        return full_copy(UNRESTRICTED_GLOBALS)
    elif restriction_level == 1:
        return full_copy(RESTRICTED_GLOBALS)
    elif restriction_level == 2:
        return full_copy(SAFE_GLOBALS)
    elif restriction_level == 3:
        return full_copy(BASE_GLOBALS)
    else:
        raise RuntimeError(f"Invalid `restriction_level` ({restriction_level}), valid values: 0-3.")
