# sec-subprocess-shell-false

> Never use `shell=True` in `subprocess` calls; pass arguments as a list with explicit executable paths.

## Why It Matters

`subprocess.run(f'cmd {user_input}', shell=True)` invokes the system shell (`/bin/sh`), allowing command injection via metacharacters (`; rm -rf /`, `|`, `$(...)`, CWE-78). Passing an argument list bypasses shell parsing.

## Bad

```python
import subprocess

# Bad: Shell injection vulnerability
def convert_image(filename: str):
    # If filename is "test.jpg; rm -rf /", shell executes the malicious command!
    subprocess.run(f"convert {filename} output.png", shell=True)
```

## Good

```python
import subprocess
import shutil

# Good: Argument list without shell=True prevents injection
def convert_image(filename: str):
    executable = shutil.which("convert")
    if not executable:
        raise RuntimeError("convert executable not found")
    subprocess.run([executable, filename, "output.png"], check=True)
```

## See Also

- [sec-pathlib-traversal](sec-pathlib-traversal.md) - Preventing path traversal attacks
- [sec-avoid-eval-exec](sec-avoid-eval-exec.md) - Avoiding eval and exec
