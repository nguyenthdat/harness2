# async-lock-granularity

> Keep `asyncio.Lock` critical sections small and never hold locks across long-running network operations.

## Why It Matters

Holding an `asyncio.Lock` across network requests or long sleeps serializes all concurrent coroutines, eliminating concurrency and creating high latency or deadlocks.

## Bad

```python
import asyncio

# Bad: Holding lock across external HTTP request
lock = asyncio.Lock()

async def update_user(user_id: str):
    async with lock:
        user = await db.get(user_id)
        # Slow network call blocks ALL other users from updating!
        remote_data = await http_client.get(f"/api/users/{user_id}")
        await db.save(user_id, remote_data)
```

## Good

```python
import asyncio

# Good: Perform network calls outside the critical section
lock = asyncio.Lock()

async def update_user(user_id: str):
    remote_data = await http_client.get(f"/api/users/{user_id}")
    async with lock:
        # Lock held only for fast in-memory or atomic state modification
        await db.save(user_id, remote_data)
```

## See Also

- [async-avoid-blocking-calls](async-avoid-blocking-calls.md) - Non-blocking async code
- [conc-thread-synchronization](conc-thread-synchronization.md) - Thread locking primitives
