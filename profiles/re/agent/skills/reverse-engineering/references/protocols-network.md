# Custom Binary Protocols & Network Stream Analysis

Actionable guidance for reverse engineering proprietary network protocols, Protocol Buffers (Protobuf), gRPC services, WebSocket framing, and offline PCAP/PCAPNG packet stream triage.

---

## 1. Proprietary Protocol Framing & Anatomy

Custom binary protocols typically encapsulate messages within a fixed-width header followed by a variable-length payload and an integrity trailer:

```text
+--------------+---------------+----------------+-----------------+-----------------------+---------------+
| Magic (2-4B) | Msg ID (2-4B) | Payload Len(4B)| Sequence (4B)   | Payload Data (N Bytes)| Checksum (2-4B|
+--------------+---------------+----------------+-----------------+-----------------------+---------------+
```

### Key Field Patterns:
- **Magic Bytes**: Static preamble (e.g., `0xDEADBEEF`, `0x5A5A`) identifying the protocol boundary in a continuous TCP stream.
- **Message Type / Command ID**: Enumerated value mapping to an internal handler or dispatcher.
- **Length Field**: Indicates whether the length counts only the payload or includes header bytes; verify endianness (Big-Endian network byte order vs Little-Endian).
- **Checksum / CRC**: CRC16, CRC32, Adler-32, or HMAC protecting against transmission errors.

---

## 2. Protocol Buffers & gRPC Schema Recovery

### Protobuf Wire Encoding
Protocol Buffers serialize structured messages as Tag-Length-Value (TLV) records using variable-length integers (varints):
- **Field Header Key**: `(field_number << 3) | wire_type`.
- **Wire Types**:
  - `0`: Varint (`int32`, `int64`, `uint32`, `bool`, `enum`).
  - `1`: 64-bit (`fixed64`, `sfixed64`, `double`).
  - `2`: Length-delimited (`string`, `bytes`, embedded messages, packed repeated fields).
  - `5`: 32-bit (`fixed32`, `sfixed32`, `float`).

### Recovering Protobuf Schemas Offline:
1. **Raw Wire Decoding without `.proto` Definition**:
   ```bash
   protoc --decode_raw < payload.bin
   ```
   Outputs field numbers, wire types, and raw values.
2. **Embedded Descriptors in Compiled Binaries**:
   - Binaries often embed the original `FileDescriptorSet` or gzip-compressed `FileDescriptorProto` descriptor strings.
   - Search binary for strings containing `.proto` filenames:
     ```bash
     strings target_binary | grep -E "\.proto$"
     ```
   - Tools like `pbtk` (Protobuf Toolkit) can scan the binary, extract the descriptor bytes, and automatically reconstruct original `.proto` source files.

### gRPC Over HTTP/2 Framing
- **HTTP/2 Headers**: `content-type: application/grpc`, `te: trailers`.
- **5-Byte Message Framing**: Every gRPC message starts with a 5-byte prefix:
  - Byte 0: `Compressed-Flag` (`0` = uncompressed, `1` = compressed with gzip/deflate/snappy).
  - Bytes 1–4: Big-endian unsigned 32-bit integer indicating message length.
- Trailing status delivered in HTTP/2 trailers (`grpc-status: 0` for OK).

---

## 3. WebSocket Frame Structure (RFC 6455)

WebSocket frames transport text or binary payloads over an established TCP connection:

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------- - - - - - - - - - - - - - - - +
```
- **Opcodes**: `0x1` (UTF-8 text), `0x2` (binary data), `0x8` (connection close), `0x9` (ping), `0xA` (pong).
- **Masking**: Client-to-server frames **must** have the `MASK` bit set (`1`) and provide a 4-byte masking key. Server-to-client frames must **not** be masked.
- **Unmasking Logic**:
  ```python
  unmasked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(masked_payload))
  ```

---

## 4. Offline PCAP Triage with `tshark` & REA MCP

### CLI Invocations with `tshark`:
```bash
# List unique TCP conversation streams
tshark -r capture.pcap -q -z conv,tcp

# Extract TLS Server Name Indication (SNI) and HTTP Host headers
tshark -r capture.pcap -Y "tls.handshake.extensions_server_name || http.host" \
  -T fields -e frame.number -e ip.src -e ip.dst -e tls.handshake.extensions_server_name -e http.host

# Follow TCP stream index 0 in ASCII
tshark -r capture.pcap -q -z follow,tcp,ascii,0

# Export raw payload bytes from specific TCP port
tshark -r capture.pcap -Y "tcp.port == 9000 && tcp.payload" -T fields -e tcp.payload > payloads.hex
```

### REA MCP Tools:
- `inspect_packet_fields`: Discovers protocol field names, types, and supported display filters.
- `inspect_packet_capture`: Filters frames with Wireshark display filters and extracts specified fields.
- `inspect_pcap_capture`: Generates address, DNS, SNI, and protocol summaries without streaming raw frames.

---

## 5. Operational Boundaries

1. **Passive Offline Analysis Only**: Analyze offline packet recordings (`.pcap`, `.pcapng`, `.saz`, `.mitm`). Do not inject packets or attack live services.
2. **Schema Reconstruction Focus**: The goal is to document message boundaries, field types, serialization mechanisms, and API contracts.
