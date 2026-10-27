# pkg-uv-lockfile

> Commit `uv.lock` or target platform lockfiles for reproducible, deterministic application deployments.

## Why It Matters

Unpinned dependency resolution in production or CI leads to 'works on my machine' breakage when transitive dependencies release breaking changes. `uv.lock` generates cross-platform, deterministic, cryptographic lockfiles.

## Bad

```python
# Bad: Relying on floating unpinned dependencies in production
# pyproject.toml
[project]
dependencies = [
    "fastapi",
    "sqlalchemy",
]
# No lockfile committed; builds can break at any time when upstream releases updates
```

## Good

```python
# Good: Maintain pyproject.toml with compatibility ranges and commit uv.lock

# Generate lockfile:
# $ uv lock

# Install locked dependencies strictly in CI / Docker:
# $ uv sync --frozen --no-dev
```

## See Also

- [proj-virtualenv-isolation](proj-virtualenv-isolation.md) - Virtual environment isolation
- [pkg-dependency-pinning](pkg-dependency-pinning.md) - Library vs application dependency pinning
