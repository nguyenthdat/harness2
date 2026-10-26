# obs-tracebacks-exc-info

> Pass `exc_info=True` or use `logger.exception()` inside `except` blocks to record stack traces.

## Why It Matters

`logger.error(str(e))` only captures the error message, discarding the entire stack trace, file numbers, and exception cause chain. `logger.exception()` or `exc_info=True` preserves full diagnostic traces.

## Bad

```python
# Bad: Only logs message, discarding file and line traceback
try:
    process_order(order)
except Exception as e:
    logger.error(f"Order failed: {e}")  # No traceback!
```

## Good

```python
# Good: logger.exception automatically includes full traceback and causes
try:
    process_order(order)
except Exception:
    logger.exception("Order processing failed for order_id=%s", order.id)
```

## See Also

- [err-reraise-from](err-reraise-from.md) - Chained exceptions
- [err-avoid-bare-except](err-avoid-bare-except.md) - Avoiding bare except clauses
