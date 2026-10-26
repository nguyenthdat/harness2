# anti-mutable-default-args

> Never use mutable objects (`list`, `dict`, `set`) as default parameter values; use `None` and initialize inside the function.

## Why It Matters

Default parameter expressions are evaluated once when the function definition is executed, NOT at call time. A mutable default argument is shared across all function calls, accumulating state unexpectedly.

## Bad

```python
# Bad: Mutable default list is shared across all invocations!
def append_item(item: str, target_list: list = []) -> list:
    target_list.append(item)
    return target_list

print(append_item("a"))  # ['a']
print(append_item("b"))  # ['a', 'b']  -- Mutated from previous call!
```

## Good

```python
from typing import Optional

# Good: Default to None and create new instance per call
def append_item(item: str, target_list: Optional[list[str]] = None) -> list[str]:
    if target_list is None:
        target_list = []
    target_list.append(item)
    return target_list

print(append_item("a"))  # ['a']
print(append_item("b"))  # ['b']
```

## See Also

- [api-immutability-defensive-copy](api-immutability-defensive-copy.md) - Immutable API design
- [anti-wildcard-imports](anti-wildcard-imports.md) - Avoiding wildcard imports
