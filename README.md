# SecurePy

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

restrictor = securepy.Restrictor(max_exec_time=3, restriction_scope=2)
stdout, exc = restrictor.execute("""
[your python code here]
""")
```

`max_exec_time` parameter is a way to specify the maximum amount of seconds the code will be allowed to run for until interruption.
`restriction_scope` parameter is a way to specify how restricted the code should be. These are the currently available scopes:

- **0**: No restriction (regular exec)
- **1**: Restricted globals (removed some unsafe globals)
- **2** (RECOMMENDED): Secure globals (only using relatively safe globals)
- **3**: No globals (very limiting but quite safe)

`stdout` and `exc` variables will hold the outputs from your code. `exc` will hold the exception if there is some (otherwise it will be `None`). `stdout` will hold the simple standard output (print output).

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

### STDOUT/STDERR Capturing

SecurePy has the ability to run a function in a STD capturing mode which will redirect STDOUT/STDERR and store it internally so that it can be accessed later on as a string.

```py
import securepy

captured_std = securepy.StdCapture(auto_reset=True)

# Context Manager:
with captured_std:
    print("hello")

# Wrapper:
def foo(*args, **kwargs):
    print("hello")

captured_std.capture(foo, args=None, kwargs=None)

# Decorator:
@captured_std
def foo(*args, **kwargs):
    print("hello")

foo(*args, **kwargs)

# Getting STDOUT
captured_std.stdout  # <-- will contain the captured STDOUT (str): "hello\n"
# Getting STDERR
captured_std.stderr  # <-- will contain the captured STDERR (str): ""
```

`auto_reset` parameter passed into `StdCapture` is a bool which guides whether stored stdout should keep being added to or if it should reset itself once function ends. Default value is `True`. Note that if you set this to `False` you'll have to reset manually with `StdCapture.reset()`.

### Capturing STDOUT/STDERR with Time Limiting

If you need to capture STDOUT/STDERR for a function which you also want to time-limit, you can use `CapturingTimedFunction` which works very similarly to `TimedFunction` but apart from max time, it also takes the `StdCapture` class

```py
import securepy

std_capture = securepy.StdCapture()

@securepy.TimedFunction(time_limit=2, std_capture=std_capture)
def foo(value):
    print("hello")
    return value

foo(2)  # <-- will return `value` (2)

std_capture.stdout  # <-- will hold the captured stdout string: "hello\n"
```
