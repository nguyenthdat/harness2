# anti-dynamic-attribute-injection

> Avoid monkey-patching arbitrary dynamic attributes onto third-party or library class instances (`setattr(obj, ...)`).

## Why It Matters

Attaching arbitrary attributes to foreign objects bypasses static type checkers, creates memory leaks if the object is cached or pooled, and leads to runtime `AttributeError` when upstream libraries refactor internal structures.

## Bad

```python
# Bad: Attaching custom state to foreign request or connection objects
def handle_request(request):
    # Monkey-patching custom attribute on framework object
    request.custom_user_cache = {"role": "admin"}
```

## Good

```python
from dataclasses import dataclass

# Good: Use explicit wrapper context or ContextVar
# (Use slots=True on Python 3.10+)
@dataclass
class RequestContext:
    request: object
    user_cache: dict[str, str]
```

## See Also

- [api-composition-over-inheritance](api-composition-over-inheritance.md) - Composition wrapper patterns
- [type-dataclass-vs-pydantic](type-dataclass-vs-pydantic.md) - Dataclasses for context wrappers
