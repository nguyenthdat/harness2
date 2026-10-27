# iter-itertools-utilities

> Use `itertools` utilities (`chain`, `islice`, `batched`, `groupby`) rather than building temporary intermediate lists.

## Why It Matters

`itertools` functions are implemented in optimized C inside CPython, producing zero intermediate list allocations and running significantly faster than manual nested loops or slicing.

## Bad

```python
# Bad: Creating temporary intermediate lists for slicing or chunking
def get_first_ten(items):
    return list(items)[:10]  # Materializes entire iterable before slicing!

def chunk_data(data, chunk_size):
    # Manual slicing requires indexable sequences and creates sublists
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
```

## Good

```python
import itertools

# Good: islice works on any stream without materializing
def get_first_ten(items):
    return list(itertools.islice(items, 10))

# Good (Python 3.12+): itertools.batched for efficient streaming chunks
def chunk_data(data, chunk_size):
    return itertools.batched(data, chunk_size)
```

## See Also

- [iter-generators-streaming](iter-generators-streaming.md) - Streaming with generator functions
- [iter-zip-strict](iter-zip-strict.md) - Using zip with strict=True
