# err-custom-hierarchy

> Derive domain-specific exceptions from a single package-level base exception derived from `Exception`.

## Why It Matters

A clear exception hierarchy allows consumers of a library or service to catch either specific errors or all package errors with a single `except PackageError:` clause. Inheriting from `Exception` (never `BaseException`) ensures `KeyboardInterrupt` and `SystemExit` are not accidentally caught.

## Bad

```python
# Bad: Inheriting directly from BaseException or using built-in exceptions everywhere
class ServiceError(BaseException):  # Traps SIGINT/KeyboardInterrupt!
    pass

def query():
    raise ValueError("Database connection lost")  # Generic standard exception
```

## Good

```python
class PackageError(Exception):
    """Base exception for all errors raised by this package."""

class ConnectionError(PackageError):
    """Raised when remote endpoint connection fails."""

class AuthenticationError(PackageError):
    """Raised when credentials fail authentication."""

# Callers can catch specific or all package errors:
# try:
#     client.connect()
# except ConnectionError:
#     ...
# except PackageError:
#     ...
```

## See Also

- [err-reraise-from](err-reraise-from.md) - Preserving cause with raise ... from
- [err-avoid-bare-except](err-avoid-bare-except.md) - Avoiding bare except clauses
