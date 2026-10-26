# iter-zip-strict

> Always pass `strict=True` to `zip()` (Python 3.10+) when input iterables must have identical lengths.

## Why It Matters

By default, `zip()` silently stops when the shortest iterable is exhausted. If inputs have unequal lengths (e.g. headers vs row values), trailing elements are silently dropped, causing silent data corruption.

## Bad

```python
# Bad: Silently drops trailing values if lengths mismatch
headers = ["id", "name", "email", "created_at"]
row = ["101", "Alice", "alice@example.com"]  # Missing created_at!

data = dict(zip(headers, row))  # Silently creates 3-key dict without error!
```

## Good

```python
# Good (Python 3.10+): strict=True raises ValueError on length mismatch
headers = ["id", "name", "email", "created_at"]
row = ["101", "Alice", "alice@example.com"]

# Raises ValueError: zip() argument 2 is shorter than argument 1
data = dict(zip(headers, row, strict=True))
```

## See Also

- [proj-version-compatibility](proj-version-compatibility.md) - Version compatibility check for 3.10+
- [iter-itertools-utilities](iter-itertools-utilities.md) - Itertools utilities
