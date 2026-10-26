# proj-virtualenv-isolation

> Always use an isolated virtual environment (`.venv`) or `uv` workspace; never install into system Python.

## Why It Matters

Installing packages into the system or global Python interpreter corrupts operating system tools, leads to conflicting dependency versions across projects, and makes builds non-reproducible. Isolated virtual environments guarantee strict separation of project dependencies.

## Bad

```python
# Bad: Installing globally or assuming system Python environment
# $ pip install requests fastapi
# $ python -c "import requests"
```

## Good

```python
# Good: Creating and managing isolated virtual environment via uv or venv

# With uv (recommended):
# $ uv venv
# $ uv pip install -e .
# Or run commands directly:
# $ uv run pytest

# With standard library venv:
# $ python3 -m venv .venv
# $ source .venv/bin/activate
# $ pip install -e .
```

## See Also

- [pkg-uv-lockfile](pkg-uv-lockfile.md) - Deterministic lockfiles with uv
- [proj-pyproject-single-source](proj-pyproject-single-source.md) - Project metadata in pyproject.toml
