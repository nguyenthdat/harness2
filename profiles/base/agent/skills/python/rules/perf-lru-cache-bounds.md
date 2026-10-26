# perf-lru-cache-bounds

> Always specify a bounded `maxsize` on `@functools.lru_cache` and ensure cached arguments are immutable.

## Why It Matters

`@functools.cache` or `@lru_cache(maxsize=None)` creates an unbounded dictionary that will grow indefinitely, causing memory leaks. Furthermore, caching mutable objects produces stale or invalid results.

## Bad

```python
import functools

# Bad: Unbounded cache grows indefinitely on varying input
@functools.cache
def compute_user_stats(user_id: str, options: dict) -> dict:  # dict is unhashable anyway!
    ...
```

## Good

```python
import functools

# Good: Bounded maxsize and immutable arguments (tuples, frozensets, frozen dataclasses)
@functools.lru_cache(maxsize=1024)
def compute_user_stats(user_id: str, flags: tuple[str, ...]) -> dict:
    ...
```

## See Also

- [perf-local-var-lookup](perf-local-var-lookup.md) - Local variable lookup caching
- [type-dataclass-vs-pydantic](type-dataclass-vs-pydantic.md) - Frozen dataclasses as hashable keys
