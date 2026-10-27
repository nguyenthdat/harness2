# pkg-dependency-pinning

> Use semantic lower/upper bounds for library dependencies and lockfiles for deployable applications.

## Why It Matters

Over-constraining library dependencies (e.g. `requests==2.31.0`) prevents end-user applications from resolving compatible transitive dependency graphs. Under-constraining applications leads to unexpected runtime breakage.

## Bad

```python
# Bad: Library pinning exact versions
# In a reusable library's pyproject.toml:
dependencies = [
    "pydantic==2.6.1",  # Prevents applications using pydantic 2.7+ from installing this library!
]
```

## Good

```python
# Good (for libraries): Flexible semantic version ranges
dependencies = [
    "pydantic>=2.4.0,<3.0.0",
]

# Good (for applications / services):
# Commit uv.lock or poetry.lock for exact reproducibility.
```

## See Also

- [pkg-uv-lockfile](pkg-uv-lockfile.md) - Deterministic lockfiles with uv
- [pkg-modern-build-backend](pkg-modern-build-backend.md) - Modern build backend configuration
