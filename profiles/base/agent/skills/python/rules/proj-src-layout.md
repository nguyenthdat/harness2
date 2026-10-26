# proj-src-layout

> Use the `src/` package layout (`src/<package>/`) to isolate imported code from local working directory files.

## Why It Matters

In a flat layout (`./mypackage/`), running tests or python scripts in the repository root imports the local uninstalled source folder directly, masking missing package data, build packaging errors, or broken editable installs. A `src/` layout forces tools to import from the properly installed package in site-packages or editable environment.

## Bad

```python
# Flat layout: tests can import ./mypackage even when package installation fails
my_project/
├── mypackage/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
└── pyproject.toml
```

## Good

```python
# Robust src layout:
my_project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── core.py
│       └── py.typed
├── tests/
│   └── test_core.py
├── pyproject.toml
└── README.md
```

## Verification
When using `src/` layout, running `pytest` tests against the installed package in `.venv`, preventing false-positive test passes where local untracked files are accidentally picked up by Python's `sys.path[0]`.

## See Also

- [proj-pyproject-single-source](proj-pyproject-single-source.md) - Single source of truth in pyproject.toml
- [pkg-modern-build-backend](pkg-modern-build-backend.md) - Build backend packaging configuration
