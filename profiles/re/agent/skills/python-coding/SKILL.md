---
name: python-coding
description: >
  Comprehensive Python coding guidelines with 76 rules across 13 categories.
  Use when writing, reviewing, or refactoring Python code. Covers project detection,
  static typing, boundary models, error handling, async/task groups, concurrency,
  memory optimization, Rust-backed performance (Polars, Granian, orjson), iterators,
  packaging with pyproject/uv, pytest, observability, security, API design, and common anti-patterns.
compatibility: Python 3.9+ (with 3.10, 3.11, 3.12, 3.13, and 3.14 features explicitly gated; modern performance stack requires >=3.10)
license: MIT
metadata:
  author: coder-specialty
  version: "1.2.0"
  sources:
    - Python Language Reference & Standard Library Documentation
    - PEP 8 (Style Guide), PEP 517/518/621 (Packaging), PEP 484/561/695 (Typing)
    - FastHTML, FastAPI, Pydantic, HTTPX, Trio, and CPython internals
    - PyPA (Python Packaging Authority) & Astral uv specifications
    - Polars, Granian, and PyO3/Maturin documentation
---

# Python coding

Comprehensive guide for writing robust, type-safe, idiomatic, and highly performant Python code. Contains 76 rules across 13 categories, prioritized by impact to guide code generation, refactoring, and review across Python 3.9 through Python 3.14+.

## When to Apply

Reference these guidelines when:
- Authoring new Python modules, classes, and async functions
- Defining domain models, schemas, and type annotations
- Implementing structured concurrency, task groups, and async I/O
- Structuring exception hierarchies and context managers
- Writing comprehensive, isolated pytest test suites
- Optimizing memory usage (`__slots__`, zero-copy buffers, generator streaming, Polars lazy pipelines)
- Serving high-throughput ASGI applications with Granian and native Rust extensions
- Configuring `pyproject.toml`, build backends, and `uv` lockfiles
- Hardening code against path traversal, command injection, and insecure deserialization

## Rule Categories by Priority

| Priority | Category | Impact | Prefix | Rules |
|----------|----------|--------|--------|-------|
| 1 | Project & Version Detection | CRITICAL | `proj-` | 5 |
| 2 | Type System & Boundary Models | CRITICAL | `type-` | 9 |
| 3 | Error Handling & Resource Management | CRITICAL | `err-` | 6 |
| 4 | Async/Await & Structured Concurrency | HIGH | `async-` | 6 |
| 5 | Concurrency & Multiprocessing | HIGH | `conc-` | 5 |
| 6 | Security & Safe Data Handling | HIGH | `sec-` | 6 |
| 7 | Memory & Performance Optimization | HIGH | `perf-` | 9 |
| 8 | Iterators, Generators & Collections | MEDIUM | `iter-` | 5 |
| 9 | Packaging & Dependency Management | MEDIUM | `pkg-` | 6 |
| 10 | Testing with Pytest | MEDIUM | `test-` | 6 |
| 11 | Logging & Observability | MEDIUM | `obs-` | 4 |
| 12 | API & Module Design | MEDIUM | `api-` | 4 |
| 13 | Common Anti-Patterns | REFERENCE | `anti-` | 5 |

---

## Quick Reference

### 1. Project & Version Detection (CRITICAL)

- [`proj-pyproject-single-source`](rules/proj-pyproject-single-source.md) - Use `pyproject.toml` (PEP 517/518/621) as the single source of truth for build metadata and tool configurations.
- [`proj-src-layout`](rules/proj-src-layout.md) - Use the `src/` package layout (`src/<package>/`) to isolate imported code from local working directory files.
- [`proj-type-checker-config`](rules/proj-type-checker-config.md) - Configure strict type checking (mypy/pyright) in `pyproject.toml` aligned with target Python version.
- [`proj-version-compatibility`](rules/proj-version-compatibility.md) - Check and respect declared `requires-python` / `python_version` before adopting newer language features.
- [`proj-virtualenv-isolation`](rules/proj-virtualenv-isolation.md) - Always use an isolated virtual environment (`.venv`) or `uv` workspace; never install into system Python.

