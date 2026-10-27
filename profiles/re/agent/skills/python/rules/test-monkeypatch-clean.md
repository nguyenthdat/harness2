# test-monkeypatch-clean

> Use pytest's `monkeypatch` fixture instead of `unittest.mock.patch` for automatic teardown and environment overrides.

## Why It Matters

Manual mocking or decorators can leak modified global state or environment variables across tests if an error occurs. Pytest's `monkeypatch` fixture guarantees automatic, reliable restoration at the end of each test.

## Bad

```python
import os

# Bad: Manual environment mutation can leak across tests if test fails midway
def test_env_config():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    config = load_config()
    assert config.is_test is True
    # If assert fails, os.environ is never cleaned up!
    del os.environ["DATABASE_URL"]
```

## Good

```python
import pytest

# Good: monkeypatch fixture restores original state automatically
def test_env_config(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    config = load_config()
    assert config.is_test is True
```

## See Also

- [test-tmp-path-filesystem](test-tmp-path-filesystem.md) - Isolated filesystem testing
- [test-pytest-fixtures-scope](test-pytest-fixtures-scope.md) - Fixture scoping
