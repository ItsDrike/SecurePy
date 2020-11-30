import builtins
import typing as t


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
    "print", "callable", "next",
    "zip", "divmod", "hash", "id",
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

SAFE_GLOBAL_SCOPE = SAFE_TYPES + SAFE_FUNCTIONS + SAFE_EXCEPTIONS + SAFE_DUNDERS

UNSAFE_GLOBAL_SCOPE = [
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
    "getattr": secure_getattr
}


SAFE_BUILTINS = {}
for name in SAFE_GLOBAL_SCOPE:
    SAFE_BUILTINS[name] = getattr(builtins, name)
for name, reference in OVERRIDDEN_VALUES.items():
    SAFE_BUILTINS[name] = reference

RESTRICTED_BUILTINS = {}
for builtin, reference in vars(builtins).items():
    if builtin not in UNSAFE_GLOBAL_SCOPE:
        RESTRICTED_BUILTINS[builtin] = reference

UNRESTRICTED_BUILTINS = vars(builtins)

SAFE_GLOBALS = {"__builtins__": SAFE_BUILTINS}
RESTRICTED_GLOBALS = {"__builtins__": RESTRICTED_BUILTINS}
UNRESTRICTED_GLOBALS = {"__builtins__": UNRESTRICTED_BUILTINS}
