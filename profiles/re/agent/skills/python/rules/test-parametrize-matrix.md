# test-parametrize-matrix

> Use `@pytest.mark.parametrize` to test boundary values and equivalence partitions without code duplication.

## Why It Matters

Writing separate test functions with identical assertion logic creates bloated test suites that are tedious to maintain. `@pytest.mark.parametrize` runs each case as an independent, clearly named test.

## Bad

```python
# Bad: Repetitive copy-pasted test functions
def test_parse_valid_ipv4():
    assert parse_ip("192.168.1.1") == IPv4Address("192.168.1.1")

def test_parse_valid_ipv4_loopback():
    assert parse_ip("127.0.0.1") == IPv4Address("127.0.0.1")

def test_parse_invalid_ip_letters():
    with pytest.raises(ValueError):
        parse_ip("invalid")
```

## Good

```python
import pytest

# Good: Clean, readable parameter matrix
@pytest.mark.parametrize("ip_str, expected", [
    ("192.168.1.1", IPv4Address("192.168.1.1")),
    ("127.0.0.1", IPv4Address("127.0.0.1")),
    ("10.0.0.1", IPv4Address("10.0.0.1")),
])
def test_parse_valid_ip(ip_str: str, expected: IPv4Address):
    assert parse_ip(ip_str) == expected

@pytest.mark.parametrize("invalid_ip", [
    "999.999.999.999",
    "invalid",
    "",
    "1.2.3",
])
def test_parse_invalid_ip(invalid_ip: str):
    with pytest.raises(ValueError, match="Invalid IP address"):
        parse_ip(invalid_ip)
```

## See Also

- [test-pytest-raises-match](test-pytest-raises-match.md) - Testing exceptions with match regex
- [test-pytest-fixtures-scope](test-pytest-fixtures-scope.md) - Pytest fixture scoping
