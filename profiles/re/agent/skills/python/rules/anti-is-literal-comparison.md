# anti-is-literal-comparison

> Use `==` for value equality and reserve `is` for object identity checks (`is None` and sentinel objects).

## Why It Matters

The `is` operator tests object identity (whether two references point to the exact same object), whereas `==` tests value equality. While CPython interns small integers and short string literals as an internal implementation detail, larger numbers and runtime strings will fail `is` comparisons unpredictably. Use `==` for data comparisons, and reserve `is` for singletons (`is None`, `is Ellipsis`) or private sentinel objects.

## Bad

```python
# Bad: Comparing values or string literals with 'is'
x = 1000
if x is 1000:  # Fails across Python versions/compilers; SyntaxWarning!
    ...

user_role = get_role()
if user_role is "admin":  # Fails if string was dynamically allocated!
    ...

if is_valid is True:  # Verbose; use 'if is_valid:' directly
    ...
```

## Good

```python
# Good: == for value equality
x = 1000
if x == 1000:
    ...

user_role = get_role()
if user_role == "admin":
    ...

# Good: Direct boolean truth testing
if is_valid:
    ...

# Good: 'is' used exclusively for singletons and sentinels
if item is None:
    ...

_SENTINEL = object()
def fetch(default=_SENTINEL):
    ...
```

## See Also

- [sec-secrets-constant-time](sec-secrets-constant-time.md) - Constant time comparison for secrets
- [type-literal-enums](type-literal-enums.md) - Literal enums
