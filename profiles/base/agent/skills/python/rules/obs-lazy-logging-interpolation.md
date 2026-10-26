# obs-lazy-logging-interpolation

> Defer message formatting with `%s` arguments in logger calls, and guard expensive argument computation with `isEnabledFor`.

## Why It Matters

Logging methods (`logger.debug("%s", arg)`) defer string interpolation until the message is confirmed enabled by log levels and filters. However, function arguments passed to `logger.debug(fn())` are evaluated *eagerly* before the logger method is called. For expensive data serialization or state dumping, guard the logging call with `logger.isEnabledFor(logging.DEBUG)` or pass lazy wrapper objects.

## Bad

```python
import logging
logger = logging.getLogger(__name__)

# Bad: f-string formats eagerly even when DEBUG level is disabled
logger.debug(f"Computed matrix state: {dump_large_matrix(matrix)}")

# Bad: dump_large_matrix() is still evaluated eagerly before debug() is invoked!
logger.debug("Computed matrix state: %s", dump_large_matrix(matrix))
```

## Good

```python
import logging
logger = logging.getLogger(__name__)

# Good: Pass pre-computed values as parameters for deferred string interpolation
logger.info("Order processed order_id=%s status=%s", order.id, order.status)

# Good: Guard expensive diagnostic functions with isEnabledFor
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("Computed matrix state: %s", dump_large_matrix(matrix))
```

## See Also

- [obs-structured-logging](obs-structured-logging.md) - Structured logging format
- [obs-logger-hierarchy](obs-logger-hierarchy.md) - Logger hierarchy setup
