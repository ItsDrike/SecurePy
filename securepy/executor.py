"""
This file will be run in subprocess and it's where the true code
execution is happening.

You need to provide system arguments to define,
the code that will be executed and the restriction level

Example usage:
    `python securepy/executor.py [restriction_level] [code]`

This also means that it will assume root of securepy/ hence
the imports specified here won't need the `import securepy.module`
but will instead only use `import module`.
"""

import sys

from security import get_globals


if __name__ == "__main__":
    try:
        restriction_level = int(sys.argv[1])
        code = sys.argv[2]
    except IndexError:
        raise RuntimeError("Warning, some arguments are missing.")
    except ValueError:
        raise RuntimeError("Warning, some arguments aren't correct.")

    exec(code, get_globals(restriction_level), {})
