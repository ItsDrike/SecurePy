# SecurePy

[![made-with-python](https://img.shields.io/badge/Made%20with-Python%203.8-ffe900.svg?longCache=true&style=flat-square&colorB=00a1ff&logo=python&logoColor=88889e)](https://www.python.org/)
[![LGPL](https://img.shields.io/badge/Licensed%20under-LGPL-red.svg?style=flat-square)](./LICENSE)
![Linting & Tests](https://github.com/ItsDrike/SecurePy/workflows/Linting%20&%20Tests/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/ItsDrike/SecurePy/badge.svg?branch=master)](https://coveralls.io/github/ItsDrike/SecurePy?branch=master)

SecurePy is a project which aims to allow very secure unknown python code execution without worries.

## Functionality

SecurePy has 2 ways of restricting your executions:

- **`securepy.Restrictor`** this is a way to execute python code directly, using `exec` in a protected way. It tries to remove as many potentially harmful builtin classes and functions as it can, in order to run the given code safely.
- **`securepy.Sandbox`** this is only available for Linux based devices and currently requires a privilege escalation (must be run as root). This is because it uses [`nsjail`](https://github.com/google/nsjail) to create an isolated environment for the python script to run. This option is much safer but it's currently unfinished and it can't be used in production. (It's being developed in the `nsjail` branch)

## Critical note

Even though this library is able to safely execute most unknown python source codes, you should still be very careful with granting someone access to random code execution as it is hard to cover everything.

You should also take note that this library is still relatively new and the development is still in progress, although the basic implementation is working and is relatively secure.

## Usage

In order to use this library, you must first download it from PyPi: `pip install securepy`

### Restrictor

```py
import securepy

restrictor = securepy.Restrictor(
    time_limit=3,  # seconds
    restriction_scope=2,  # secure global scope
    max_process_memory=20 * 1024 * 1024,  # 20 MB
    max_output_memory=10_000,  # 10,000 characters (bytes) maximum
    output_chunk_read_size=1_000,  # characters (bytes)
    python_path="python"  # default `python` command in PATH
)
stdout, exc = restrictor.execute("""
[your python code here]
""")
```

- `time_limit` parameter is a way to specify the maximum amount of seconds the code will be allowed to run for until interruption. (required - int/float)
- `restriction_scope` parameter is a way to specify how restricted the code should be. These are the currently available scopes:
  - **0**: No restriction (regular exec)
  - **1**: Restricted globals (removed some unsafe globals)
  - **2** (RECOMMENDED, default): Secure globals (only using relatively safe globals)
  - **3**: No globals (very limiting but quite safe)
- `max_process_memory` is the maximum amount of RAM available to given process (default: 20MB)
- `max_output_memory` is the maximum amount of memory allowed for STDOUT/STDERR outputs (default: 10,000 characters)
- `output_chunk_read_size` is the memory amount of a single chunk of stdout/stderr buffer to be read. (this buffer will keep being read until there's no more characters left or it gets bigger than specified `max_output_memory`) (default: 1,000 characters)
- `python_path` is the path to python executable used to run given code. This gives you the ability to use different non-default python versions. (default `python` as defined in PATH).

### Sandbox (NsJail)

This is only available in `nsjail` branch and it isn't production ready, only use it for testing purposes until it's finished.

You'll need to run your script as root user (or using `sudo`) because nsjail requires mounting privileges and some more file/floder management permissions, this is not a security issue as the script inside of `nsjail` is completely isolated and it can't touch the main system even with root privileges.

You'll also have to have [`nsjail`](https://github.com/google/nsjail) installed and manually create a directory `/securepy` which will be used as the working directory for nsjail.

```py
from pathlib import Path
import securepy

sandbox = securepy.Sandbox(
    nsjail_path=Path("/usr/sbin/nsjail"),  # This is path to nsjail binary (not necessary if left default)
    python_path=Path("/usr/bin/python"),  # This is path to python binary (not necessary if left default)
    allowed_memory=64_000_000,  # Maximum allowed memory: 64 MB
    max_stdout=1_000_000,  # Maximum of 1MB of stdout/stderr data
    read_chunk_size=10_000,  # Read from stdout/stderr by chunks of 10KB
    time_limit=6,  # Set maximum execution time to 6 seconds
)
```

### Maximum time limiting

SecurePy has the ability to stop given function if it takes over certain given maximum execution time.

```py
from time import sleep
import securepy

# Decorator
@securepy.TimedFunction(3)  # Limit this function to 3 seconds
def foo():
    sleep(5)  # Function will take 5 seconds (> 3s limit)
    return 2

foo()  # <-- this will raise `TimeoutError` after 3 second limit and the execution of the function will be automatically stopped.

# Wrapper
timed_func = securepy.TimedFunction(3)

def foo():
    sleep(1)
    return 2

timed_foo = timed_func(foo)

timed_foo()  # <-- this will return `2` after 1 second, since it didn't reach the given limit

# Exceptions
@securepy.TimedFunction(3)  # Limit this function to 3 seconds
def foo():
    raise TypeError("example exception")

foo()  # <-- this will raise `securepy.TimedFunctionError` and the original exception will be stored in `TimedFunctionError.inner_exception`
```

**Important note:** Running timed functions requires running them as separate processes in order to be able to terminate them after time limit was reached. This means that you might encounter some issues if you want to access/change certain variables because they'll exist in separate process. If you need to obtain some extra variables, the best approach would be to subclass `TimedFunction` and override `_capture_return` and `_value_return` functions to your needs.

### I/O Control

SecurePy has the ability to run a function in a STD capturing and simulating mode which will redirect STDOUT/STDERR and store it internally so that it can be accessed later on as a string, and simulate STDIN to be accessed inside the function.

```py
import securepy

io_cage = securepy.IOCage(
    auto_reset=True,
    memory_limit=100000,  # Store up to 100kB of STDOUT
    stdin="hi\nthere\n"
)

# Context Manager:
with io_cage:
    print("hello")
    print(input())
    print(input())

# Wrapper:
def foo(*args, **kwargs):
    print("hello")
    print(input())
    print(input())

io_cage.capture(foo, args=None, kwargs=None)

# Decorator:
@io_cage
def foo(*args, **kwargs):
    print("hello")
    print(input())
    print(input())

foo(*args, **kwargs)

# Getting STDOUT
io_cage.stdout  # <-- will contain the captured STDOUT (str): "hello\nhi\nthere"

# Getting STDERR
io_cage.stderr  # <-- will contain the captured STDERR (str): ""

# Change STDIN
io_cage.set_stdin("something\nelse\n")  # <-- will rewrite the specified stdin with a new string value
```

- `auto_reset` parameter passed into `IOCage` is a bool which guides whether stored stdout should keep being added to or if it should reset itself once function ends. Default value is `True`. Note that if you set this to `False` you'll have to reset manually with `IOCage.reset()`. (default: `True`)
- `memory_limit` parameter passed into `IOCage` is a maximum amount of memory in bytes which will be stored, if the amount of stored memory gets higher, raise `securepy.MemoryOverflow` (default: `100_000`)
- `stdin` parameter is a string containing the STDIN which should be simulated. String can be separated by `\n` in order to simulate values to multiple `input()` calls. If not specified, STDIN won't be simulated. (default: `None`)
- `enable_stdout` parameter is a way to control wether `stdout` will be captured. (default: `True`)
- `enable_stderr` parameter is a way to control wether `stderr` will be captured. (default: `True`)

### Using IOCage with Time Limiting

If you need to capture STDOUT/STDERR for a function which you also want to time-limit, you can use `IOTimedFunction` which works very similarly to `TimedFunction` but apart from max time, it also takes the `IOCage` instance.

```py
import securepy

io_cage = securepy.IOCage()

@securepy.IOTimedFunction(time_limit=2, io_cage=io_cage)
def foo(value):
    print("hello")
    return value

foo(2)  # <-- will return `value` (2)

io_cage.stdout  # <-- will hold the captured stdout string: "hello\n"
```
