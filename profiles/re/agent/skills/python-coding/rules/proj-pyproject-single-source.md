# proj-pyproject-single-source

> Use `pyproject.toml` (PEP 517/518/621) as the single source of truth for build metadata and tool configurations.

## Why It Matters

Spreading configuration across legacy `setup.py`, `setup.cfg`, `requirements.txt`, `.flake8`, and `pytest.ini` leads to configuration drift, duplicate dependencies, and broken environments. Modern Python tools (uv, ruff, mypy, pytest, hatchling, setuptools) all support unified configuration in `pyproject.toml`.

## Bad

```python
# Fragmented configuration files:
# requirements.txt -> fastapi==0.110.0
# setup.py -> install_requires=['fastapi>=0.100.0']
# .flake8 -> max-line-length = 88
# pytest.ini -> [pytest] testpaths = tests
# mypy.ini -> [mypy] strict = True
```

## Good

```python
# pyproject.toml - Unified single source of truth
[project]
name = "my-service"
version = "0.1.0"
description = "Core payment processing service"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110.0",
    "pydantic>=2.6.0",
    "httpx>=0.27.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "mypy>=1.9.0",
    "ruff>=0.3.0",
]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

## See Also

- [proj-version-compatibility](proj-version-compatibility.md) - Check version compatibility
- [pkg-modern-build-backend](pkg-modern-build-backend.md) - Modern build backend configuration
- [pkg-avoid-setup-py](pkg-avoid-setup-py.md) - Eliminate legacy setup.py