### 2. Type System & Boundary Models (CRITICAL)

- [`type-annotated-metadata`](rules/type-annotated-metadata.md) - Use `typing.Annotated` to attach validation, serialization, or dependency injection metadata to types.
- [`type-avoid-any`](rules/type-avoid-any.md) - Avoid `Any` in type annotations; use `object`, type variables, or `unknown` protocols for unconstrained values.
- [`type-dataclass-vs-pydantic`](rules/type-dataclass-vs-pydantic.md) - Prefer standard dataclasses for internal domain logic; reserve Pydantic for validation boundaries when already adopted.
- [`type-literal-enums`](rules/type-literal-enums.md) - Use `Literal` for finite string sets and `enum.Enum` / `StrEnum` for nominal domain enumerations.
- [`type-narrowing-typeguard`](rules/type-narrowing-typeguard.md) - Use `TypeGuard` (Python 3.10+) or `TypeIs` (Python 3.13+ / typing_extensions) for custom type narrowing functions.
- [`type-protocols-structural`](rules/type-protocols-structural.md) - Use `typing.Protocol` for structural subtyping (duck typing) instead of tight abstract base class inheritance.
- [`type-pydantic-boundaries`](rules/type-pydantic-boundaries.md) - Validate external data at system boundaries using Pydantic when installed/standard in the repo, or strict standard library validation models.
- [`type-typeddict-raw-data`](rules/type-typeddict-raw-data.md) - Use `TypedDict` with `NotRequired` (or `total=False`) for typed dictionary shapes without runtime validation overhead.
- [`type-variance-typevar`](rules/type-variance-typevar.md) - Declare variance on generic container and protocol parameters, while keeping function type variables unconstrained.

### 3. Error Handling & Resource Management (CRITICAL)

- [`err-avoid-bare-except`](rules/err-avoid-bare-except.md) - Never use bare `except:` or catch `BaseException`; catch specific exceptions or `Exception`.
- [`err-context-managers`](rules/err-context-managers.md) - Use context managers (`with` / `async with` / `@contextlib.contextmanager`) to guarantee deterministic resource cleanup.
- [`err-custom-hierarchy`](rules/err-custom-hierarchy.md) - Derive domain-specific exceptions from a single package-level base exception derived from `Exception`.
- [`err-eafp-vs-lbyl`](rules/err-eafp-vs-lbyl.md) - Prefer EAFP (Easier to Ask for Forgiveness than Permission) over LBYL to avoid race conditions (TOCTOU).
- [`err-exception-groups`](rules/err-exception-groups.md) - Use `except*` (Python 3.11+) or `exceptiongroup` backport to handle concurrent failures in `ExceptionGroup`.
- [`err-reraise-from`](rules/err-reraise-from.md) - Always use `raise NewException(...) from err` to preserve exception cause and traceback chains.

### 4. Async/Await & Structured Concurrency (HIGH)

- [`async-avoid-blocking-calls`](rules/async-avoid-blocking-calls.md) - Never run synchronous blocking I/O, heavy CPU computations, or `time.sleep` in the async event loop thread.
- [`async-lock-granularity`](rules/async-lock-granularity.md) - Keep `asyncio.Lock` critical sections small and never hold locks across long-running network operations.
- [`async-queue-backpressure`](rules/async-queue-backpressure.md) - Always set a bounded `maxsize` on `asyncio.Queue` to enforce backpressure against fast producers.
- [`async-shield-critical-cleanup`](rules/async-shield-critical-cleanup.md) - Give essential cleanup explicit task ownership; use `shield` only when caller cancellation must not cancel that owned task.
- [`async-taskgroups-cancellation`](rules/async-taskgroups-cancellation.md) - Use `asyncio.TaskGroup` on Python 3.11+ when non-cancellation child failures should cancel unfinished siblings.
- [`async-timeout-handling`](rules/async-timeout-handling.md) - Use `asyncio.timeout` (Python 3.11+) for scoped code blocks; retain `asyncio.wait_for` on Python 3.9/3.10 or for single awaitable timeouts.

