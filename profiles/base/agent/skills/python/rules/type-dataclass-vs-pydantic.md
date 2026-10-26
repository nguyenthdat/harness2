# type-dataclass-vs-pydantic

> Prefer standard dataclasses for internal domain logic; reserve Pydantic for validation boundaries when already adopted.

## Why It Matters

Standard library dataclasses have zero external dependencies and significantly lower instantiation overhead than Pydantic models. On Python 3.10+, `@dataclass(slots=True, frozen=True)` provides compact memory representation and generates a `__hash__` method (provided all field values are themselves hashable). For Python 3.9 projects, `@dataclass(frozen=True)` or explicit `__slots__` provides lightweight domain modeling.

## Bad

```python
# Bad: Using heavy Pydantic models for internal graph node structures or tight algorithm loops
from pydantic import BaseModel

class Node(BaseModel):
    id: int
    weight: float
    # Instantiating 1,000,000 Pydantic nodes incurs substantial validation and memory overhead
```

## Good

```python
from dataclasses import dataclass

# Good (Python 3.10+): slots=True eliminates instance __dict__
@dataclass(slots=True, frozen=True)
class Node:
    id: int
    weight: float

# Good (Python 3.9 compatible): standard frozen dataclass
# @dataclass(frozen=True)
# class Node:
#     id: int
#     weight: float
```

## See Also

- [perf-slots-memory](perf-slots-memory.md) - Memory optimization with __slots__
- [type-pydantic-boundaries](type-pydantic-boundaries.md) - Boundary validation models
