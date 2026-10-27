# perf-slots-memory

> Use `__slots__` or `@dataclass(slots=True)` for classes instantiated in high volumes to eliminate `__dict__` overhead.

## Why It Matters

Standard Python objects store instance attributes in a per-instance `__dict__` dictionary, consuming ~150-200 bytes per object. `__slots__` replaces `__dict__` with a fixed-size array of descriptor pointers, reducing memory by up to 60% and speeding up attribute access.

## Bad

```python
# Bad: Creates a __dict__ for every one of 10,000,000 coordinate points
class Point:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z
```

## Good

```python
from dataclasses import dataclass

# Good: slots=True (Python 3.10+) eliminates __dict__ and __weakref__
@dataclass(slots=True, frozen=True)
class Point:
    x: float
    y: float
    z: float

# Or manual slots in standard classes:
class ManualPoint:
    __slots__ = ("x", "y", "z")
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z
```

## See Also

- [type-dataclass-vs-pydantic](type-dataclass-vs-pydantic.md) - Dataclass vs Pydantic
- [perf-generators-memory](perf-generators-memory.md) - Memory optimization with generators
