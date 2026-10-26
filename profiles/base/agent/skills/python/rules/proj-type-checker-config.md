# proj-type-checker-config

> Configure strict type checking (mypy/pyright) in `pyproject.toml` aligned with target Python version.

## Why It Matters

Without explicit type-checker configuration, default settings allow implicit `Any`, untyped function definitions, and missed type errors. Aligning the type checker's target Python version with `requires-python` ensures that incompatibilities are caught at lint/check time.

## Bad

```python
# Bad: Running mypy with default loose flags or missing configuration
# mypy src/  (allows untyped defs, ignores missing imports silently)
```

## Good

```python
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true

# Or for Pyright:
[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "strict"
include = ["src", "tests"]
```

## See Also

- [type-avoid-any](type-avoid-any.md) - Avoid Any in type signatures
- [type-narrowing-typeguard](type-narrowing-typeguard.md) - Type narrowing with TypeGuard and TypeIs
