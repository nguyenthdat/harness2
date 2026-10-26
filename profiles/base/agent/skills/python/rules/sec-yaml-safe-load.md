# sec-yaml-safe-load

> Always use `yaml.safe_load()` instead of `yaml.load()` when parsing YAML content with PyYAML.

## Why It Matters

`yaml.load(data)` defaults to or allows full object instantiation (`!!python/object/apply`), executing arbitrary Python code embedded in untrusted YAML documents.

## Bad

```python
import yaml

# Bad: yaml.load can execute arbitrary Python constructors
def load_user_config(yaml_str: str):
    return yaml.load(yaml_str, Loader=yaml.Loader)  # Vulnerable to RCE!
```

## Good

```python
import yaml

# Good: yaml.safe_load restricts parsing to standard scalar types and maps
def load_user_config(yaml_str: str) -> dict:
    return yaml.safe_load(yaml_str)
```

## See Also

- [sec-avoid-pickle-untrusted](sec-avoid-pickle-untrusted.md) - Safe deserialization
- [sec-avoid-eval-exec](sec-avoid-eval-exec.md) - Avoiding dynamic execution
