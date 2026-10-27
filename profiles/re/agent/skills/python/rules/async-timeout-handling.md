# async-timeout-handling

> Use `asyncio.timeout` (Python 3.11+) for scoped code blocks; retain `asyncio.wait_for` on Python 3.9/3.10 or for single awaitable timeouts.

## Why It Matters

`asyncio.timeout(delay)` (Python 3.11+) provides a structured asynchronous context manager that bounds an entire block of coroutines without creating intermediate tasks for each await. On Python 3.9 and 3.10, or when wrapping a single standalone awaitable with a timeout, `asyncio.wait_for(awaitable, timeout)` remains fully supported and idiomatic.

## Bad

```python
import asyncio

# Bad: Manually tracking elapsed time across multiple async steps with sleep/deadline loops
async def process_with_manual_timer(client, url):
    start = asyncio.get_event_loop().time()
    res1 = await client.get(url)
    if asyncio.get_event_loop().time() - start > 5.0:
        raise TimeoutError()
    res2 = await client.post(url, json=res1.json())
```

## Good

```python
import asyncio

# Good (Python 3.11+): Structured timeout context manager over multiple operations
async def process_with_timeout(client, url):
    try:
        async with asyncio.timeout(5.0):
            res1 = await client.get(url)
            res2 = await client.post(url, json=res1.json())
            return res2.json()
    except TimeoutError:
        logger.warning("Pipeline exceeded 5.0s timeout")
        return None

# Good (Python 3.9/3.10 or single awaitable):
async def fetch_single_with_timeout(client, url):
    try:
        response = await asyncio.wait_for(client.get(url), timeout=5.0)
        return response.json()
    except asyncio.TimeoutError:
        logger.warning("Single request timed out")
        return None
```

## See Also

- [async-avoid-blocking-calls](async-avoid-blocking-calls.md) - Avoiding blocking calls
- [proj-version-compatibility](proj-version-compatibility.md) - Checking Python version features
