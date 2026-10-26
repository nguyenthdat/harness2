# iter-generators-streaming

> Use generator functions (`yield`) and generator expressions to stream large datasets with $O(1)$ memory.

## Why It Matters

Materializing large sequences into lists consumes memory proportional to the dataset size ($O(N)$), causing swapping or OOM kills on multi-gigabyte files. Generators compute items lazily on demand.

## Bad

```python
# Bad: Reads entire 10GB file into memory at once
def read_log_lines(filepath: str) -> list[str]:
    with open(filepath, "r") as f:
        return [line.strip() for line in f.readlines()]  # OOM on large file!
```

## Good

```python
from typing import Iterator

# Good: Streams line by line with O(1) memory overhead
def read_log_lines(filepath: str) -> Iterator[str]:
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            yield line.strip()
```

## See Also

- [iter-itertools-utilities](iter-itertools-utilities.md) - Itertools streaming helpers
- [perf-generators-memory](perf-generators-memory.md) - Memory benefits of generators
