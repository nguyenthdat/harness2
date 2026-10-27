# perf-str-join-builder

> Use `''.join(parts)` or `io.StringIO` instead of repeated string concatenation (`+=`) in loops.

## Why It Matters

Because Python strings are immutable, `s += chunk` in a loop can copy the accumulating string repeatedly ($O(N^2)$ time). `str.join()` calculates total required memory once and builds the result in a single pass ($O(N)$ time).

## Bad

```python
# Bad: O(N^2) string allocations in a loop
def build_report(records: list[str]) -> str:
    result = ""
    for r in records:
        result += r + "\n"  # Reallocates and copies result every iteration!
    return result
```

## Good

```python
# Good: O(N) single-pass allocation
def build_report(records: list[str]) -> str:
    return "\n".join(records) + "\n"

# Or with io.StringIO for complex procedural formatting:
import io

def build_complex_report(records: list[dict]) -> str:
    buf = io.StringIO()
    for r in records:
        buf.write(f"ID: {r['id']}, Status: {r['status']}\n")
    return buf.getvalue()
```

## See Also

- [perf-local-var-lookup](perf-local-var-lookup.md) - Local variable caching in loops
- [iter-generators-streaming](iter-generators-streaming.md) - Streaming generator functions
