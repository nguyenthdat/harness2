# conc-shared-memory-ipc

> Manage `multiprocessing.shared_memory` lifecycle explicitly with `close()` in all processes and `unlink()` by the owner.

## Why It Matters

`multiprocessing.shared_memory.SharedMemory` allows high-throughput zero-copy data sharing across processes without pickle serialization overhead. However, OS shared memory segments persist beyond process termination on POSIX systems. Every process accessing a segment must call `shm.close()` when finished, and the segment owner must call `shm.unlink()` exactly once to release operating system resources.

## Bad

```python
from multiprocessing import shared_memory

# Bad: Missing close() and unlink() leaks OS shared memory segments indefinitely
def create_shared_buffer(size: int):
    shm = shared_memory.SharedMemory(create=True, size=size)
    # Never closed or unlinked!
    return shm.name
```

## Good

```python
from multiprocessing import shared_memory
from contextlib import contextmanager

# Good: Owner guarantees both close() and unlink()
@contextmanager
def shared_memory_block(size: int):
    shm = shared_memory.SharedMemory(create=True, size=size)
    try:
        yield shm
    finally:
        shm.close()
        try:
            shm.unlink()  # Release OS segment
        except FileNotFoundError:
            pass

# Worker process closes its attached segment after releasing exported views.
def worker_process(shm_name: str):
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    view = existing_shm.buf
    try:
        view[0:4] = b"DONE"
    finally:
        view.release()
        existing_shm.close()
```

## See Also

- [conc-processpool-cpu](conc-processpool-cpu.md) - ProcessPoolExecutor computation
- [perf-memoryview-zero-copy](perf-memoryview-zero-copy.md) - Memoryview zero-copy slicing
