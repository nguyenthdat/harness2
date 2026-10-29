# Binary Protocol & Network Serialization Recovery

## Title & Overview
- **Domain**: Custom binary network protocols, serialization formats (Protocol Buffers, gRPC, MessagePack, FlatBuffers), and telemetry streams.
- **Scope**: Reverse engineering packet framing, header fields, TLV structures, state machines, deserialization routines, and Wireshark dissector generation.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Network traffic captures or client binaries utilize non-standard binary TCP/UDP communications.
- String references include `.proto` file definitions, `google.protobuf.*`, `grpc-status`, or `flatbuffers`.
- Code contains manual byte serialization loops (e.g. shifts and bitwise masks `buffer[i++] = (val >> 24) & 0xff`).

---

## Tooling & CLI/MCP Actions
- **Primary Decompilers & Analyzers**:
  - Headless IDA Pro MCP / Ghidra: Disassembly of serialization and dispatch logic.
  - Protobuf Recovery: `pbtk` (Protobuf toolkit), `protodec`.
- **Traffic Inspection & Prototyping**:
  - `tshark` / Wireshark: Network packet filtering and Wireshark Lua dissector testing.
  - `mitmproxy`: WebSocket and HTTP/2 stream inspection.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Packet Framing & Transport Boundary
- [ ] Determine framing mechanism:
  - Fixed-length headers: Magic bytes + packet type + payload length field.
  - Delimiter-based: Specific delimiter bytes separating messages.
  - Length-prefixed: Varint or fixed 32-bit big/little-endian integer at offset 0.
- [ ] Map header fields: Message ID, Sequence number, Flags, Timestamp, Checksum/CRC.

### 2. Protocol Buffers & gRPC Schema Recovery
- [ ] Locate embedded `.proto` file descriptors in binary `.rodata`: Scan for `\x08` followed by package and message names.
- [ ] Extract Protobuf descriptors using `pbtk` to generate valid `.proto` definitions.
- [ ] Map field tags, types (varint, fixed64, length-delimited), and nested sub-messages.
- [ ] Reconstruct gRPC service definitions, RPC method names, and stream types.

### 3. State Machine & Dispatch Table Mapping
- [ ] Locate main packet dispatch switch: Find switch statement or handler function table branching on packet type/opcode.
- [ ] Map each opcode to its corresponding message handler function.
- [ ] Document request-response pairings, handshake sequences, and heartbeat mechanisms.

### 4. Custom Serialization Dissector Development
- [ ] Document field byte offsets, endianness, and encoding algorithms.
- [ ] Author Wireshark Lua dissector script to parse live and captured packets automatically.
- [ ] Verify decoded protocol structures against offline PCAP captures.

---

## Boundaries & Anti-Patterns
- **Do not assume network integers are always host-endian**: Most protocols use network byte order (big-endian); verify whether conversion functions (`ntohl`, `be32toh`) are called.
- **Do not invent protocol field names without evidence**: Ground field names in string literals, log messages, or verified usage in code.
- **Do not replay packets against live third-party services**: Protocol verification must occur against local test stubs or offline captures.
