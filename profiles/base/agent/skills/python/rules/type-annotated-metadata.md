# type-annotated-metadata

> Use `typing.Annotated` to attach validation, serialization, or dependency injection metadata to types.

## Why It Matters

`Annotated[T, ...]` allows attaching runtime metadata (such as Pydantic constraints, FastAPI dependencies, or Typer options) without losing static type checking for base type `T`.

## Bad

```python
# Bad: Creating custom wrapper classes solely to attach validation constraints
class PositiveInt:
    def __init__(self, val: int):
        if val <= 0:
            raise ValueError("Must be positive")
        self.val = val
```

## Good

```python
from typing import Annotated
from pydantic import Field, BaseModel

PositiveInt = Annotated[int, Field(gt=0, description="Strictly positive integer")]

class Account(BaseModel):
    balance: PositiveInt
```

## See Also

- [type-pydantic-boundaries](type-pydantic-boundaries.md) - Pydantic boundary models
- [api-composition-over-inheritance](api-composition-over-inheritance.md) - Composition and metadata
