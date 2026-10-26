# pkg-py-typed-marker

> Include a `py.typed` marker file in packaged libraries to signal type checker support (PEP 561).

## Why It Matters

Static type checkers (mypy, pyright) ignore type annotations in installed third-party packages unless the package contains an empty `py.typed` marker file in its root package directory.

## Bad

```python
# Bad: Package with full type annotations but missing py.typed marker
src/
└── my_library/
    ├── __init__.py
    └── core.py
# Mypy will report: "Skipping analyzing 'my_library': module is installed, but missing library stubs or py.typed marker"
```

## Good

```python
# Good: py.typed marker included in package directory
src/
└── my_library/
    ├── __init__.py
    ├── core.py
    └── py.typed  # Empty marker file required by PEP 561

# Ensure pyproject.toml includes package data if necessary
[tool.hatch.build.targets.wheel]
packages = ["src/my_library"]
```

## See Also

- [proj-type-checker-config](proj-type-checker-config.md) - Type checker configuration
- [type-protocols-structural](type-protocols-structural.md) - Exporting structural protocols
