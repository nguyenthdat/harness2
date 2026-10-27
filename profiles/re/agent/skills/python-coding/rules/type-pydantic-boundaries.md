# type-pydantic-boundaries

> Validate external data at system boundaries using Pydantic when installed/standard in the repo, or strict standard library validation models.

## Why It Matters

External inputs (HTTP payloads, environment variables, message queues) are untrusted and loosely typed. Validating at the network/storage perimeter prevents runtime errors inside core logic. When Pydantic is part of the project's dependencies (e.g. in FastAPI or modern services), use strict models; if Pydantic is not a project dependency, use standard library dataclasses with exact type and range checks rather than blind type coercion.

## Bad

```python
# Bad: Manually indexing into raw dictionaries without schema validation or error handling
def handle_webhook(data: dict):
    user_id = data["user"]["id"]  # KeyError if missing!
    amount = float(data["amount"])  # ValueError if invalid string!
    return user_id, amount
```

## Good

```python
# Good (when Pydantic is used in the repository):
from pydantic import BaseModel, ConfigDict, Field

class UserPayload(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    id: str = Field(min_length=1)
    name: str

class WebhookPayload(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    user: UserPayload
    amount: float = Field(gt=0.0)

def handle_webhook(payload: WebhookPayload) -> tuple[str, float]:
    return payload.user.id, payload.amount

# Good (standard-library fallback with exact type validation):
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class SafeUser:
    id: str
    name: str

@dataclass(frozen=True)
class SafeWebhook:
    user: SafeUser
    amount: float

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SafeWebhook":
        user_raw = data.get("user")
        if not isinstance(user_raw, dict):
            raise ValueError("Expected user to be an object")
        user_id = user_raw.get("id")
        user_name = user_raw.get("name")
        if type(user_id) is not str or not user_id.strip():
            raise ValueError("Expected non-empty string for user.id")
        if type(user_name) is not str:
            raise ValueError("Expected string for user.name")
        
        amount_raw = data.get("amount")
        # Reject booleans (which are int subclasses) and non-finite floats
        if type(amount_raw) not in (int, float) or type(amount_raw) is bool:
            raise ValueError("Expected numeric amount")
        amount = float(amount_raw)
        if not math.isfinite(amount) or amount <= 0.0:
            raise ValueError("Expected positive finite amount")
        
        return cls(user=SafeUser(id=user_id, name=user_name), amount=amount)
```

## See Also

- [type-dataclass-vs-pydantic](type-dataclass-vs-pydantic.md) - Choosing dataclasses vs Pydantic
- [type-typeddict-raw-data](type-typeddict-raw-data.md) - TypedDict for untransformed JSON shapes
