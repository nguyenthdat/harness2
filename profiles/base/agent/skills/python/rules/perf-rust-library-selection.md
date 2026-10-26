# perf-rust-library-selection

> Prefer maintained Rust-backed libraries where the workload benefits, without overriding repository contracts or assuming that Rust guarantees speed, GIL release, or memory safety at every boundary.

## Selection Policy

1. Reuse the repository's standard library and existing dependencies when they meet the requirement. For new unconstrained work, use the decision matrix in [the Python skill](../SKILL.md#modern-performance--rust-backed-tooling-decision-matrix).
2. Resolve the latest **stable, non-yanked, compatible** release from official documentation and PyPI at adoption time. Do not silently select prereleases or upgrade an established project just to get the newest version. Let `uv add` resolve against the project's Python/dependency constraints, review the result, and commit `uv.lock` for applications; use `uv sync --locked` in reproducible application CI.
3. Check `Requires-Python`, interpreter implementation, CPU architecture, OS/libc, ABI, and native transitive wheels. A pure packaging wheel such as `polars` does not prove its native runtime wheel supports the target. Missing wheels require an explicit source-build/toolchain decision, not a silent expensive build.
4. Check license, relevant security advisories, maintained release history, and dependency footprint. Do not infer quality solely from implementation language, popularity, or absence of reported CVEs.
5. Compare the actual workload before and after: output equivalence, end-to-end wall time, peak RSS, conversion/copy cost, and cold start where relevant; for servers also measure throughput, tail latency, and errors at realistic concurrency. Hold inputs, CPU quota, worker counts, and dependency versions constant. Do not publish an unmeasured speedup.
6. Preserve existing pandas, Uvicorn/Gunicorn, HTTP-client, type-checker, and formatter contracts unless migration is requested or evidence justifies it. Make conversions and cutovers explicit; do not add speculative wrappers.

## Workload Defaults

- **uv**: Python dependency/environment/tool management when unconstrained.
- **Ruff**: linting and formatting for new projects; verify rule/plugin and formatting parity before replacing established tools.
- **Polars**: new tabular processing; use lazy native expressions and minimize Python/native and pandas/Polars conversions.
- **Granian**: new compatible FastAPI ASGI serving; it is an HTTP server, not a replacement Python interpreter.
- **Pydantic v2 / pydantic-core**: validation and serialization at external boundaries; keep simple internal values as dataclasses or ordinary Python types. Validation may coerce inputs unless strictness is configured.
- **orjson**: measured raw JSON encoding/decoding needs, subject to the semantic checks below. Keep stdlib `json` when it suffices.
- **ty**: evaluate the Rust type checker when target typing features, plugins, editor support, and CI contracts fit; do not automatically replace mypy/Pyright.
- **maturin / PyO3**: only for a profiler-confirmed kernel that existing native libraries cannot address. Review Rust/Python ownership, errors, GIL handling, ABI, and wheel delivery. Merely consuming a Rust-backed wheel does not require a Rust build backend in the application.

## GIL and JSON Boundaries

Native code does not automatically release the GIL. In particular, `orjson.dumps` and `orjson.loads` hold it for the duration of the call. A PyO3 extension must deliberately release/detach where safe; verify the specific API rather than generalizing from its language. Native calls that release the GIL can still block the event-loop thread that calls them.

Before replacing stdlib JSON, verify the consumer contract:

- `orjson.dumps` returns UTF-8 **bytes**, not `str`; avoid unnecessary encode/decode copies.
- Non-finite floats serialize as `null`; decoding `NaN`/`Infinity` is rejected. Decide whether this is acceptable rather than silently changing data meaning.
- Integer ranges, UTF-8 validity, non-string mapping keys, and datetime/timezone options differ. Validate the actual boundary, including failure behavior.
- Avoid double serialization. On supported modern FastAPI versions, typed responses already use Pydantic's Rust serializer; do not add an `ORJSONResponse` override merely because it sounds faster.

```python
import orjson

payload = {"name": "item", "quantity": 3}
encoded = orjson.dumps(payload)  # bytes, suitable for a byte-oriented boundary
assert isinstance(encoded, bytes)
assert orjson.loads(encoded) == payload
```

`msgspec` is a C extension, `uvloop` uses Cython/libuv, and DuckDB is C++: all can be appropriate, but none should be described as Rust-backed. Performance and compatibility matter more than implementation-language branding.

## See Also

- [perf-polars-pipelines](perf-polars-pipelines.md)
- [perf-granian-fastapi-serving](perf-granian-fastapi-serving.md)
- [conc-threadpool-executor](conc-threadpool-executor.md)
- [pkg-modern-build-backend](pkg-modern-build-backend.md)

## Sources

- [uv project management](https://docs.astral.sh/uv/guides/projects/)
- [Ruff](https://docs.astral.sh/ruff/) and [ty](https://docs.astral.sh/ty/)
- [Pydantic performance](https://docs.pydantic.dev/latest/concepts/performance/)
- [orjson API, GIL, and serialization contracts](https://github.com/ijl/orjson)
- [PyO3](https://pyo3.rs/) and [maturin](https://www.maturin.rs/)
