# test-async-pytest

> Use the async test plugin and mode already configured by the repository; avoid manual event-loop lifecycle management.

## Why It Matters

Manual loop creation can leak tasks and produce unclosed-loop warnings. `pytest-asyncio` is one option, but `auto` mode changes marker ownership and can conflict with other async plugins such as AnyIO or Trio integrations. Preserve the repository's plugin and mode; for a new asyncio-only suite, configure one explicitly.

## Bad

```python
import asyncio

# Bad: Manual event loop handling in tests
def test_fetch_user():
    loop = asyncio.new_event_loop()
    user = loop.run_until_complete(fetch_user("123"))
    assert user.id == "123"
    loop.close()
```

## Good

```python
import pytest

# Good when pytest-asyncio strict mode is the repository convention.
@pytest.mark.asyncio
async def test_fetch_user():
    user = await fetch_user("123")
    assert user.id == "123"
```

## See Also

- [async-taskgroups-cancellation](async-taskgroups-cancellation.md) - Async task groups
- [proj-pyproject-single-source](proj-pyproject-single-source.md) - Configuring pytest in pyproject.toml
