# perf-local-var-lookup

> Cache repeated lookups only inside a profiler-confirmed hot loop.

## Why It Matters

Lookup costs vary by Python implementation and release; adaptive specialization can optimize globals and attributes. Local aliases can also become stale after monkey-patching and reduce clarity. Apply this micro-optimization only after a representative profile attributes material time to the lookup.

## Bad

```python
import math

# Bad: adds aliases before a representative profile shows lookup overhead matters.
def calculate_distances(points: list[tuple[float, float]]) -> list[float]:
    sqrt = math.sqrt
    output: list[float] = []
    append = output.append
    for x, y in points:
        append(sqrt(x * x + y * y))
    return output
```

## Good

```python
import math

# Keep the clear implementation until profiling identifies a material bottleneck.
def calculate_distances(points: list[tuple[float, float]]) -> list[float]:
    return [math.hypot(x, y) for x, y in points]

# If a profile on the deployed interpreter attributes material time to a stable
# repeated lookup, compare a local alias with the baseline in a benchmark.
def calculate_distances_profiled(points: list[tuple[float, float]]) -> list[float]:
    hypot = math.hypot
    return [hypot(x, y) for x, y in points]
```

## See Also

- [perf-str-join-builder](perf-str-join-builder.md) - Fast string accumulation
- [perf-lru-cache-bounds](perf-lru-cache-bounds.md) - Memoization with lru_cache
