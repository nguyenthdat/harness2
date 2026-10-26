# obs-logger-hierarchy

> Always instantiate loggers using `logging.getLogger(__name__)` at module level; never use the root logger.

## Why It Matters

`logging.info()` calls the root logger directly, making it impossible to configure log levels, handlers, or filters per module/subsystem. `__name__` inherits configuration through the hierarchical dot notation (`pkg.module`).

## Bad

```python
import logging

# Bad: Using root logger directly
def process_data(data):
    logging.info("Processing data")  # Uses root logger!
    logging.error("Failed")
```

## Good

```python
import logging

# Good: Module-scoped logger inherits parent package configuration
logger = logging.getLogger(__name__)

def process_data(data):
    logger.info("Processing data")
    logger.error("Failed")
```

## See Also

- [obs-structured-logging](obs-structured-logging.md) - Structured logging
- [obs-lazy-logging-interpolation](obs-lazy-logging-interpolation.md) - Lazy logging interpolation
