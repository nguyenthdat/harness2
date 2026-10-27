# perf-granian-fastapi-serving

> Prefer Granian as the ASGI HTTP server for new production FastAPI deployments; configure worker processes and Rust runtime threads according to core counts without oversubscription or blocking the async event loop.

## Why It Matters

Granian is an HTTP server for Python applications written in Rust, built on Tokio and Hyper. Prefer it for new compatible FastAPI deployments; measure throughput, tail latency, error rate, and memory on the actual workload rather than assuming it outperforms every alternative.

Granian is **not** a replacement for the Python interpreter or Python's `asyncio` event loop: it runs standard CPython bytecode for the application layer while handling network sockets, HTTP/1.1 and HTTP/2 protocol parsing, and TLS termination in Rust.

To deploy Granian reliably in production:
1. **CLI Invocation**: Specify the ASGI interface explicitly:
   ```bash
   uv run granian --interface asgi --host 0.0.0.0 --port 8000 app.main:app
   ```
2. **Factory Functions**: Use `--factory` only if referencing an application factory function, not when referencing an application instance:
   ```bash
   uv run granian --interface asgi --factory app.main:create_app
   ```
3. **Production Configuration**: Never run with `--reload` in production. Reloading incurs filesystem monitoring overhead and must be restricted to local development.
4. **Worker & Thread Architecture**:
   - `--workers N`: Worker processes on standard GIL-enabled CPython. Start with one per container; for a standalone host, size against CPU quota, memory, and downstream connection budgets.
   - `--runtime-threads T`: Rust runtime threads per worker handling network I/O. Keep the default unless measurements justify changing it; do not use the obsolete `--threads` spelling.
   - `--blocking-threads B`: Granian's Python interop pool, relevant to synchronous protocols such as WSGI; it does **not** size FastAPI/Starlette's AnyIO thread pool for synchronous `def` endpoints. Leave it alone for ASGI.
   - Budget worker count together with Polars/BLAS pools and per-worker database/client pools. Multiplying every pool by core count causes oversubscription and memory pressure.
   - `--backpressure`: CLI help describes maximum concurrent requests per worker. However, the [Granian 2.8.3 README's backpressure warning](https://github.com/emmett-framework/granian/tree/v2.8.3#backpressure) explicitly says enforcement occurs at connection acceptance and does not count individual keep-alive requests. Verify the deployed version; do not assume a strict in-flight-request cap for keep-alive/HTTP2. Bound application work and downstream pools separately.
5. **No Blocking on Event Loop**: Use async clients for I/O; offload unavoidable blocking I/O with bounded concurrency. A native call may release the GIL while still blocking the calling event-loop thread. Pure-Python CPU work needs a bounded process/job boundary, not an assumption that `asyncio.to_thread` makes it parallel. Cancelling an await does not forcibly stop work already running in a thread.
6. **Application Lifespan**: Implement standard ASGI lifespan handlers (`@asynccontextmanager lifespan(app)`) to ensure database connection pools and background clients initialize and shut down cleanly.
7. **FastAPI Response Serialization**:
   - Modern FastAPI (leveraging Pydantic v2 / `pydantic-core`) automatically serializes type-annotated responses (`response_model` or return type hints) directly to JSON bytes inside Rust.
   - Current FastAPI documentation deprecates `ORJSONResponse` in favor of typed responses. Do not blanket-configure `default_response_class=ORJSONResponse`; verify the installed FastAPI/Pydantic versions and response path before changing an existing serialization contract.
8. **Existing Repositories**: Retain established, working Uvicorn/Gunicorn deployment setups unless server throughput or latency has been measured as a bottleneck.
9. **Deployment Boundaries**: Verify required WebSocket/streaming/ASGI extensions, proxy trust, and graceful shutdown before switching servers. Do not trust arbitrary forwarded headers. Free-threaded Python has different worker semantics and experimental Granian support; do not enable it as an automatic optimization.

## Bad

```python
# Bad: Using deprecated ORJSONResponse, running reload in production, and blocking the event loop
import time
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse  # Deprecated in modern FastAPI with Pydantic v2

# Bad: Overriding default response class with deprecated ORJSONResponse
app = FastAPI(default_response_class=ORJSONResponse)

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    # Bad: Blocking the async event loop thread
    time.sleep(0.5)  # Freezes all concurrent requests on this worker's event loop!
    return {"item_id": item_id, "status": "active"}

# Bad production command:
# granian --reload --workers 16 --runtime-threads 16 app:app
```

## Good

```python
# Good: Clean ASGI lifespan, non-blocking handlers, and native Pydantic v2 serialization
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
import httpx

class ItemResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    item_id: str
    status: str

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Initialize shared async resources cleanly
    async with httpx.AsyncClient(timeout=10.0) as client:
        app.state.http_client = client
        yield
    # Resources cleanly closed on shutdown signal

app = FastAPI(lifespan=lifespan)

# Standard typed response model: serializes directly to JSON bytes via Pydantic v2 in Rust
@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str) -> ItemResponse:
    return ItemResponse(item_id=item_id, status="active")
```

```bash
# Conservative container starting point; tune only against a measured workload:
uv run granian --interface asgi --host 0.0.0.0 --port 8000 --workers 1 app.main:app
```

## Concurrency Model Reference

| Component | Flag | Controlled Layer | Recommendation |
|-----------|------|------------------|----------------|
| Worker Processes | `--workers` | CPython processes (GIL build) | Start with one/container; measure before scaling. |
| Runtime Threads | `--runtime-threads` | Rust (Tokio) | Keep server defaults unless profiling justifies tuning. |
| Blocking Threads | `--blocking-threads` | Granian Python interop | Not FastAPI's sync-endpoint AnyIO pool; do not tune for ASGI. |
| Interface | `--interface` | Protocol | Set explicitly to `asgi` for FastAPI applications. |

## See Also

- [perf-rust-library-selection](perf-rust-library-selection.md) - Rust-backed library selection
- [async-avoid-blocking-calls](async-avoid-blocking-calls.md) - Preventing event-loop blocking
- [type-pydantic-boundaries](type-pydantic-boundaries.md) - Boundary validation with Pydantic

## Sources

- [Granian CLI, workers, backpressure, and deployment caveats](https://github.com/emmett-framework/granian)
- [FastAPI typed response serialization](https://fastapi.tiangolo.com/advanced/response-directly/)
- [Starlette thread pool](https://www.starlette.io/threadpool/)
