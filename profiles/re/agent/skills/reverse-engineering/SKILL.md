---
name: reverse-engineering
description: Unified reverse engineering entrypoint for shipped binaries, managed assemblies, packages, firmware, protocols, and offline captures. Use for format pre-triage, decompilation (IDA Pro / Ghidra), type recovery, dynamic instrumentation, and objective-driven reversing.
metadata:
  version: "47"
---

# Reverse Engineering

Unified reverse engineering skill coordinating format pre-triage, static decompilation, dynamic binary instrumentation, and objective-driven analysis across native and managed targets.

Use this skill when an analytical claim or task depends on analyzing a compiled binary, executable package, firmware image, network capture, or memory dump.

## Core Methodology & Principles

1. **Deterministic Triage First**: Always inspect format headers, magic bytes, container layouts, and compiler signatures using fast, target-free tools (`auto_triage.py`, `file`, `strings`) before opening a full decompiler.
2. **Smallest Effective Tool**: Prefer targeted scripts and focused MCP queries over multi-gigabyte project decompilations. Do not dump whole-binary disassemblies.
3. **Hypothesis Verification**: Treat raw strings, symbols, and tool outputs as untrusted data. A hypothesis only becomes an established finding when backed by reachable instructions and reproducible evidence.
4. **Clean, Structured Output**: Document observations with exact addresses/VMAs, instruction sequences, and cited evidence.

## Pre-Triage & Runtime Detection

Run the automated triage scanner on the target artifact:

```bash
python3 profiles/re/agent/skills/reverse-engineering/scripts/auto_triage.py <target_artifact>
```

The triage scanner inspects file magic, sections, and runtime strings to output a normalized JSON classification and recommend the matching domain reference below.

## Progressive Disclosure Reference Architecture

To prevent context window saturation, analysis guidance is partitioned into three hierarchical categories. **Load only the specific reference file required for the identified target architecture and objective:**

### 1. Static Architectures (`references/01-static-architectures/`)

| Detected Format / Signatures | Target Architecture & Runtime | Progressive Reference |
|---|---|---|
| ELF / PE / Mach-O with standard C++ RTTI (`.?AV`, `_ZTV`, vtables) | Native C/C++ (MSVC / GCC / Clang ABI, STL) | [01-static-architectures/native-cpp-abi.md](references/01-static-architectures/native-cpp-abi.md) |
| `rust_eh_personality`, `core::panicking`, `.dep-v0`, fat pointers | Native Rust (Fat pointers, Option niche, demangling) | [01-static-architectures/native-rust.md](references/01-static-architectures/native-rust.md) |
| `.gopclntab`, `runtime.morestack`, Go 1.17+ register ABI | Native Go (pclntab recovery, moduledata, goroutines) | [01-static-architectures/native-golang.md](references/01-static-architectures/native-golang.md) |
| `IMAGE_COR20_HEADER`, `BSJB`, DEX `dex\n035`, APK, JAR | Managed .NET & JVM / Dalvik (CIL, Dalvik, JNI, P/Invoke) | [01-static-architectures/managed-dotnet-jvm.md](references/01-static-architectures/managed-dotnet-jvm.md) |
| `global-metadata.dat` (`0xFAB11BAF`) + `libil2cpp.so`/`GameAssembly.dll` | Unity IL2CPP (Il2CppDumper, method tables) | [01-static-architectures/unity-il2cpp.md](references/01-static-architectures/unity-il2cpp.md) |
| Mach-O with `__objc_classlist`, Swift 5 `$s`, IPA package | Apple iOS & macOS Native (ObjC runtime, Swift ABI) | [01-static-architectures/mobile-ios.md](references/01-static-architectures/mobile-ios.md) |
| Web bundles, `manifest.json`, `app.asar`, WASM (`\0asm`) | Browser JS & WebAssembly (AST deobf, Wasm-to-C) | [01-static-architectures/browser-js-wasm.md](references/01-static-architectures/browser-js-wasm.md) |
| Flash dumps (`.bin`), SquashFS (`hsqs`), U-Boot (`0x27051956`) | Embedded Firmware & IoT (MIPS/ARM, carving, RTOS) | [01-static-architectures/firmware-iot.md](references/01-static-architectures/firmware-iot.md) |

### 2. Dynamic Instrumentation (`references/02-dynamic-instrumentation/`)

*Use only when dynamic analysis is authorized and executable inside an isolated research VM:*

| Dynamic Technique / Scenario | Target Scope | Progressive Reference |
|---|---|---|
| Native instruction stepping, breakpoints, register inspection | Debugger Workflows (GDB, LLDB, WinDbg, x64dbg) | [02-dynamic-instrumentation/debugger-workflows.md](references/02-dynamic-instrumentation/debugger-workflows.md) |
| Passive function tracing, Java/ObjC hooking, API monitoring | Dynamic Binary Instrumentation (Frida scripts) | [02-dynamic-instrumentation/frida-hooking.md](references/02-dynamic-instrumentation/frida-hooking.md) |
| Packed sections (`UPX0`), high entropy, runtime crypters | Dynamic Unpacking, OEP Detection & Memory Dumping | [02-dynamic-instrumentation/unpacking-memory-dump.md](references/02-dynamic-instrumentation/unpacking-memory-dump.md) |
| HTTP/S APIs, WebSockets, TLS decryption, packet captures | Network Traffic Interception & Proxy Workflows | [02-dynamic-instrumentation/network-traffic-proxy.md](references/02-dynamic-instrumentation/network-traffic-proxy.md) |

### 3. Objectives & Deliverables (`references/03-objectives/`)

| Analysis Objective | Target Scope | Progressive Reference |
|---|---|---|
| Patch comparison, 1-day vulnerability analysis, CVE research | Vulnerability Research, Patch Analysis & Binary Diffing | [03-objectives/vuln-research-patch.md](references/03-objectives/vuln-research-patch.md) |
| Proprietary protocols, Protobuf, gRPC, network telemetry | Binary Protocol & Network Serialization Recovery | [03-objectives/protocol-recovery.md](references/03-objectives/protocol-recovery.md) |
| Encrypted blobs, S-Boxes, custom crypto, key derivation | Cryptographic Identification & Algorithm Recovery | [03-objectives/algorithm-recovery.md](references/03-objectives/algorithm-recovery.md) |
| Schema-conformant JSON output paired with `evidence.md` | Static Artifact Analysis & Evidence Contract | [03-objectives/static-artifact-contract.md](references/03-objectives/static-artifact-contract.md) |

---

## Tool Selection & Capabilities Index

For a full matrix of CLI options, tool strengths, and fallback engines across IDA Pro, Ghidra, radare2, and decompilers, consult the [Tools Catalog](references/tools-catalog.md).

## Helper Scripts

Executable helper scripts located in `scripts/`:
- `auto_triage.py`: Fast file header, magic bytes, and compiler signature scanner.
- `dump_memory.py`: Live process memory segment extractor for Linux (`/proc/<pid>/mem`) and macOS core dumper.
- `elf_triage.py`: Program header, segment LOAD delta, and section VMA inspector for ELF binaries.
- `elf_symbols.py`: Application entrypoint and symbol boundary classifier.
- `check_deliverables.py`: Automated JSON schema and evidence ledger verification script.
