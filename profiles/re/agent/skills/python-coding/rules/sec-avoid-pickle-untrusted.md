# sec-avoid-pickle-untrusted

> Never deserialize untrusted data with `pickle`, `marshal`, or `shelve`; use standard JSON or schema-validated data formats.

## Why It Matters

Python's `pickle` serialization format is Turing-complete during deserialization (`__reduce__`). Loading pickled data from untrusted network sources, cookies, or message queues leads directly to Remote Code Execution (RCE, CWE-502). Use structured serialization formats such as JSON, Protocol Buffers, or message packs, and validate data types and bounds on receipt.

## Bad

```python
import pickle

# Bad: Deserializing untrusted network payload allows Remote Code Execution!
def handle_network_packet(raw_bytes: bytes):
    obj = pickle.loads(raw_bytes)  # Critical Security Vulnerability (RCE)
    return obj
```

## Good

```python
import json

# Good: Standard library JSON parsing with explicit shape validation
def handle_network_packet(raw_bytes: bytes) -> dict[str, str]:
    data = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object")
    command = data.get("command")
    if type(command) is not str or not command.strip():
        raise ValueError("Invalid command field")
    return {"command": command}

# Good (when Pydantic is adopted in the project):
# from pydantic import BaseModel
# class SafeMessage(BaseModel):
#     command: str
# def handle_network_packet_pydantic(raw_bytes: bytes) -> SafeMessage:
#     return SafeMessage.model_validate_json(raw_bytes)
```

## See Also

- [sec-yaml-safe-load](sec-yaml-safe-load.md) - Safe YAML parsing
- [type-pydantic-boundaries](type-pydantic-boundaries.md) - Boundary validation with Pydantic
