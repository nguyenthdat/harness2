# type-variance-typevar

> Declare variance on legacy generic class and protocol type variables; let Python 3.12+ type-parameter syntax infer variance where supported.

## Why It Matters

Variance controls subtyping relationships for generic classes and protocols. With legacy syntax, declare producer parameters covariant, consumer parameters contravariant, and read-write parameters invariant. Python 3.12+ type-parameter syntax normally lets type checkers infer class variance. Generic function type variables express relationships between arguments and results; they do not need covariance or contravariance declarations.

## Bad

```python
from typing import TypeVar, Generic

# Bad: An invariant TypeVar used on a read-only producer class/protocol
T = TypeVar("T")

class ReadOnlySource(Generic[T]):
    def __init__(self, item: T) -> None:
        self._item = item

    def get(self) -> T:
        return self._item

class Animal: pass
class Dog(Animal): pass

def inspect_animal_source(src: ReadOnlySource[Animal]) -> None:
    print(src.get())

dog_source = ReadOnlySource(Dog())
# Type Error with invariant T: ReadOnlySource[Dog] cannot be passed where ReadOnlySource[Animal] is expected!
inspect_animal_source(dog_source)
```

## Good

```python
from typing import TypeVar, Generic

# Good (Python 3.9-3.11): Covariant TypeVar for read-only producer container
T_co = TypeVar("T_co", covariant=True)

class ReadOnlySource(Generic[T_co]):
    def __init__(self, item: T_co) -> None:
        self._item = item

    def get(self) -> T_co:
        return self._item

class Animal: pass
class Dog(Animal): pass

def inspect_animal_source(src: ReadOnlySource[Animal]) -> None:
    print(src.get())

# Valid: ReadOnlySource[Dog] is a subtype of ReadOnlySource[Animal]
dog_source: ReadOnlySource[Dog] = ReadOnlySource(Dog())
inspect_animal_source(dog_source)

# Ordinary generic functions express argument/result relationships without
# declaring variance on their TypeVar.
T = TypeVar("T")
def first_item(items: list[T]) -> T:
    return items[0]
```

## See Also

- [proj-version-compatibility](proj-version-compatibility.md) - Target Python version compatibility
- [type-protocols-structural](type-protocols-structural.md) - Generic structural protocols
