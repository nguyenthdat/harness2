# perf-generators-memory

> Avoid eagerly collecting pipelines into lists between intermediate transformation stages.

## Why It Matters

Chaining multiple list comprehensions (`[z for z in [y for y in [x for x in data]]`) materializes full lists at each step, multiplying memory consumption. Generator expressions pipe data in a single pass.

## Bad

```python
# Bad: Eager materialization creates 3 full intermediate lists
def process_pipeline(raw_records: list[str]) -> list[dict]:
    cleaned = [r.strip() for r in raw_records if r.strip()]
    parsed = [parse_json(r) for r in cleaned]
    validated = [p for p in parsed if p.get("valid")]
    return validated
```

## Good

```python
from typing import Iterator

# Good: Generator expressions stream items one-by-one through stages
def process_pipeline(raw_records: Iterator[str]) -> Iterator[dict]:
    cleaned = (r.strip() for r in raw_records if r.strip())
    parsed = (parse_json(r) for r in cleaned)
    validated = (p for p in parsed if p.get("valid"))
    return validated
```

## See Also

- [iter-generators-streaming](iter-generators-streaming.md) - Streaming generator functions
- [iter-itertools-utilities](iter-itertools-utilities.md) - Itertools helpers
