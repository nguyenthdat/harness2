# anti-shadowing-builtins

> Never name variables, arguments, or attributes after Python built-in functions (`id`, `type`, `list`, `dict`, `dir`, `input`, `filter`).

## Why It Matters

Shadowing built-in names leads to baffling `TypeError: 'str' object is not callable` errors later in the function when code attempts to call the original built-in function.

## Bad

```python
# Bad: Shadows built-in 'id' and 'type'
def save_entity(id: str, type: str, list: list[str]):
    # Later in the function...
    entity_id = id(list)  # TypeError: 'str' object is not callable!
```

## Good

```python
# Good: Use descriptive names or append trailing underscore
def save_entity(entity_id: str, entity_type: str, items: list[str]):
    ...

# Or standard PEP 8 trailing underscore for reserved keywords:
def fetch_by_class(class_: str):
    ...
```

## See Also

- [type-avoid-any](type-avoid-any.md) - Explicit type naming
- [anti-wildcard-imports](anti-wildcard-imports.md) - Avoiding namespace pollution
