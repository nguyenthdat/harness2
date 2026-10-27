# async-queue-backpressure

> Always set a bounded `maxsize` on `asyncio.Queue` to enforce backpressure against fast producers.

## Why It Matters

An unbounded queue (`asyncio.Queue(maxsize=0)`) will consume infinite memory if producers generate items faster than consumers can process them, eventually crashing the process with `MemoryError`.

## Bad

```python
import asyncio

# Bad: Unbounded queue can cause Out-Of-Memory under load
work_queue: asyncio.Queue = asyncio.Queue()  # maxsize=0 (unbounded)

async def producer():
    while True:
        item = await fetch_event()
        work_queue.put_nowait(item)  # Never slows down!
```

## Good

```python
import asyncio

# Good: Bounded queue pauses producer when buffer reaches capacity
work_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=1000)

async def producer():
    while True:
        item = await fetch_event()
        # Pauses producer until space is available in queue (backpressure)
        await work_queue.put(item)
```

## See Also

- [async-taskgroups-cancellation](async-taskgroups-cancellation.md) - Structured worker tasks
- [perf-generators-memory](perf-generators-memory.md) - Streaming with generators
