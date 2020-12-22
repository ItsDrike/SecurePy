"""
This file will be run in subprocess and it's where the true code
execution is happening.

You need to provide system arguments to define,
the code that will be executed and the restriction level

Example usage:
    `python securepy/executor.py [restriction_level] [memory_limit] [code]`

This also means that it will assume root of securepy/ hence
the imports specified here won't need the `import securepy.module`
but will instead only use `import module`.
"""

import sys
import warnings

from security import get_safe_globals


def mem_limit(max_virtual_memory: int) -> None:
    if sys.platform in ["linux", "linux32", "darwin"]:
        resource = __import__("resource")
        resource.setrlimit(resource.RLIMIT_AS, (max_virtual_memory, resource.RLIM_INFINITY))
    else:
        warnings.warn("Your operating system doesn't support memory limitation, skipping memory limiting")


if __name__ == "__main__":
    try:
        restriction_level = int(sys.argv[1])
        memory_limit = int(sys.argv[2])
        code = sys.argv[3]
    except IndexError:
        raise RuntimeError("Warning, some arguments are missing.")
    except ValueError:
        raise RuntimeError("Warning, some arguments aren't correct.")

    if memory_limit != -1:
        mem_limit(memory_limit)

    exec(code, get_safe_globals(restriction_level))