### 5. Concurrency & Multiprocessing (HIGH)

- [`conc-multiprocessing-start-method`](rules/conc-multiprocessing-start-method.md) - Use explicit multiprocessing contexts (`mp.get_context(...)`) to select safe start methods without mutating global state.
- [`conc-processpool-cpu`](rules/conc-processpool-cpu.md) - Profile CPU-bound work, then choose processes, threads, native code, or free-threaded CPython from runtime and transfer constraints.
- [`conc-shared-memory-ipc`](rules/conc-shared-memory-ipc.md) - Manage `multiprocessing.shared_memory` lifecycle explicitly with `close()` in all processes and `unlink()` by the owner.
- [`conc-thread-synchronization`](rules/conc-thread-synchronization.md) - Protect shared mutable state across threads with `threading.Lock` or use thread-safe `queue.Queue`.
- [`conc-threadpool-executor`](rules/conc-threadpool-executor.md) - Use `ThreadPoolExecutor` for blocking synchronous I/O and GIL-releasing native operations; avoid pure-Python CPU workloads on GIL-enabled builds.

### 6. Security & Safe Data Handling (HIGH)

- [`sec-avoid-eval-exec`](rules/sec-avoid-eval-exec.md) - Never execute untrusted code with `eval()` or `exec()`; use restricted AST evaluators or dedicated expression parsers.
- [`sec-avoid-pickle-untrusted`](rules/sec-avoid-pickle-untrusted.md) - Never deserialize untrusted data with `pickle`, `marshal`, or `shelve`; use standard JSON or schema-validated data formats.
- [`sec-pathlib-traversal`](rules/sec-pathlib-traversal.md) - Validate path containment against trusted base directories; account for symlink races in writable trees.
- [`sec-secrets-constant-time`](rules/sec-secrets-constant-time.md) - Use `secrets.compare_digest` for comparing hashes, tokens, and HMACs to prevent timing attacks.
- [`sec-subprocess-shell-false`](rules/sec-subprocess-shell-false.md) - Never use `shell=True` in `subprocess` calls; pass arguments as a list with explicit executable paths.
- [`sec-yaml-safe-load`](rules/sec-yaml-safe-load.md) - Always use `yaml.safe_load()` instead of `yaml.load()` when parsing YAML content with PyYAML.

### 7. Memory & Performance Optimization (HIGH)

- [`perf-generators-memory`](rules/perf-generators-memory.md) - Avoid eagerly collecting pipelines into lists between intermediate transformation stages.
- [`perf-granian-fastapi-serving`](rules/perf-granian-fastapi-serving.md) - Serve production FastAPI applications with Granian ASGI, tuning workers and Tokio runtime threads without event-loop blocking.
- [`perf-local-var-lookup`](rules/perf-local-var-lookup.md) - Cache repeated lookups only inside a profiler-confirmed hot loop.
- [`perf-lru-cache-bounds`](rules/perf-lru-cache-bounds.md) - Always specify a bounded `maxsize` on `@functools.lru_cache` and ensure cached arguments are immutable.
- [`perf-memoryview-zero-copy`](rules/perf-memoryview-zero-copy.md) - Use `memoryview` and `bytearray` for zero-copy slicing and buffer manipulation of large binary data.
- [`perf-polars-pipelines`](rules/perf-polars-pipelines.md) - Prefer Polars for new tabular workloads using lazy execution, columnar expression pushdowns, and native streaming.
- [`perf-rust-library-selection`](rules/perf-rust-library-selection.md) - Adopt maintained Rust-backed libraries for high-throughput workloads, resolving current stable versions and platform wheels at adoption.
- [`perf-slots-memory`](rules/perf-slots-memory.md) - Use `__slots__` or `@dataclass(slots=True)` for classes instantiated in high volumes to eliminate `__dict__` overhead.
- [`perf-str-join-builder`](rules/perf-str-join-builder.md) - Use `''.join(parts)` or `io.StringIO` instead of repeated string concatenation (`+=`) in loops.

