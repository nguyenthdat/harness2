# err-avoid-bare-except

> Never use bare `except:` or catch `BaseException`; catch specific exceptions or `Exception`.

## Why It Matters

Bare `except:` catches `KeyboardInterrupt`, `SystemExit`, and generator/async cancellation signals (`asyncio.CancelledError`), preventing processes from shutting down gracefully or responding to termination signals.

## Bad

```python
# Bad: Silently swallowing all signals and exceptions
try:
    run_worker()
except:
    pass  # Swallows SIGINT / KeyboardInterrupt / SystemExit!
```

## Good

```python
# Good: Catching specific anticipated errors
try:
    run_worker()
except (ConnectionResetError, TimeoutError) as exc:
    logger.warning("Worker transient error: %s", exc)
except Exception as exc:
    logger.error("Unexpected worker failure", exc_info=True)
    raise
```

## See Also

- [err-custom-hierarchy](err-custom-hierarchy.md) - Domain exception hierarchy
- [obs-tracebacks-exc-info](obs-tracebacks-exc-info.md) - Logging exceptions properly
