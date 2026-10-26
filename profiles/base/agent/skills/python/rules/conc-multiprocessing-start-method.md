# conc-multiprocessing-start-method

> Use explicit multiprocessing contexts (`mp.get_context(...)`) to select safe start methods without mutating global state.

## Why It Matters

On POSIX systems, `fork` copies parent memory without copying threads, risking deadlocks if a parent thread held a lock during fork. While `spawn` starts a fresh interpreter, calling `multiprocessing.set_start_method(..., force=True)` mutates global process state and conflicts with test runners, application servers, or library callers. Furthermore, `forkserver` is unavailable on Windows. Using a local context (`mp.get_context("spawn")`) isolates start method configuration safely.

## Bad

```python
import multiprocessing as mp

# Bad: Forcing global start method mutates process-wide settings for all callers
def run_background_workers():
    mp.set_start_method("spawn", force=True)  # Global mutation; breaks test runners and parent process
    p = mp.Process(target=worker_fn)
    p.start()
```

## Good

```python
import multiprocessing as mp

def worker_fn(q):
    q.put("done")

# Good: Explicit local context selection without global side effects
def run_background_workers():
    # 'spawn' is portable across Windows, macOS, and Linux
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=worker_fn, args=(q,))
    p.start()
    result = q.get()
    p.join()
    return result

if __name__ == "__main__":
    # In main scripts, guard entry points to support spawn child imports
    run_background_workers()
```

## See Also

- [conc-processpool-cpu](conc-processpool-cpu.md) - ProcessPoolExecutor computation
- [conc-shared-memory-ipc](conc-shared-memory-ipc.md) - Shared memory between processes
