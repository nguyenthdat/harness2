# sec-secrets-constant-time

> Use `secrets.compare_digest` for comparing hashes, tokens, and HMACs to prevent timing attacks.

## Why It Matters

Standard string comparison (`token == expected`) returns `False` immediately upon encountering the first mismatching character. Attackers can measure subtle microsecond differences in response time to guess tokens byte by byte.

## Bad

```python
# Bad: Early return in standard string equality allows timing side-channel attacks
def verify_token(user_token: str, secret_token: str) -> bool:
    return user_token == secret_token  # Vulnerable to timing attack
```

## Good

```python
import secrets

# Good: Constant-time comparison defends against timing attacks
def verify_token(user_token: str, secret_token: str) -> bool:
    return secrets.compare_digest(user_token, secret_token)
```

## See Also

- [sec-avoid-eval-exec](sec-avoid-eval-exec.md) - Avoiding dynamic evaluation
- [api-explicit-all-exports](api-explicit-all-exports.md) - API boundary design
