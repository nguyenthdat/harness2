# api-immutability-defensive-copy

> Return immutable collections (`tuple`, `MappingProxyType`, `frozenset`) from getters to prevent external state tampering.

## Why It Matters

Returning references to internal mutable lists or dicts allows external callers to modify private class state without calling class methods, bypassing validation invariants.

## Bad

```python
# Bad: Returning mutable internal list allows external corruption
class Registry:
    def __init__(self):
        self._handlers = []

    def get_handlers(self) -> list:
        return self._handlers  # Caller can call .clear() or .pop() directly!
```

## Good

```python
from types import MappingProxyType
from typing import Sequence

class Registry:
    def __init__(self):
        self._handlers = []

    # Good: Return immutable tuple or Sequence view
    def get_handlers(self) -> tuple:
        return tuple(self._handlers)
```

## See Also

- [type-dataclass-vs-pydantic](type-dataclass-vs-pydantic.md) - Frozen dataclasses
- [anti-mutable-default-args](anti-mutable-default-args.md) - Avoiding mutable default arguments
