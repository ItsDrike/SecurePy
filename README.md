# SecurePy

SecurePy is a project which aims to allow very secure unknown python code execution without worries.

This project is highly work in progress and it's currently in very early stages.

## Functionality

SecurePy has 2 ways of restricting your executions:
- securepy.Restrictor
- securepy.Sandbox

**`Sandbox`** only aviable for Linux devices and currently requires privillage escallation (must be run as root). It uses [`nsjail`](https://github.com/google/nsjail) to create an isolated environment for the python script to run. This is a much safer way to run your code, but it's currently unfinished and it can't be used in production.

**`Restrictor`** is a way to execute python code directly, without any additional dependencies. It's approach is to remove as many potentionally harmful builtin classes and functions as it can so that the given code will run without any problems.

## Critical note

Using this library isn't recommended as it's currently in high work in progress stage, even though it does provide some level of protection against unknown scripts, it's certainly not perfect and it shouldn't be used in production under no circumstances.


## Usage

In order to use this library, you must first download it from PyPi: `pip install securepy`

```py
import securepy

restrictor = securepy.Restrictior()
restrictor.execute("""
[your python code here]
""")
```
