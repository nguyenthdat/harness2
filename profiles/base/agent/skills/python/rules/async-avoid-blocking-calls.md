# async-avoid-blocking-calls

> Never run synchronous blocking I/O, heavy CPU computations, or `time.sleep` in the async event loop thread.

## Why It Matters

Python's `asyncio` runs a single-threaded cooperative event loop. Any blocking call (such as `requests.get()`, `time.sleep()`, or heavy file I/O) halts the entire event loop, freezing all concurrent coroutines and incoming network requests.

## Bad

```python
import asyncio
import time
import requests

# Bad: Blocks the entire event loop thread
async def fetch_item(url: str):
    time.sleep(1.0)  # Freezes all concurrent requests!
    res = requests.get(url)  # Blocking synchronous network I/O
    return res.json()
```

## Good

```python
import asyncio
import httpx

# Good: Use asynchronous I/O libraries (httpx, aiofiles)
async def fetch_item(client: httpx.AsyncClient, url: str):
    await asyncio.sleep(1.0)
    res = await client.get(url)
    return res.json()

# Or offload legacy synchronous blocking calls to worker thread
async def run_blocking_legacy(func, *args):
    return await asyncio.to_thread(func, *args)
```

## See Also

- [conc-threadpool-executor](conc-threadpool-executor.md) - Using ThreadPoolExecutor for blocking calls
- [async-timeout-handling](async-timeout-handling.md) - Enforcing async timeouts