### 8. Iterators, Generators & Collections (MEDIUM)

- [`iter-collections-specialized`](rules/iter-collections-specialized.md) - Use specialized collections (`deque`, `defaultdict`, `Counter`) instead of inefficient list/dict workarounds.
- [`iter-dict-views-operations`](rules/iter-dict-views-operations.md) - Use dictionary view set operations (`dict.keys() & set`) instead of creating intermediate sets.
- [`iter-generators-streaming`](rules/iter-generators-streaming.md) - Use generator functions (`yield`) and generator expressions to stream large datasets with $O(1)$ memory.
- [`iter-itertools-utilities`](rules/iter-itertools-utilities.md) - Use `itertools` utilities (`chain`, `islice`, `batched`, `groupby`) rather than building temporary intermediate lists.
- [`iter-zip-strict`](rules/iter-zip-strict.md) - Always pass `strict=True` to `zip()` (Python 3.10+) when input iterables must have identical lengths.

### 9. Packaging & Dependency Management (MEDIUM)

- [`pkg-avoid-setup-py`](rules/pkg-avoid-setup-py.md) - Prefer PEP 517/621 builds and never invoke deprecated `setup.py` commands; migrate legacy metadata only when in scope.
- [`pkg-dependency-pinning`](rules/pkg-dependency-pinning.md) - Use semantic lower/upper bounds for library dependencies and lockfiles for deployable applications.
- [`pkg-modern-build-backend`](rules/pkg-modern-build-backend.md) - Use standard declarative build backends (`hatchling`, `flit-core`) for pure Python, allowing `maturin` only for compiled Rust extensions.
- [`pkg-prefer-established-libraries`](rules/pkg-prefer-established-libraries.md) - Prefer standard library and established maintained packages over custom or hand-rolled reimplementations.
- [`pkg-py-typed-marker`](rules/pkg-py-typed-marker.md) - Include a `py.typed` marker file in packaged libraries to signal type checker support (PEP 561).
- [`pkg-uv-lockfile`](rules/pkg-uv-lockfile.md) - Commit `uv.lock` or target platform lockfiles for reproducible, deterministic application deployments.

### 10. Testing with Pytest (MEDIUM)

- [`test-async-pytest`](rules/test-async-pytest.md) - Use the async test plugin and mode already configured by the repository; avoid manual event-loop lifecycle management.
- [`test-monkeypatch-clean`](rules/test-monkeypatch-clean.md) - Use pytest's `monkeypatch` fixture instead of `unittest.mock.patch` for automatic teardown and environment overrides.
- [`test-parametrize-matrix`](rules/test-parametrize-matrix.md) - Use `@pytest.mark.parametrize` to test boundary values and equivalence partitions without code duplication.
- [`test-pytest-fixtures-scope`](rules/test-pytest-fixtures-scope.md) - Use explicit fixture scopes (`function`, `module`, `session`) and avoid mutable shared fixture state.
- [`test-pytest-raises-match`](rules/test-pytest-raises-match.md) - Scope `pytest.raises` to the exact failing operation; assert exception attributes or match text when error content is contractual.
- [`test-tmp-path-filesystem`](rules/test-tmp-path-filesystem.md) - Use the standard `tmp_path` fixture for all filesystem-dependent tests; never hardcode `/tmp`.

### 11. Logging & Observability (MEDIUM)

- [`obs-lazy-logging-interpolation`](rules/obs-lazy-logging-interpolation.md) - Defer message formatting with `%s` arguments in logger calls, and guard expensive argument computation with `isEnabledFor`.
- [`obs-logger-hierarchy`](rules/obs-logger-hierarchy.md) - Always instantiate loggers using `logging.getLogger(__name__)` at module level; never use the root logger.
- [`obs-structured-logging`](rules/obs-structured-logging.md) - Use structured logging (JSON / key-value context) instead of unstructured formatted strings in production.
- [`obs-tracebacks-exc-info`](rules/obs-tracebacks-exc-info.md) - Pass `exc_info=True` or use `logger.exception()` inside `except` blocks to record stack traces.

