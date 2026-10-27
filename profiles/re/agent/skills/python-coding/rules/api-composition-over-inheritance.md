# api-composition-over-inheritance

> Prefer composition and structural protocols over deep class inheritance hierarchies.

## Why It Matters

Deep class inheritance creates tight coupling, fragile base class problems, and confusing MRO (Method Resolution Order) chains. Composition and dependency injection make components independently testable, replaceable, and mockable.

## Bad

```python
# Bad: Deep rigid inheritance hierarchy
class BaseService:
    ...
class AuthenticatedService(BaseService):
    ...
class UserDatabaseService(AuthenticatedService):
    ...
```

## Good

```python
from dataclasses import dataclass
from typing import Protocol

class Authenticator(Protocol):
    def authenticate(self, token: str) -> bool: ...

class UserRepository(Protocol):
    def get_user(self, user_id: str) -> dict: ...

# Good: Composed service with injected protocol dependencies
# (Use slots=True on Python 3.10+)
@dataclass
class UserService:
    auth: Authenticator
    repo: UserRepository

    def get_profile(self, token: str, user_id: str) -> dict:
        if not self.auth.authenticate(token):
            raise PermissionError("Unauthorized")
        return self.repo.get_user(user_id)
```

## See Also

- [type-protocols-structural](type-protocols-structural.md) - Structural subtyping with Protocol
- [api-kwonly-arguments](api-kwonly-arguments.md) - Keyword-only parameters
