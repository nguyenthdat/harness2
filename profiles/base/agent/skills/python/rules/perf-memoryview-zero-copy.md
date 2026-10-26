# perf-memoryview-zero-copy

> Use `memoryview` and `bytearray` for zero-copy slicing and buffer manipulation of large binary data.

## Why It Matters

Standard slice operations on `bytes` (`data[100:1000]`) allocate a brand new `bytes` object and copy the payload memory. `memoryview` creates a slice descriptor pointing to the existing buffer without copying a single byte.

## Bad

```python
# Bad: Slicing 50MB bytes creates a full copy on every packet
def process_packets(payload: bytes):
    offset = 0
    while offset < len(payload):
        header = payload[offset:offset + 8]  # Copies 8 bytes
        length = int.from_bytes(header, "big")
        body = payload[offset + 8:offset + 8 + length]  # Copies 'length' bytes!
        handle(body)
        offset += 8 + length
```

## Good

```python
# Good: memoryview slices without allocating new memory buffers
def process_packets(payload: bytes):
    view = memoryview(payload)
    offset = 0
    while offset < len(view):
        header = view[offset:offset + 8]
        length = int.from_bytes(header, "big")
        body = view[offset + 8:offset + 8 + length]  # Zero-copy slice!
        handle(body)
        offset += 8 + length
```

## See Also

- [conc-shared-memory-ipc](conc-shared-memory-ipc.md) - Shared memory for interprocess communication
- [perf-generators-memory](perf-generators-memory.md) - Streaming with generators
