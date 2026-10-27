# test-pytest-raises-match

> Scope `pytest.raises` to the exact failing operation; assert exception attributes or match text when error content is contractual.

## Why It Matters

Wrapping broad code blocks in `pytest.raises(ValueError)` can pass on unintended internal exceptions, causing false positives. To make tests robust, narrow the `pytest.raises` context to the single failing function call. Use `match="regex"` when error messages form an observable API contract; for domain exceptions, assert structured exception attributes.

## Bad

```python
import pytest

# Bad: Broad block where unexpected errors (e.g. inside account setup) produce false passes
def test_deposit():
    with pytest.raises(ValueError):
        account = create_account(balance=100)
        account.deposit(-50)
```

## Good

```python
import pytest

# Good: Narrow scope to the exact failing operation
def test_deposit_negative():
    account = create_account(balance=100)
    with pytest.raises(ValueError, match=r"Deposit amount must be positive"):
        account.deposit(-50)

# Good: Inspect structured custom exception attributes
def test_insufficient_funds():
    account = create_account(balance=50)
    with pytest.raises(InsufficientFundsError) as exc_info:
        account.withdraw(100)
    assert exc_info.value.requested_amount == 100
    assert exc_info.value.available_balance == 50
```

## See Also

- [err-custom-hierarchy](err-custom-hierarchy.md) - Domain exception design
- [test-parametrize-matrix](test-parametrize-matrix.md) - Parametrizing exception tests
