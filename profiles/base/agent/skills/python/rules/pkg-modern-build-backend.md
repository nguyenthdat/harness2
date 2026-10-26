# pkg-modern-build-backend

> Use standard declarative build backends (`hatchling`, `flit-core`, `setuptools>=61`) for pure-Python packages in `pyproject.toml`; allow `maturin` only when building compiled Rust extensions.

## Why It Matters

PEP 517 and PEP 518 define standard build-system interfaces so tools such as uv can invoke a backend declaratively. Preserve an established Hatchling, Flit, or Setuptools backend for pure-Python packages. For an actual Rust/PyO3 extension, evaluate maturin with `build-backend = "maturin"` and verify the Cargo crate, Python module name, ABI, and target wheels. Consuming a Rust-backed wheel does not require migrating your own package to maturin.

## Bad

```python
# Bad: Legacy setup.py with custom procedural logic
from setuptools import setup

setup(
    name="my-package",
    version="1.0.0",
    # Procedural execution during packaging discovery
)
```

## Good

```toml
# Good: Declarative build backend configuration in pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "1.0.0"
readme = "README.md"
requires-python = ">=3.11"
```

```toml
# Good: Maturin build backend used ONLY when compiling Rust extensions (PyO3)
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "fast-kernel"
version = "0.1.0"
requires-python = ">=3.10"

[tool.maturin]
module-name = "fast_kernel._native"
bindings = "pyo3"
```

## See Also

- [proj-pyproject-single-source](proj-pyproject-single-source.md) - pyproject.toml single source of truth
- [pkg-avoid-setup-py](pkg-avoid-setup-py.md) - Avoiding legacy setup.py commands
- [perf-rust-library-selection](perf-rust-library-selection.md) - Selecting Rust-backed tools
