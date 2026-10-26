# err-eafp-vs-lbyl

> Prefer EAFP (Easier to Ask for Forgiveness than Permission) over LBYL to avoid race conditions (TOCTOU).

## Why It Matters

Checking conditions before operating (LBYL: Look Before You Leap, like `os.path.exists()` before `open()`) creates Time-Of-Check-To-Time-Of-Use (TOCTOU) race conditions in concurrent or multi-process environments. EAFP attempts the operation and handles specific failure exceptions directly.

## Bad

```python
import os

# Bad (LBYL): Race condition between check and use
def read_config(path: str) -> str:
    if os.path.exists(path):
        # File can be deleted or permissions changed right here!
        with open(path, "r") as f:
            return f.read()
    return "{}"
```

## Good

```python
# Good (EAFP): Atomic attempt and precise error handling
def read_config(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "{}"
    except PermissionError as exc:
        raise ConfigAccessError(f"Cannot read {path}") from exc
```

## See Also

- [sec-pathlib-traversal](sec-pathlib-traversal.md) - Safe filesystem path handling
- [err-reraise-from](err-reraise-from.md) - Preserving exception chains