### 12. API & Module Design (MEDIUM)

- [`api-composition-over-inheritance`](rules/api-composition-over-inheritance.md) - Prefer composition and structural protocols over deep class inheritance hierarchies.
- [`api-explicit-all-exports`](rules/api-explicit-all-exports.md) - Define explicit `__all__` in public package `__init__.py` modules to document the public API.
- [`api-immutability-defensive-copy`](rules/api-immutability-defensive-copy.md) - Return immutable collections (`tuple`, `MappingProxyType`, `frozenset`) from getters to prevent external state tampering.
- [`api-kwonly-arguments`](rules/api-kwonly-arguments.md) - Use keyword-only arguments (`*`) for functions with multiple boolean flags or optional configuration parameters.

### 13. Common Anti-Patterns (REFERENCE)

- [`anti-dynamic-attribute-injection`](rules/anti-dynamic-attribute-injection.md) - Avoid monkey-patching arbitrary dynamic attributes onto third-party or library class instances (`setattr(obj, ...)`).
- [`anti-is-literal-comparison`](rules/anti-is-literal-comparison.md) - Use `==` for value equality and reserve `is` for object identity checks (`is None` and sentinel objects).
- [`anti-mutable-default-args`](rules/anti-mutable-default-args.md) - Never use mutable objects (`list`, `dict`, `set`) as default parameter values; use `None` and initialize inside the function.
- [`anti-shadowing-builtins`](rules/anti-shadowing-builtins.md) - Never name variables, arguments, or attributes after Python built-in functions (`id`, `type`, `list`, `dict`, `dir`, `input`, `filter`).
- [`anti-wildcard-imports`](rules/anti-wildcard-imports.md) - Never use wildcard imports (`from module import *`); import explicit names or modules.

---

## Modern Performance & Rust-Backed Tooling Decision Matrix

When architecting performance-critical Python services or data pipelines, prefer maintained Rust-backed tooling where the workload and compatibility fit. Always verify repository constraints, target Python version, and deployment platform wheels before adopting.

| Tool | Workload Fit / Role | Core Engine | Compatibility Gate | Adoption Guidance & Caveats |
|------|---------------------|-------------|--------------------|-----------------------------|
| `uv` | Dependencies, environments, packaging | Rust | Project Python and lockfile | Default when unconstrained; do not add a competing package manager. |
| `ruff` | Linting, formatting, import sorting | Rust | Configured target and rule/plugin parity | Prefer for new projects; preserve established checks and formatting contracts. |
| `polars` | Tabular processing, ETL, analytics | Rust | Python and native runtime wheels | Prefer over pandas for NEW tabular work; lazy scans, expressions, and explicit null/order semantics. |
| `granian` | ASGI HTTP serving | Rust (Tokio / Hyper) | Python, wheels, ASGI/deployment requirements | Prefer for NEW compatible FastAPI deployments; retain Python async semantics and verify lifecycle behavior. |
| `pydantic` v2 | Boundary validation and serialization | Rust (`pydantic-core`) | Framework/schema compatibility | Prefer native typed responses on supported FastAPI versions; validation can coerce unless strictness is explicitly configured. |
| `orjson` | Raw JSON encoding/decoding | Rust | Bytes, numeric, UTF-8 and datetime contracts | `dumps` returns bytes and holds the GIL; not a blanket FastAPI response override. |
| `ty` | Type checking | Rust | Typing features, plugins and CI parity | Evaluate when unconstrained; retain mypy/Pyright where the existing contract needs them. |
| `maturin` / `PyO3` | Custom native extensions | Rust | Rust toolchain, Python ABI and wheel targets | Only for profiler-proven kernels; not a pure-Python build-backend replacement. |

### Tooling Adoption Rules of Thumb

