# api-explicit-all-exports

> Define explicit `__all__` in public package `__init__.py` modules to document the public API.

## Why It Matters

Without `__all__`, wildcard imports (`from pkg import *`) and auto-complete tools expose internal helper functions, private submodules, and third-party imports, causing accidental coupling and breaking changes on internal refactors.

## Bad

```python
# src/mypackage/__init__.py
# Bad: Leaks internal imports (os, sys, helper) into package namespace
import os
import sys
from .core import PublicClient, internal_helper
```

## Good

```python
# src/mypackage/__init__.py
# Good: Explicit __all__ defines stable public contract
from .core import PublicClient

__all__ = ["PublicClient"]
```

## See Also

- [api-kwonly-arguments](api-kwonly-arguments.md) - Keyword-only arguments for clean APIs
- [api-composition-over-inheritance](api-composition-over-inheritance.md) - Composition over inheritance
