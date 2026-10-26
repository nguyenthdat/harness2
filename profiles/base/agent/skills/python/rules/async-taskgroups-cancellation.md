# async-taskgroups-cancellation

> Use `asyncio.TaskGroup` (Python 3.11+) when fail-fast structured concurrency and sibling cancellation are required.

## Why It Matters

Unparented background tasks spawned via `asyncio.create_task()` can outlive their intended operation unless another owner retains and supervises them. `asyncio.gather()` awaits multiple awaitables, but by default a child exception does not cancel the other awaitables; `gather(return_exceptions=True)` intentionally collects every result. `asyncio.TaskGroup` provides a different fail-fast contract: a non-cancellation child failure cancels unfinished siblings, waits for every child to settle, and normally raises grouped failures on exit.

## Bad

```python
import asyncio

# Bad: Fire-and-forget background tasks without clear parent lifecycle
async def run_pipeline():
    task1 = asyncio.create_task(fetch_user())
    task2 = asyncio.create_task(sync_database())
    # If fetch_user() fails or an exception happens here, task2 keeps running in background
    res1 = await task1
    res2 = await task2
    return res1, res2
```

## Good

```python
import asyncio

# Good (Python 3.11+): TaskGroup provides fail-fast structured concurrency
async def run_pipeline():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch_user())
        t2 = tg.create_task(sync_database())
    # On normal exit both results are available; if a child fails,
    # unfinished siblings are cancelled and all children are awaited
    # before the grouped failure propagates.
    return t1.result(), t2.result()

# Good (Python 3.9/3.10 or when collect-all error tolerance is desired):
async def run_pipeline_fallback():
    # gather(return_exceptions=True) explicitly collects successes and exceptions
    results = await asyncio.gather(fetch_user(), sync_database(), return_exceptions=True)
    return results
```

## See Also

- [err-exception-groups](err-exception-groups.md) - Handling ExceptionGroup with except*
- [async-avoid-blocking-calls](async-avoid-blocking-calls.md) - Avoiding blocking calls in async loops
