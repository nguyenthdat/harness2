# type-narrowing-typeguard

> Use `TypeGuard` (Python 3.10+) or `TypeIs` (Python 3.13+ / typing_extensions) for custom type narrowing functions.

## Why It Matters

Standard boolean helper functions do not narrow types for static type checkers. `TypeGuard` and `TypeIs` teach the type checker how to safely narrow unions in `if`/`else` branches.

## Bad

```python
from typing import Any

# Bad: Type checker doesn't know 'val' is a list of strings after this returns True
def is_str_list(val: list[Any]) -> bool:
    return all(isinstance(x, str) for x in val)

def process(items: list[object]) -> None:
    if is_str_list(items):
        # Type error: items[0] is still object!
        items[0].lower()
```

## Good

```python
from typing import TypeGuard

# Good: TypeGuard narrows type in conditional branches
def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)

def process(items: list[object]) -> None:
    if is_str_list(items):
        # Successfully narrowed to list[str]
        print(items[0].lower())
```

## See Also

- [type-avoid-any](type-avoid-any.md) - Avoiding Any in signatures
- [proj-version-compatibility](proj-version-compatibility.md) - Version feature compatibility
