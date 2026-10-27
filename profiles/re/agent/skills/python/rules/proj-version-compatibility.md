# proj-version-compatibility

> Check and respect declared `requires-python` / `python_version` before adopting newer language features.

## Why It Matters

Python evolves across releases (e.g. `match`/`case` in 3.10, `ExceptionGroup` and `TaskGroup` in 3.11, PEP 695 type parameter syntax in 3.12, experimental free-threaded builds in 3.13, template string literals in 3.14). Using syntax or standard library features not supported by the repository's minimum declared Python version (`requires-python` in `pyproject.toml`) causes runtime `SyntaxError` or `ImportError` on supported deployments.

## Bad

```python
# pyproject.toml declares: requires-python = ">=3.9"

# Bad: Using PEP 695 type parameters (Python 3.12+) in a 3.9+ project
type Point[T] = tuple[T, T]  # SyntaxError on Python 3.9-3.11!

# Bad: Using structural pattern matching (Python 3.10+) in a 3.9+ project
def handle(val: object) -> str:
    match val:  # SyntaxError on Python 3.9!
        case int():
            return "int"
        case _:
            return "other"
```

## Good

```python
# For projects supporting Python 3.9+:
from typing import TypeVar, Tuple

T = TypeVar("T")
Point = Tuple[T, T]  # Compatible with Python 3.9+

def handle(val: object) -> str:
    if isinstance(val, int):
        return "int"
    return "other"

# If Python 3.11+ is explicitly required in pyproject.toml (requires-python = ">=3.11"):
# async with asyncio.TaskGroup() as tg: ... is fully allowed.
```

## Version Feature Reference

- **Python 3.9**: Built-in generic types (`list[str]`, `dict[str, int]`), `|` operator for dict merging.
- **Python 3.10**: Structural pattern matching (`match`/`case`), union type operator (`X | Y`), `zip(..., strict=True)`, `@dataclass(slots=True)`.
- **Python 3.11**: `asyncio.TaskGroup`, `ExceptionGroup` / `except*`, `typing.Self`, stdlib `tomllib`, `typing.NotRequired`.
- **Python 3.12**: PEP 695 type parameter syntax (`type X[T] = ...`, <code>def func&#91;T&#93;(...)</code>), override decorator (`@typing.override`), `itertools.batched`.
- **Python 3.13**: Free-threaded Python without GIL (experimental PEP 703), JIT compiler (PEP 744), `typing.TypeIs` (PEP 742).
- **Python 3.14**: Template string literals (PEP 750, t-strings), deferred annotation evaluation (PEP 649).

## See Also

- [proj-pyproject-single-source](proj-pyproject-single-source.md) - Use pyproject.toml as single source of truth
- [type-variance-typevar](type-variance-typevar.md) - Type variable declarations across Python versions
