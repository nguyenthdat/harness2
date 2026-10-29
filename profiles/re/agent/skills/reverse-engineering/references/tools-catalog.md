# Reverse Engineering Tools Catalog & Routing

A comprehensive catalog and decision guide for reverse engineering tools, frameworks, and command-line interfaces across static and dynamic analysis workflows.

## Tool Selection Matrix

| Artifact / Target | Primary Tool | Secondary / Fallback | MCP Tool / Route |
|---|---|---|---|
| Native Executable (PE/ELF/Mach-O) | IDA Pro (official Hex-Rays MCP) | Ghidra (`rea`), radare2, Binary Ninja | IDA MCP for decompilation; `open_binary` in `rea` |
| Managed .NET Assembly | `ilspycmd` / `dnSpy` | `de4dot`, Ghidra | `inspect_managed_artifact` in `rea` |
| Android DEX / APK / AAB | `jadx` | `apktool`, Smali | `inspect_android_package`, `inspect_apk_signature` |
| iOS Mach-O / IPA | IDA Pro, `class-dump` | `ipsw`, Ghidra | `open_bundle_resources`, `open_binary` |
| WebAssembly (WASM) | `wasm2wat` (WABT) | Ghidra WASM plugin | `inspect_wasm_artifact` |
| JavaScript / Electron / ASAR | `analyze_javascript_application` | `asar` CLI, Babel AST parser | `analyze_javascript_application`, `inspect_electron_fuses` |
| Unity IL2CPP | `inspect_il2cpp_metadata` (REA) | Il2CppDumper + IDA/Ghidra | `inspect_il2cpp_metadata`, `open_binary` |
| Firmware Image / Flash Dump | `binwalk`, `unblob` | QEMU, Ghidra | `inspect_firmware_regions`, `extract_firmware` |
| Network Captures (PCAP/PCAPNG) | `tshark` (Wireshark CLI) | `mitmproxy` (HTTP/WS) | `inspect_packet_capture`, `inspect_pcap_capture` |
| Dynamic Instrumentation | Frida (`frida-tools`) | GDB, LLDB, x64dbg | Dynamic observation; VM/emulator hook |

---

## Tool Capabilities & Invocation

### 1. IDA Pro (Headless & MCP)
- **Strengths**: Gold standard decompilation for x86, x64, ARM, ARM64, MIPS; FLIRT signature matching; type reconstruction; IDAPython automation.
- **MCP Usage**:
  - Headless IDA MCP connects to an IDA service.
  - Queries procedures, pseudocode, types, cross-references (`xrefs`), and structural layouts.
  - Do not pass `.idb` or `.i64` as input when `open_binary` is used. Close databases on task completion.

### 2. Ghidra / REA (`rea-agents`)
- **Strengths**: Multi-architecture support, extensive format parsing (PE, ELF, Mach-O, COFF, Raw Binary), built-in headless analysis, target-free format inspectors.
- **REA MCP Tools**:
  - `open_binary` / `close_binary`: Native binary lifecycle.
  - `inspect_pe_imports`, `inspect_pe_load_config`, `inspect_pe_certificates`, `inspect_pe_resources`: Windows PE introspection.
  - `inspect_elf_notes`, `inspect_binary_layout`: Linux ELF triage.
  - `inspect_go_binary`, `inspect_rust_binary`: Embedded compiler and dependency extraction.
  - `inspect_il2cpp_metadata`: Unity metadata parser for `global-metadata.dat`.
- **CLI Fallback**:
  ```bash
  rea analyze-javascript-application /path/to/app --json
  rea inspect-evidence-bundle /path/to/bundle.json --detail summary
  ```

### 3. radare2 (`r2`) & Cutter
- **Strengths**: Fast lightweight CLI binary analysis, hex editing, scriptable via r2pipe, headless disassembly and emulation via ESIL (Evaluable Strings Intermediate Language).
- **CLI Commands**:
  ```bash
  # Analyze all symbols, entry points, calls, and display function list
  r2 -A -qc "afl" target.bin
  # Disassemble function at main
  r2 -A -qc "pdf @sym.main" target.bin
  # Search for strings
  r2 -qc "iz" target.bin
  ```

### 4. Binary Ninja
- **Strengths**: High-performance BNIL (Binary Ninja Intermediate Language) multi-stage lifting (Low Level IL, Medium Level IL, High Level IL), clean API, robust type propagation.
- **Use Case**: Advanced automated dataflow analysis, decompilation when IDA/Ghidra heuristics produce convoluted expressions.

### 5. JADX
- **Strengths**: Best-in-class Java decompiler for Android DEX, APK, AAB, and Java `.class`/`.jar` archives.
- **CLI Invocations**:
  ```bash
  # Decompile APK to output directory without saving GUI layout
  jadx -d /tmp/decompiled_apk sample.apk --no-imports --show-bad-code
  # Decompile specific class
  jadx -d /tmp/decompiled_apk -include-pkg com.example.target sample.apk
  ```

### 6. Apktool
- **Strengths**: Disassembles DEX into Smali bytecode; decodes binary XML (`AndroidManifest.xml`) and resources (`res/values/strings.xml`).
- **CLI Invocation**:
  ```bash
  apktool d sample.apk -o /tmp/apktool_out --no-src
  # Disassemble with Smali source
  apktool d sample.apk -o /tmp/apktool_out
  ```

### 7. mitmproxy (`mitmdump` / `mitmweb`)
- **Strengths**: Interception and inspection of HTTP/1.1, HTTP/2, and WebSocket traffic; SSL/TLS decryption via dynamic CA generation.
- **CLI Usage**:
  ```bash
  # Headless traffic dump to file with SSL decryption
  mitmdump -p 8080 -w traffic.mitm
  # Filter specific host
  mitmdump -r traffic.mitm "~u example.com" -s export_script.py
  ```

### 8. tshark (Wireshark CLI)
- **Strengths**: Dissects hundreds of protocols from raw PCAP/PCAPNG files; extract fields, streams, and TLS handshake SNIs.
- **CLI Commands**:
  ```bash
  # Extract DNS queries and HTTP hosts
  tshark -r capture.pcap -Y "dns || http" -T fields -e ip.src -e dns.qry.name -e http.host
  # Follow TCP stream index 0 in ASCII
  tshark -r capture.pcap -q -z follow,tcp,ascii,0
  ```

### 9. Frida
- **Strengths**: Dynamic binary instrumentation via V8 JavaScript runtime injected into target process on Linux, Windows, macOS, Android, and iOS.
- **CLI & Script Patterns**:
  ```bash
  # Enumerate loaded modules
  frida -p <PID> -E "Process.enumerateModules()"
  # Trace specific native symbol
  frida-trace -p <PID> -i "open*" -i "read*"
  ```

---

## Operating Boundaries & Rules

1. **Read-Only / Static First**: Always default to static triage using `file`, `strings`, `objdump`, or REA target-free inspectors before opening a full decompiler.
2. **Never Execute Malware**: Do not launch suspicious executables, trigger installation, or connect to extracted C2 endpoints.
3. **No Unapproved Tool Installation**: Use tools already provisioned or available via `skill://tool-setup` allowlist.
4. **Distinguish Claims**: A tool listing an import or string is an observation, not proof of runtime execution. Always verify reachability.
