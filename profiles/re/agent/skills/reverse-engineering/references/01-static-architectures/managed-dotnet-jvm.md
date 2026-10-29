# Managed .NET & JVM / Dalvik Reverse Engineering

## Title & Overview
- **Domain**: Managed bytecodes running on virtual machines: Microsoft .NET (CIL, CLR, CoreCLR, NativeAOT) and Java / Android Dalvik / ART (JVM class files, DEX, APK, AAB).
- **Scope**: Metadata token tables, CIL/bytecode decompilation, Smali disassembly, ProGuard/R8 deobfuscation, JNI/PInvoke native bridges, and packed/compressed assemblies.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- **.NET / CIL**:
  - PE header contains `IMAGE_COR20_HEADER` in the COM descriptor directory.
  - Presence of CLI metadata root magic `BSJB` (`0x424A534A`) and streams (`#~`, `#Strings`, `#US`, `#Blob`, `#GUID`).
  - Import of `mscoree.dll` (`_CorExeMain` or `_CorDllMain`).
  - Compressed Xamarin/Mono bundles (`XALZ` magic header).
- **JVM / Android DEX**:
  - DEX header magic `dex\n035\0` or `dex\n037\0` / `dex\n038\0`.
  - Android application packages (`.apk`, `.aab`) containing `classes.dex`, `classes2.dex`.
  - Java archives (`.jar`) containing standard JVM `.class` files (`0xCAFEBABE`).

---

## Tooling & CLI/MCP Actions
- **Primary Decompilers & Analyzers**:
  - **.NET**: `ilspycmd`, `dnSpy` (Windows GUI), `de4dot` (deobfuscation), `inspect_managed_artifact` in REA.
  - **Android / JVM**: `jadx` (CLI and GUI), `apktool` (resource & Smali disassembly), `baksmali` / `smali`.
- **Target-Free & Fast Inspection**:
  - `monodis --assembly <file.exe>`: Disassemble ECMA-335 assembly metadata.
  - `dexdump -d <classes.dex>`: Fast DEX bytecode dump.
  - `auto_triage.py`: Detects managed runtime and routes here.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Metadata Parsing & Decompilation Pass
- [ ] Parse ECMA-335 table streams (`TypeDef`, `MethodDef`, `MemberRef`, `Param`).
- [ ] Recover user string literals from the `#US` (User Strings) heap.
- [ ] Decompile bytecode back to high-level C# or Java source using `ilspycmd` or `jadx`.
- [ ] Extract embedded resource blobs (`.resources`, Android `resources.arsc`, `AndroidManifest.xml`).

### 2. Obfuscation & Protector Stripping
- [ ] Detect obfuscators: ConfuserEx, .NET Reactor, SmartAssembly, ProGuard, R8, DexGuard.
- [ ] Strip symbol renaming and control flow flattening with `de4dot` (for .NET).
- [ ] Handle dynamic string encryption: Identify static string decryption routines and emulate or trace them.

### 3. Native Bridges (P/Invoke & JNI)
- [ ] **.NET P/Invoke**: Inspect `[DllImport("native.dll")]` signatures to locate corresponding native function exports.
- [ ] **Android JNI**:
  - Static JNI: Map `Java_com_example_app_NativeClass_methodName` in companion `.so` files.
  - Dynamic JNI: Trace `JNI_OnLoad` calls to `RegisterNatives` mapping function pointers to Java methods.
- [ ] Cross-reference native code analysis with IDA Pro / Ghidra for the native library.

### 4. .NET NativeAOT & Ahead-of-Time Compilation
- [ ] Identify NativeAOT binaries: Native PE/ELF with stripped CIL but embedded EEType structures.
- [ ] Reconstruct method addresses from NativeAOT dispatch maps and interface tables.
- [ ] Fall back to native IDA Pro / Ghidra analysis using the NativeAOT signature layout.

---

## Boundaries & Anti-Patterns
- **Do not analyze pure managed assemblies in raw native disassemblers**: Disassembling a .NET PE stub in standard IDA without managed plugins yields only the `_CorExeMain` loader stub.
- **Do not execute untrusted APKs or .NET binaries on host systems**: Decompile statically; do not run malware samples in local environments.
- **Do not confuse ProGuard identifier renaming with structural encryption**: Renamed identifiers (`a`, `b`, `c`) preserve complete control flow.
