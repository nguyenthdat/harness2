# obs-structured-logging

> Use structured logging (JSON / key-value context) instead of unstructured formatted strings in production.

## Why It Matters

Unstructured strings (`logger.info(f'User {u} logged in')`) cannot be indexed or queried by log aggregators (Elasticsearch, Datadog, CloudWatch). Passing structured fields or using `structlog` allows precise filtering and metrics.

## Bad

```python
import logging
logger = logging.getLogger(__name__)

# Bad: f-string prevents machine indexing and wastes CPU formatting unlogged messages
def log_login(user_id: str, ip: str):
    logger.info(f"User {user_id} logged in from IP {ip}")
```

## Good

```python
import logging
logger = logging.getLogger(__name__)

# Good: Standard logging with extra dictionary for structured ingestion
def log_login(user_id: str, ip: str):
    logger.info(
        "User login successful",
        extra={"user_id": user_id, "client_ip": ip, "event_type": "auth_login"}
    )
```

## See Also

- [obs-lazy-logging-interpolation](obs-lazy-logging-interpolation.md) - Lazy string formatting in logging
- [obs-tracebacks-exc-info](obs-tracebacks-exc-info.md) - Exception logging
