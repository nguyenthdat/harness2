# conc-thread-synchronization

> Protect shared mutable state across threads with `threading.Lock` or use thread-safe `queue.Queue`.

## Why It Matters

Even with the GIL, operations on mutable objects spanning multiple bytecode instructions (like `counter += 1`) are not atomic and will suffer race conditions and corrupted data when accessed concurrently by multiple threads.

## Bad

```python
import threading

# Bad: Non-atomic in-place addition causes race conditions
counter = 0

def increment():
    global counter
    for _ in range(100_000):
        counter += 1  # 3 bytecode operations (LOAD, ADD, STORE) - NOT atomic!
```

## Good

```python
import threading

# Good: Explicit lock ensures atomic updates
counter = 0
counter_lock = threading.Lock()

def increment():
    global counter
    for _ in range(100_000):
        with counter_lock:
            counter += 1
```

## See Also

- [conc-threadpool-executor](conc-threadpool-executor.md) - ThreadPoolExecutor concurrency
- [async-lock-granularity](async-lock-granularity.md) - Async lock granularity
