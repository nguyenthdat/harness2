# type-typeddict-raw-data

> Use `TypedDict` with `NotRequired` (or `total=False`) for typed dictionary shapes without runtime validation overhead.

## Why It Matters

When dealing with legacy APIs or raw dictionary transformations where runtime schema instantiation is unnecessary, `TypedDict` provides compile-time key and type validation without the overhead of class instantiation. For Python 3.9/3.10, import `NotRequired` from `typing_extensions`; on Python 3.11+, use standard library `typing.NotRequired`.

## Bad

```python
from typing import Any

# Bad: Untyped dictionary signatures disable type checking on dict keys
def format_headers(headers: dict[str, Any]) -> dict[str, str]:
    return {k: str(v) for k, v in headers.items()}
```

## Good

```python
import sys
from typing import TypedDict

# Good: Version-portable NotRequired import
if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

class RequestHeaders(TypedDict):
    authorization: str
    content_type: str
    trace_id: NotRequired[str]

def format_headers(headers: RequestHeaders) -> dict[str, str]:
    auth = headers["authorization"]
    res = {"Authorization": auth, "Content-Type": headers["content_type"]}
    if "trace_id" in headers:
        res["X-Trace-ID"] = headers["trace_id"]
    return res
```

## See Also

- [type-pydantic-boundaries](type-pydantic-boundaries.md) - Boundary validation with Pydantic
- [type-dataclass-vs-pydantic](type-dataclass-vs-pydantic.md) - Dataclasses vs Pydantic
