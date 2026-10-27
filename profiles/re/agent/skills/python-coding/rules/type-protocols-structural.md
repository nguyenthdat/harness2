# type-protocols-structural

> Use `typing.Protocol` for structural subtyping (duck typing) instead of tight abstract base class inheritance.

## Why It Matters

`Protocol` enables compile-time verification of interfaces without forcing third-party or caller types to inherit from an abstract base class. This keeps libraries decoupled and composable.

## Bad

```python
from abc import ABC, abstractmethod

# Bad: Requiring callers to inherit from an internal ABC
class Renderable(ABC):
    @abstractmethod
    def render(self) -> str: ...

def display(item: Renderable) -> None:
    print(item.render())
```

## Good

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Renderable(Protocol):
    def render(self) -> str:
        ...

# Any class with a .render() -> str method satisfies Renderable without inheriting
class MarkdownDoc:
    def render(self) -> str:
        return "# Title"

def display(item: Renderable) -> None:
    print(item.render())
```

## See Also

- [api-composition-over-inheritance](api-composition-over-inheritance.md) - Composition over inheritance
- [type-avoid-any](type-avoid-any.md) - Avoiding Any with Protocols
