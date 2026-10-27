# type-avoid-any

> Avoid `Any` in type annotations; use `object`, type variables, or `unknown` protocols for unconstrained values.

## Why It Matters

`Any` disables static type checking entirely, allowing arbitrary attribute access and method calls that can fail at runtime with `AttributeError`. Using `object` enforces explicit runtime inspection or narrowing before use.

## Bad

```python
from typing import Any

# Bad: Any disables all type safety downstream
def process_payload(payload: Any) -> Any:
    # No type checker warning if 'user_id' does not exist or has wrong type
    return payload.user_id.upper()
```

## Good

```python
from typing import TypeVar, cast

T = TypeVar("T")

# Good: Use object and narrow with isinstance or use generic TypeVar
def parse_id(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, int):
        return str(value)
    raise TypeError(f"Expected str or int, got {type(value).__name__}")
```

## See Also

- [type-narrowing-typeguard](type-narrowing-typeguard.md) - Type narrowing techniques
- [type-protocols-structural](type-protocols-structural.md) - Structural subtyping with Protocol
