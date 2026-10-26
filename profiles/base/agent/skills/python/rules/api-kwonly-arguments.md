# api-kwonly-arguments

> Use keyword-only arguments (`*`) for functions with multiple boolean flags or optional configuration parameters.

## Why It Matters

Calling functions with positional boolean flags (`process(data, True, False, True)`) produces unreadable call sites where argument meaning is opaque and order errors pass unnoticed. Keyword-only arguments force descriptive parameter names.

## Bad

```python
# Bad: Positional booleans are unreadable at call sites
def create_user(username: str, is_admin: bool = False, notify: bool = True, dry_run: bool = False):
    ...

# What do True and False mean here?
create_user("alice", True, False, True)
```

## Good

```python
# Good: Keyword-only arguments (after *) require explicit parameter names
def create_user(
    username: str,
    *,
    is_admin: bool = False,
    notify: bool = True,
    dry_run: bool = False
) -> User:
    ...

# Clear and self-documenting call site
create_user("alice", is_admin=True, notify=False, dry_run=True)
```

## See Also

- [api-explicit-all-exports](api-explicit-all-exports.md) - Public API design
- [type-literal-enums](type-literal-enums.md) - Literal enums for explicit options
