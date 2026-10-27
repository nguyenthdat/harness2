# conc-threadpool-executor

> Use `ThreadPoolExecutor` for blocking synchronous I/O and GIL-releasing native operations; avoid pure-Python CPU workloads on GIL-enabled builds.

## Why It Matters

Threads are useful for blocking I/O and for specific native operations documented to release the GIL. Do not assume every C/C++/Rust extension does so: orjson holds the GIL, and PyO3 routines need explicit safe release/detach. On GIL-enabled CPython, pure-Python CPU bytecode does not become multicore simply by using threads; consider bounded process workers only after accounting for startup and serialization costs. Free-threaded Python requires explicit runtime and extension compatibility checks.

## Bad

```python
# Bad: Spawning heavy OS processes for lightweight HTTP requests
from concurrent.futures import ProcessPoolExecutor
import requests

def fetch_url(url: str):
    return requests.get(url).status_code

def fetch_all(urls: list[str]):
    # ProcessPoolExecutor has high IPC serialization and process spawn overhead
    with ProcessPoolExecutor(max_workers=50) as ex:
        return list(ex.map(fetch_url, urls))
```

## Good

```python
from concurrent.futures import ThreadPoolExecutor
import requests

def fetch_url(url: str):
    return requests.get(url).status_code

def fetch_all(urls: list[str]):
    # ThreadPoolExecutor is lightweight and releases GIL during network wait
    with ThreadPoolExecutor(max_workers=50) as ex:
        return list(ex.map(fetch_url, urls))
```

Polars and many numerical libraries already use native thread pools. Prefer their own query/batch execution facilities before wrapping them in another executor; only add bounded outer concurrency when representative measurements show a benefit. Account for native pools, request concurrency, worker processes, and memory together.

## See Also

- [conc-processpool-cpu](conc-processpool-cpu.md) - ProcessPoolExecutor for CPU-bound tasks
- [async-avoid-blocking-calls](async-avoid-blocking-calls.md) - AsyncIO as alternative to threads
- [perf-polars-pipelines](perf-polars-pipelines.md) - High-performance tabular pipelines with Polars
- [perf-rust-library-selection](perf-rust-library-selection.md) - Selecting Rust-backed tools
