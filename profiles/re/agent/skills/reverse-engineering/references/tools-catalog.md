# Reverse Engineering Tools Catalog & Capability Index

## Title & Overview
- **Domain**: Comprehensive tooling index, capabilities, command invocations, and selection matrix for reverse engineering across static, dynamic, and specialized targets.
- **Scope**: IDA Pro, Ghidra/REA, radare2, Binary Ninja, managed decompilers (jadx, ilspycmd), binary diffing engines, and dynamic instrumentation frameworks.

---

## Tool Selection Matrix

| Artifact / Target | Primary Tool | Secondary / Fallback | Invocation & Reference Route |
|---|---|---|---|
| **Native PE/ELF/Mach-O** | IDA Pro (official Hex-Rays MCP) | Ghidra (`rea`), radare2, Binary Ninja | [01-static-architectures/native-cpp-abi.md](01-static-architectures/native-cpp-abi.md) |
| **Rust Compiled Binary** | IDA Pro / Ghidra | `rustfilt`, `cargo-depgraph` | [01-static-architectures/native-rust.md](01-static-architectures/native-rust.md) |
| **Go Compiled Binary** | Ghidra / IDA Pro | `IDAGolangHelper`, `redress` | [01-static-architectures/native-golang.md](01-static-architectures/native-golang.md) |
| **.NET Assembly / CIL** | `ilspycmd` / `dnSpy` | `de4dot`, Ghidra | [01-static-architectures/managed-dotnet-jvm.md](01-static-architectures/managed-dotnet-jvm.md) |
| **Java / Android DEX / APK** | `jadx` | `apktool`, Smali | [01-static-architectures/managed-dotnet-jvm.md](01-static-architectures/managed-dotnet-jvm.md) |
| **Unity IL2CPP Package** | `Il2CppDumper` + IDA/Ghidra | `inspect_il2cpp_metadata` (REA) | [01-static-architectures/unity-il2cpp.md](01-static-architectures/unity-il2cpp.md) |
| **Apple iOS / macOS Mach-O** | IDA Pro, `class-dump` | `swift-demangle`, Ghidra | [01-static-architectures/mobile-ios.md](01-static-architectures/mobile-ios.md) |
| **Web JS / Electron / WASM** | `analyze_javascript_application` | `wasm2wat`, Babel AST, `asar` | [01-static-architectures/browser-js-wasm.md](01-static-architectures/browser-js-wasm.md) |
| **Embedded Firmware / IoT** | `binwalk`, `unblob` | QEMU, Ghidra | [01-static-architectures/firmware-iot.md](01-static-architectures/firmware-iot.md) |
| **Instruction Debugger** | GDB (pwndbg/gef), LLDB, WinDbg | x64dbg | [02-dynamic-instrumentation/debugger-workflows.md](02-dynamic-instrumentation/debugger-workflows.md) |
| **Dynamic Instrumentation** | Frida (`frida-tools`) | `frida-trace`, QEMU | [02-dynamic-instrumentation/frida-hooking.md](02-dynamic-instrumentation/frida-hooking.md) |
| **Process Unpacking / Dump** | `dump_memory.py`, Scylla | `procdump`, PE-sieve | [02-dynamic-instrumentation/unpacking-memory-dump.md](02-dynamic-instrumentation/unpacking-memory-dump.md) |
| **Network Traffic Proxy** | `mitmproxy` / `mitmdump` | `tshark`, Wireshark | [02-dynamic-instrumentation/network-traffic-proxy.md](02-dynamic-instrumentation/network-traffic-proxy.md) |
| **Binary Diffing & Patches** | BinDiff | Ghidra BSim, Diaphora | [03-objectives/vuln-research-patch.md](03-objectives/vuln-research-patch.md) |
| **Protocol Recovery** | `tshark`, `pbtk` | Wireshark, IDA Pro | [03-objectives/protocol-recovery.md](03-objectives/protocol-recovery.md) |
| **Algorithm / Crypto RE** | `findcrypt`, Python `cryptography` | CyberChef, Ghidra FindCrypt | [03-objectives/algorithm-recovery.md](03-objectives/algorithm-recovery.md) |
| **Schema JSON & Evidence** | `elf_triage.py`, `check_deliverables.py` | Headless IDA Pro / Ghidra | [03-objectives/static-artifact-contract.md](03-objectives/static-artifact-contract.md) |

---

## Tool Capabilities & Invocation Reference

### 1. Hex-Rays IDA Pro (Headless MCP)
- **Use Case**: Primary decompilation for x86, x64, ARM, ARM64, MIPS; FLIRT signatures; struct recovery.
- **Workflow**: Connect via MCP, open binary, decompile target functions, close database upon completion.
- **Rule**: Do not pass `.idb` or `.i64` as input; pass target binary path.

### 2. Ghidra & REA Tools (`rea-agents`)
- **Use Case**: Multi-architecture decompilation, target-free format inspection, embedded format extraction.
- **MCP Tools**: `open_binary`, `inspect_pe_imports`, `inspect_elf_notes`, `inspect_go_binary`, `inspect_rust_binary`, `inspect_il2cpp_metadata`.
- **CLI Tools**: `rea analyze-javascript-application <path> --json`.

### 3. JADX (Java / Android Decompiler)
- **Use Case**: Decompiling Dalvik bytecode (`.dex`), APK, AAB, and JAR files directly to readable Java source.
- **CLI Command**: `jadx --deobf -d <output_dir> <sample.apk>`

### 4. ILSpy / dnSpy (.NET Decompiler)
- **Use Case**: Decompiling CIL assemblies to C# source code, recovering WinForms/WPF assets, inspecting metadata tokens.
- **CLI Command**: `ilspycmd -p -o <output_dir> <assembly.dll>`

### 5. BinDiff & Diaphora (Binary Diffing)
- **Use Case**: Comparing two binaries to extract patch deltas, identify patched vulnerabilities, and transfer symbol names.
- **CLI Command**: `bindiff --primary=<unpatched.idb> --secondary=<patched.idb> --output_dir=<out>`

---

## Boundaries & Anti-Patterns
- **Do not guess tool capabilities**: Consult this catalog before invoking external CLIs.
- **Do not install duplicate tools**: Check system paths and VM environments before triggering package installations.
- **Do not open large binaries in interactive GUI tools**: Use headless MCP or CLI options for bounded automated reversing.
