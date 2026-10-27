# test-pytest-fixtures-scope

> Use explicit fixture scopes (`function`, `module`, `session`) and avoid mutable shared fixture state.

## Why It Matters

Sharing mutable fixtures (such as database connections or caches) across tests with broad scopes (`scope='session'`) causes test pollution and order-dependent test failures. Keep mutating fixtures function-scoped and read-only setup session-scoped.

## Bad

```python
import pytest

# Bad: Session-scoped mutable list polluted by each test
@pytest.fixture(scope="session")
def shared_user_list():
    return []

def test_add_user_1(shared_user_list):
    shared_user_list.append("Alice")
    assert len(shared_user_list) == 1

def test_add_user_2(shared_user_list):
    # Fails if test_add_user_1 ran first!
    shared_user_list.append("Bob")
    assert len(shared_user_list) == 1  # FAILS!
```

## Good

```python
import pytest

# Good: Read-only expensive setup in session fixture, clean state per test
@pytest.fixture(scope="session")
def db_engine():
    engine = create_test_engine()
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

## See Also

- [test-parametrize-matrix](test-parametrize-matrix.md) - Parametrized testing with pytest
- [test-monkeypatch-clean](test-monkeypatch-clean.md) - Safe monkeypatching
