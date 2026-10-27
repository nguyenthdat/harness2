# pkg-avoid-setup-py

> Prefer PEP 517/621 builds and never invoke deprecated `setup.py` commands; migrate legacy metadata only when in scope.

## Why It Matters

Commands such as `python setup.py install`, `develop`, and `test` are deprecated. A `setup.py` file and `setup.cfg` remain supported configuration inputs for setuptools projects, so their presence is not itself invalid. New projects should prefer declarative `pyproject.toml`; existing projects should migrate deliberately without breaking their release contract.

## Bad

```console
# Bad: direct legacy commands bypass the modern build frontend.
$ python setup.py install
$ python setup.py test
```

## Good

```python
# Good: Modern declarative pyproject.toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "modern-app"
version = "0.1.0"
```

## See Also

- [pkg-modern-build-backend](pkg-modern-build-backend.md) - Modern build backend selection
- [proj-src-layout](proj-src-layout.md) - Package layout best practices