- **Current Stable Resolution at Adoption**: Do not hardcode transient tool or library versions into static repository guidelines. Always resolve current stable versions from PyPI, official documentation, and lockfile constraints at adoption time.
- **Python Baseline & Modern Performance Stack**: The general language pack supports Python 3.9+, but current Polars, Granian, orjson, and FastAPI releases require a newer baseline. Recheck each selected release's `Requires-Python`; never force an unrequested repository-wide interpreter upgrade.
- **Native Transitive Wheels**: Packages like `polars` distribute packaging wheels that delegate to platform-specific native runtime wheels. Ensure precompiled wheels exist for your deployment architecture (e.g. `manylinux`, macOS `arm64`, Windows, or `musl`/Alpine) to prevent slow or failing source builds in container environments.
- **Accurate Runtime Classification**: Do not mislabel non-Rust performance tools as Rust:
  - `msgspec` is a C extension.
  - `uvloop` is written in Cython wrapping `libuv` (C).
  - `DuckDB` is written in C++.
  Accurate identification prevents incorrect assumptions regarding toolchains and memory safety guarantees.
- **Preserve Established Contracts**: Never replace established, working HTTP clients (`httpx`, `aiohttp`, `requests`) or existing pandas / Uvicorn deployments without profiling evidence proving a clear bottleneck.
- **Type Checking**: Consider modern type checkers like `ty` only when static typing compatibility and ecosystem requirements are proven.

---

## How to Use

This skill provides indexed rule identifiers for targeted application. When developing or reviewing Python code:

1. **Determine repository constraints**: Inspect `requires-python` in `pyproject.toml` or target runtime before using modern syntax.
2. **Check relevant categories** based on the specific engineering task.
3. **Prioritize rules**: CRITICAL > HIGH > MEDIUM > REFERENCE.
4. **Consult standalone rule files** in `rules/` for concrete Bad/Good implementations.

### Rule Application by Task

| Task | Primary Categories |
|------|-------------------|
| Project setup & dependencies | `proj-`, `pkg-` |
| Domain modeling & types | `type-`, `api-` |
| Error handling & cleanup | `err-`, `obs-` |
| Async I/O & task groups | `async-`, `err-` |
| CPU parallelism / multiprocessing | `conc-`, `perf-` |
| Tabular data & analytics pipelines | `perf-`, `iter-` |
| ASGI web serving & API services | `perf-`, `async-` |
| Streaming & data pipelines | `iter-`, `perf-` |
| Performance & memory tuning | `perf-`, `iter-` |
| Security auditing & IO boundaries | `sec-`, `type-` |
| Testing & fixtures | `test-`, `proj-` |
| Logging & tracing | `obs-`, `err-` |
| Public library / API design | `api-`, `type-`, `pkg-` |
| Code review & smell refactoring | `anti-`, `sec-`, `perf-` |

---

## Sources & Attribution

This skill is an independent synthesis of official Python enhancement proposals (PEPs), standard library documentation, and production practices from widely adopted projects.

**Official Python Standards & PEPs**
- [PEP 8](https://peps.python.org/pep-0008/) — Style Guide for Python Code
- [PEP 484](https://peps.python.org/pep-0484/) / [PEP 561](https://peps.python.org/pep-0561/) / [PEP 695](https://peps.python.org/pep-0695/) — Type Hinting and Generics
- [PEP 517](https://peps.python.org/pep-0517/) / [PEP 518](https://peps.python.org/pep-0518/) / [PEP 621](https://peps.python.org/pep-0621/) — Modern Packaging Metadata
- [Python Documentation](https://docs.python.org/3/) — Language Reference, Data Model, and Standard Library

**Production Ecosystem Standards**
- [Pydantic V2](https://docs.pydantic.dev/latest/) — Data validation and settings management
- [Pytest Documentation](https://docs.pytest.org/en/stable/) — Testing framework practices
- [Astral uv Documentation](https://docs.astral.sh/uv/) — Fast Python packaging and project management
- [Mypy & Pyright](https://mypy.readthedocs.io/) — Static typing best practices
- [Polars Documentation](https://docs.pola.rs/) — Vectorized multithreaded DataFrame library
- [Granian Documentation](https://github.com/emmett-framework/granian) — High-performance Rust HTTP server for Python
- [PyO3 & Maturin](https://pyo3.rs/) — Rust bindings and packaging for CPython
