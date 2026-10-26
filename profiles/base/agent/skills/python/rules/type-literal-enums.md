# type-literal-enums

> Use `Literal` for finite string sets and `enum.Enum` / `StrEnum` for nominal domain enumerations.

## Why It Matters

`Literal['read', 'write']` allows type checkers to enforce exact string values without wrapping strings in enum instances. Use `enum.StrEnum` (Python 3.11+) when the enumeration has associated behavior or requires grouping.

## Bad

```python
# Bad: Using unconstrained str for finite options
def open_file(path: str, mode: str) -> None:
    # Typo like mode="reed" will only fail at runtime
    ...
```

## Good

```python
from typing import Literal

# Good: Literal restricts allowed values statically
FileMode = Literal["r", "w", "a", "rb", "wb"]

def open_file(path: str, mode: FileMode) -> None:
    ...

# For structured domain enums in Python 3.11+:
from enum import StrEnum

class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
```

## See Also

- [type-avoid-any](type-avoid-any.md) - Avoiding Any in signatures
- [type-narrowing-typeguard](type-narrowing-typeguard.md) - Type narrowing
