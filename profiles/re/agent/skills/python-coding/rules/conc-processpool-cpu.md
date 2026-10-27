# conc-processpool-cpu

> Profile CPU-bound work, then choose processes, threads, native code, or free-threaded CPython from runtime and transfer constraints.

## Why It Matters

Traditional GIL-enabled CPython cannot run CPU-bound Python bytecode concurrently in ordinary threads, but that is not universal: many native extensions release the GIL, and free-threaded CPython builds change the tradeoff. Processes add serialization, startup, and memory costs. Choose from measurements and the deployed interpreter rather than assuming `ProcessPoolExecutor` is always faster.

## Bad

```python
from concurrent.futures import ThreadPoolExecutor

# Bad: assumes every interpreter and workload is GIL-bound without measuring.
def compute_heavy_hash(data: bytes) -> str:
    ...

def process_batch(items: list[bytes]):
    with ThreadPoolExecutor() as executor:
        return list(executor.map(compute_heavy_hash, items))
```

## Good

```python
from concurrent.futures import ProcessPoolExecutor

def compute_heavy_hash(data: bytes) -> str:
    ...

def process_batch(items: list[bytes]):
    # Chosen only after profiling a GIL-enabled deployment and accounting for
    # process startup plus serialization of each item.
    with ProcessPoolExecutor() as executor:
        return list(executor.map(compute_heavy_hash, items))
```

## See Also

- [conc-threadpool-executor](conc-threadpool-executor.md) - ThreadPoolExecutor for I/O
- [conc-multiprocessing-start-method](conc-multiprocessing-start-method.md) - Safe multiprocessing start methods
