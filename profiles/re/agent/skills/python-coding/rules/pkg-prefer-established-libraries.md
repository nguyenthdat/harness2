# pkg-prefer-established-libraries

> Prefer the Python standard library, existing repository dependencies, and established maintained packages over custom or hand-rolled reimplementations.

## Why It Matters

Reimplementing standard protocols, formats, or algorithms by hand is a frequent source of security vulnerabilities (e.g. broken crypto, path traversal, injection), subtle edge-case bugs (e.g. timezone shifts, character encodings, unescaped delimiters), and ongoing maintenance burden. Battle-tested libraries encapsulate years of edge-case discovery, security audits, performance optimizations, and ecosystem compatibility.

## Selection Order

When addressing a functional requirement, evaluate options in strict priority order:

1. **Standard Library**: Always prefer Python's built-in standard library (`pathlib`, `tomllib`, `secrets`, `datetime`, `argparse`, `dataclasses`, etc.) when it satisfies the functional and performance requirements without external dependencies.
2. **Existing Repository Dependencies**: Reuse libraries already declared in the repository's `pyproject.toml` or lockfile. Never introduce a redundant or competing dependency (e.g. do not add `requests` when `httpx` is already used, or `click` when `typer` is established).
3. **Official / Maintained PyPI Libraries**: When stdlib or existing dependencies are insufficient, choose established, actively maintained, widely adopted packages. Vet every candidate per [perf-rust-library-selection](perf-rust-library-selection.md) (license, security advisories, release maintenance, `Requires-Python`, platform wheels).
4. **Hand-Written Code (Last Resort)**: Implement custom logic only when:
   - The logic is domain-specific or trivial and no standard library or existing dependency equivalent exists; or
   - Every external candidate fails vetting (incompatible license, unaddressed vulnerabilities, abandoned maintenance, missing target platform wheels); or
   - The repository explicitly forbids external dependencies.
   - Always state the rationale in code comments or the pull request description when choosing to hand-roll non-trivial logic.

## Never Hand-Roll

Never implement custom or ad-hoc solutions for domains with established standard library or ecosystem implementations:

- **Cryptography, Hashing & Token Generation**: Never invent crypto or use naive random generators for security tokens. Use `secrets` for cryptographically secure random values and tokens; use `hashlib` for standard digests; use `argon2-cffi` or `bcrypt` for password hashing; use `cryptography` for symmetric/asymmetric encryption, certificates, and TLS primitives.
- **TLS & HTTP Clients**: Never write raw socket HTTP parsers. Use `httpx` or `requests` (or stdlib `urllib.request` for trivial zero-dependency scripts).
- **URL, Email & Path Handling**: Never use raw string slicing or regex on filesystem paths, email addresses, or URLs. Use `pathlib` for file paths (see [sec-pathlib-traversal](sec-pathlib-traversal.md)), `urllib.parse` for URLs, and `email.utils` or `email.headerregistry` for email parsing.
- **Structured File & Data Formats**: Never parse or emit JSON, TOML, YAML, CSV, XML, HTML, or INI using custom string splits or regex (see global `structured-parsing`). Use `json`, `tomllib` (Python 3.11+ / `tomli`), `PyYAML` with `safe_load` (see [sec-yaml-safe-load](sec-yaml-safe-load.md)), `csv`, `configparser`, `defusedxml` / `xml.etree` (trusted XML only), and `beautifulsoup4` or `lxml` for HTML.
- **CLI Argument Parsing**: Never inspect `sys.argv` by hand. Use `argparse` in the standard library or `typer` / `click` for richer interfaces.
- **Retries & Exponential Backoff**: Never write manual `while True:` sleep loops. Use `tenacity`.
- **Date & Time Arithmetic**: Never manually compute leap years, epoch offsets, or timezone differences. Use `datetime` with `zoneinfo` (Python 3.9+) or `python-dateutil`.
- **Templating & Escaping**: Never concatenate raw strings to build HTML, SQL, XML, or configuration files. Use `jinja2` for templating; use parameterized queries or `SQLAlchemy` for SQL.
- **Schema Validation & Boundary Models**: Never write manual dictionary inspection routines. Use `pydantic` at boundary layers or `dataclasses` internally (see [type-dataclass-vs-pydantic](type-dataclass-vs-pydantic.md) and [type-pydantic-boundaries](type-pydantic-boundaries.md)).
- **Concurrency Primitives & Queues**: Never invent threading locks or custom async queues. Use `threading`, `multiprocessing`, `queue`, or `asyncio` primitives.
- **Logging & Test Frameworks**: Never use `print()` for production diagnostics or hand-rolled assertions for test suites. Use `logging` or `structlog`, and `pytest` (see [obs-structured-logging](obs-structured-logging.md) and [test-pytest-fixtures-scope](test-pytest-fixtures-scope.md)).

