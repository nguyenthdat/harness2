# Unity IL2CPP Reverse Engineering

## Title & Overview
- **Domain**: Unity games and applications compiled using the IL2CPP (Intermediate Language to C++) toolchain.
- **Scope**: Extracting metadata tokens from `global-metadata.dat`, mapping method addresses in `libil2cpp.so` or `GameAssembly.dll`, reconstructing C# classes, structures, and method tables.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Shipped package contains the Unity IL2CPP pair:
  - `global-metadata.dat` (magic `0xFAB11BAF` / `0xAF1BB1FA`) located in `assets/bin/Data/Managed/Metadata/` or game data folders.
  - Native binary: `libil2cpp.so` (Android/Linux), `GameAssembly.dll` (Windows), or main Mach-O executable (iOS).
- String references include `il2cpp::vm::MetadataCache`, `il2cpp_codegen_initialize_method`.
- Export table of native binary exports `il2cpp_init`, `il2cpp_class_get_methods`.

---

## Tooling & CLI/MCP Actions
- **Primary Extraction Tools**:
  - `Il2CppDumper`: CLI tool to extract types, methods, fields, and generate IDA/Ghidra Python symbol restoration scripts.
  - REA Tool: `inspect_il2cpp_metadata` (built-in parser for `global-metadata.dat`).
  - `Cpp2IL`: Alternative decompiler generating high-level C# pseudocode from IL2CPP binaries.
- **Decompiler Integration**:
  - Run generated `ida_with_struct_py3.py` or `ghidra_with_struct.py` against the native binary to rename all methods and reconstruct structs.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Metadata & Binary Pairing Verification
- [ ] Read `global-metadata.dat` header: verify magic `0xFAB11BAF` and version integer (common: 24, 27, 29, 31).
- [ ] Check for encrypted or scrambled metadata headers (common in protected mobile games).
- [ ] Match binary target architecture (x86, x64, ARM, ARM64) and ensure symbols correspond to the extracted metadata.

### 2. Header & Type Dump Execution
- [ ] Run `Il2CppDumper <executable> <global-metadata.dat> <output_dir>`.
- [ ] Inspect generated `dump.cs`: contains all high-level class definitions, fields, properties, and method virtual address offsets.
- [ ] Inspect generated `script.json`: contains address-to-symbol mappings, string literals, and metadata usages.

### 3. Decompiler Symbol & Type Script Import
- [ ] Open native binary (`GameAssembly.dll` or `libil2cpp.so`) in IDA Pro or Ghidra.
- [ ] Execute the generated IDA/Ghidra script to restore all stripped function names and C++ struct declarations.
- [ ] Navigate directly to key game logic classes (`GameManager`, `NetworkClient`, `LicenseValidator`).

### 4. Method Dispatch & Calling Convention
- [ ] Note that all IL2CPP methods take an explicit `MethodInfo*` as their final hidden parameter.
- [ ] Virtual method calls resolve via `Il2CppClass` vtable array indices.
- [ ] Map native memory allocations to C# garbage-collected references.

---

## Boundaries & Anti-Patterns
- **Do not analyze `libil2cpp.so` without metadata restoration**: Without `global-metadata.dat`, function names are stripped to raw native pointers (`sub_123456`).
- **Do not modify `global-metadata.dat` directly**: Work with memory dumps or extracted headers.
- **Do not mistake native wrapper functions for game logic**: Most engine functions are generic stubs; focus on user assemblies (`Assembly-CSharp.dll`).
