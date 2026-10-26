# err-reraise-from

> Always use `raise NewException(...) from err` to preserve exception cause and traceback chains.

## Why It Matters

Wrapping an exception without `from err` creates confusing 'During handling of the above exception, another exception occurred' diagnostics and may hide the root cause in production logs. Using `from None` explicitly suppresses the cause when intentionally hidden.

## Bad

```python
# Bad: Masking the original exception context
try:
    data = json.loads(raw_str)
except json.JSONDecodeError as exc:
    raise ConfigParseError("Failed to parse config file")  # Lost exception chain!
```

## Good

```python
# Good: Explicitly chained exception cause
try:
    data = json.loads(raw_str)
except json.JSONDecodeError as exc:
    raise ConfigParseError("Failed to parse config file") from exc

# Good (when intentionally suppressing internal implementation details from security/public API):
# raise PublicAPIError("Invalid request payload") from None
```

## See Also

- [err-custom-hierarchy](err-custom-hierarchy.md) - Domain exception hierarchy
- [obs-tracebacks-exc-info](obs-tracebacks-exc-info.md) - Logging exceptions with full tracebacks