## Domain Reference Matrix

| Domain | Standard Library First | Established PyPI Packages |
|---|---|---|
| **Filesystem Paths** | `pathlib.Path` | — |
| **CLI Arguments** | `argparse` | `typer`, `click` |
| **Configuration (TOML/INI)** | `tomllib` (3.11+), `configparser` | `pydantic-settings`, `tomli` (<3.11) |
| **HTTP Client** | `urllib.request` (basic) | `httpx`, `requests` |
| **Data Validation** | `dataclasses` (internal) | `pydantic` (boundaries) |
| **Retries & Backoff** | — | `tenacity` |
| **Dates & Timezones** | `datetime`, `zoneinfo` (3.9+) | `python-dateutil` |
| **HTML / XML Parsing** | `html.parser`, `xml.etree` (trusted only) | `defusedxml`, `beautifulsoup4`, `lxml` |
| **YAML Parsing** | — | `PyYAML` (`yaml.safe_load`) |
| **Cryptography & Tokens** | `secrets`, `hashlib` | `cryptography`, `argon2-cffi`, `bcrypt` |
| **Templating** | `string.Template` (basic) | `jinja2` |
| **Database & SQL** | `sqlite3` | `SQLAlchemy` |
| **Terminal Output & Styling** | — | `rich` |
| **Logging & Observability** | `logging` | `structlog` |
| **Testing** | `unittest` | `pytest` |
| **Tabular Data** | `csv` (flat tables) | `polars` (see [perf-polars-pipelines](perf-polars-pipelines.md)) |

## Adding Dependencies Idiomatically

- **Project Dependencies**: Add dependencies using `uv add <package>` (or `uv add --dev <package>`), letting `uv` resolve compatibility against `requires-python` and pin in `uv.lock`. Follow [pkg-dependency-pinning](pkg-dependency-pinning.md) and [pkg-uv-lockfile](pkg-uv-lockfile.md).
- **Standalone Scripts (PEP 723)**: In standalone scripts executed with `uv run`, declare dependencies inline via `# /// script` metadata blocks rather than hand-rolling logic to avoid a dependency:
  ```python
  # /// script
  # requires-python = ">=3.11"
  # dependencies = [
  #     "tenacity",
  #     "httpx",
  # ]
  # ///
  ```
- **Use Public APIs Directly**: Call the library's public API directly and idiomatically. Avoid thin wrapper abstractions that simply rename or re-implement what the underlying package already provides.
- **Do Not Vendor Source**: Never copy-paste library code directly into your repository (vendoring) unless required by an explicit, documented policy and permitted by the upstream license.

## Bad

```python
# Bad: Manual retry loop with primitive time.sleep and naive backoff
import time
import requests

def fetch_data(url: str):
    attempts = 0
    while attempts < 3:
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            attempts += 1
            if attempts == 3:
                raise
            time.sleep(2 ** attempts)
```

```python
# Bad: Ad-hoc manual config parsing using string splits
def parse_simple_config(filepath: str) -> dict[str, str]:
    config = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                config[key.strip()] = val.strip().strip('"').strip("'")
    return config
```

## Good

```python
# Good: Declarative, robust retries with tenacity
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True,
)
def fetch_data(url: str) -> dict:
    with httpx.Client(timeout=5.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()
```

```python
# Good: Standard library tomllib for robust, standard-compliant configuration
import tomllib
from pathlib import Path

def parse_config(filepath: Path) -> dict:
    with filepath.open("rb") as f:
        return tomllib.load(f)
```

## See Also

- [perf-rust-library-selection](perf-rust-library-selection.md) - Vetting criteria, native wheels, and performance stack selection
- [pkg-dependency-pinning](pkg-dependency-pinning.md) - Version constraints for libraries vs applications
- [pkg-uv-lockfile](pkg-uv-lockfile.md) - Deterministic lockfile workflows with uv
- [sec-yaml-safe-load](sec-yaml-safe-load.md) - Safe deserialization with PyYAML
- [sec-pathlib-traversal](sec-pathlib-traversal.md) - Safe filesystem navigation using pathlib

## Sources

- [Python Standard Library Documentation](https://docs.python.org/3/library/)
- [Astral uv Script Support (PEP 723)](https://docs.astral.sh/uv/guides/scripts/)
- [Tenacity Documentation](https://tenacity.readthedocs.io/)
- [HTTPX Documentation](https://www.encode.io/httpx/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
