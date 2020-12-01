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

restrictor = securepy.Restrictor(restriction_scope=2)
stdout, exc = restrictor.execute("""
[your python code here]
""")
```

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
