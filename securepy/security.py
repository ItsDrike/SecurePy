import builtins


SAFE_TYPES = [
    "str", "int", "float",
    "bool", "tuple", "list",
    "dict", "set", "bytes",

    "range", "type", "enumerate",
    "slice", "super", "classmethod",
    "staticmethod"
]

SAFE_FUNCTIONS = [
    "print", "callable", "next",
    "zip", "divmod", "hash", "id",
    "isinstance", "issubclass",
    "len", "hex", "oct", "chr", "ord",
    "sorted", "repr", "pow", "abs",
    "round", "iter", "getattr", "hasattr",
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


SAFE_BUILTINS = {}
for name in SAFE_GLOBAL_SCOPE:
    SAFE_BUILTINS[name] = getattr(builtins, name)

SAFE_GLOBALS = {"__builtins__": SAFE_BUILTINS}

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
