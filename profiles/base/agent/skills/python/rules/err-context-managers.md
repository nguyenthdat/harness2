# err-context-managers

> Use context managers (`with` / `async with` / `@contextlib.contextmanager`) to guarantee deterministic resource cleanup.

## Why It Matters

Relying on `__del__` or manual `.close()` calls leads to file descriptor exhaustion, socket leaks, and dangling locks if an exception occurs before cleanup. Context managers guarantee execution of cleanup logic even upon exceptions or cancellation.

## Bad

```python
# Bad: Manual open/close with potential leaks on error
def process_file(path: str):
    f = open(path, "r")
    data = f.read()
    # If transform(data) raises an error, f is never closed!
    transform(data)
    f.close()
```

## Good

```python
from contextlib import contextmanager

# Good: Built-in context manager guarantees closure
def process_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    transform(data)

# Good: Custom context manager with contextlib
@contextmanager
def temporary_lock(lock):
    lock.acquire()
    try:
        yield lock
    finally:
        lock.release()
```

## See Also

- [err-avoid-bare-except](err-avoid-bare-except.md) - Safe exception handling in finally
- [async-taskgroups-cancellation](async-taskgroups-cancellation.md) - Async context management in task groups
