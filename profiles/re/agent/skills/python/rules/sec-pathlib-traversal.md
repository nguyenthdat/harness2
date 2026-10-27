# sec-pathlib-traversal

> Validate path containment against trusted base directories; account for symlink races in writable trees.

## Why It Matters

Untrusted file paths containing `../` or absolute prefixes can escape an application's intended root directory (Path Traversal, CWE-22). Resolving paths (`target.resolve()`) and validating `target.is_relative_to(safe_base)` verifies lexical containment. However, in environments where untrusted users or concurrent processes can modify directory contents, symlink substitution between verification and file open creates a Time-Of-Check-To-Time-Of-Use (TOCTOU) race (CWE-367). For hostile writable trees, use descriptor-relative operations (`os.open` with `dir_fd` and `os.O_NOFOLLOW`) or dedicated sandboxed storage abstractions.

## Bad

```python
import os

# Bad: Direct string concatenation allows ../ directory traversal
def read_user_file(base_dir: str, user_path: str) -> str:
    # If user_path is "../../../../etc/passwd", path escapes base_dir!
    target = os.path.join(base_dir, user_path)
    with open(target, "r") as f:
        return f.read()
```

## Good

```python
from pathlib import Path

# Good (lexical and symlink-resolved containment check):
def read_user_file(base_dir: Path, user_path: str) -> str:
    safe_base = base_dir.resolve()
    target = (safe_base / user_path).resolve()
    
    # Path.is_relative_to (Python 3.9+)
    if not target.is_relative_to(safe_base):
        raise PermissionError("Access denied: Path traversal detected")
        
    return target.read_text(encoding="utf-8")

# For an attacker-writable tree, this portable example deliberately permits only
# one leaf name. Supporting nested paths requires component-by-component no-follow
# traversal or an OS facility such as openat2(RESOLVE_BENEATH).
import os
from pathlib import PurePath

def read_untrusted_leaf(base_dir_fd: int, leaf_name: str) -> bytes:
    if not leaf_name or PurePath(leaf_name).name != leaf_name:
        raise PermissionError("nested or special paths are not allowed")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise NotImplementedError("platform lacks no-follow open support")
    fd = os.open(leaf_name, os.O_RDONLY | nofollow, dir_fd=base_dir_fd)
    try:
        with open(fd, "rb", closefd=False) as file:
            return file.read()
    finally:
        os.close(fd)
```

## See Also

- [sec-subprocess-shell-false](sec-subprocess-shell-false.md) - Safe subprocess execution
- [err-eafp-vs-lbyl](err-eafp-vs-lbyl.md) - Safe atomic file operations
