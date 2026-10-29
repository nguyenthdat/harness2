# Managed .NET Assembly & NativeAOT Reverse Engineering

Actionable guidance for reverse engineering .NET managed assemblies (CIL bytecode), ReadyToRun (R2R) pre-compiled images, Xamarin/MAUI packages, and NativeAOT executables.

---

## 1. PE / CLR Architecture & Metadata Streams

### CLR 2.0 Header (`IMAGE_COR20_HEADER`)
In PE headers, Data Directory index 14 (`IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR`) points to the CLR header:
```c
struct IMAGE_COR20_HEADER {
    uint32_t cb;                        // Size of structure
    uint16_t MajorRuntimeVersion;       // Typically 2
    uint16_t MinorRuntimeVersion;       // Typically 5
    IMAGE_DATA_DIRECTORY MetaData;      // RVA and size of metadata root
    uint32_t Flags;                     // COMIMAGE_FLAGS (ILONLY, 32BITREQUIRED, etc.)
    uint32_t EntryPointToken;           // MethodDef token or File token
    IMAGE_DATA_DIRECTORY Resources;     // Managed resources
    IMAGE_DATA_DIRECTORY StrongNameSignature;
    ...
};
```

### Metadata Streams
Follow `MetaData.VirtualAddress` to find the `BSJB` signature (`0x42534A42`), indicating the metadata root. The root declares metadata streams:
- **`#~` (Compressed Metadata Tables)**: Tables for modules, type refs, type defs, method defs, param, interface impls, member refs, etc.
- **`#-` (Uncompressed Metadata Tables)**: Rare, used in older or un-optimized assemblies.
- **`#Strings`**: UTF-8 string heap containing identifier names.
- **`#US` (User Strings)**: UTF-16LE string heap containing literal strings used in code (`ldstr` instruction).
- **`#GUID`**: 128-bit GUIDs (e.g., MVID - Module Version ID).
- **`#Blob`**: Raw binary signatures, default parameter values, and custom attribute payloads.

### Metadata Tokens
A 4-byte token has the format `0xTTNNNNNN`:
- `TT`: Table index (Type).
- `NNNNNN`: 1-based Row index (Record number).

| Table | Name | Description |
|---|---|---|
| `0x01` | `TypeRef` | Reference to type defined in another assembly |
| `0x02` | `TypeDef` | Type defined in current assembly |
| `0x04` | `FieldDef` | Field defined in current assembly |
| `0x06` | `MethodDef`| Method definition with RVA to CIL bytecode |
| `0x08` | `Param` | Parameter definition |
| `0x0A` | `MemberRef`| Reference to method/field in external type |
| `0x1B` | `TypeSpec` | Generic type specification instantiation |
| `0x70` | `UserString`| Offset into `#US` string heap |

---

## 2. Decompilation & Deobfuscation Tooling

### `ilspycmd` (Cross-Platform CLI Decompiler)
Decompile any .NET DLL/EXE directly into formatted C# source:
```bash
# Decompile whole assembly into C# files in a directory
ilspycmd -p -o /tmp/decompiled_src target.dll
# Decompile specific type
ilspycmd -t MyNamespace.SecretManager target.dll
```

### `de4dot`
- Used to unpack and deobfuscate protected assemblies (ConfuserEx, .NET Reactor, Agile.NET, SmartAssembly, Babel).
- Renames obfuscated symbols (`Class0`, `method_0`), decrypts strings, and cleans invalid CIL control flow:
  ```bash
  de4dot target_obfuscated.dll -o target_cleaned.dll
  ```

### REA MCP: `inspect_managed_artifact`
Target-free inspection of managed PE/CLI files:
- Inspects metadata headers, flags, assembly definitions, type hierarchies, and method tokens without executing the assembly.
- Reads resources without triggering runtime initialization.

---

## 3. ReadyToRun (R2R) vs NativeAOT

### ReadyToRun (R2R)
- **Concept**: Ahead-Of-Time (AOT) compiled native code combined with standard CIL bytecode to accelerate startup.
- **Inspection**:
  - The PE contains standard metadata tables (`#~`) and CIL bytecodes.
  - The CLR header includes a ReadyToRun header pointing to pre-compiled native machine code routines in `.text`.
  - If native analysis is difficult, decompilers (ILSpy/dnSpy) can still decompile the original CIL bytecode cleanly!

### NativeAOT (Ahead-Of-Time Compiled Native Executable)
- **Concept**: Compiles C# directly to native machine code (x64/ARM64) linked with a minimal, stripped CoreRT/Native runtime. No CIL bytecode is preserved.
- **Signatures**:
  - PE or ELF file with standard native sections (`.text`, `.rdata`, `.data`).
  - No `#~` metadata stream.
  - Symbols prefixed with `rhp` (Runtime Helper Procedures) such as `RhpNewFast`, `RhpAssignRef`, `RhpStelemRef`, `RhpByRefAssign`.
- **Reverse Engineering Strategy**:
  1. Treat as a standard native C++ binary (open in IDA Pro or Ghidra).
  2. Locate GC allocation calls (`RhpNewFast`) to identify class construction.
  3. Look for serialized MethodTable and TypeDescriptor structures in `.rdata`.

---

## 4. Xamarin & MAUI Applications (Mobile .NET)

Xamarin and .NET MAUI compile application logic into .NET DLLs bundled inside the Android APK or iOS IPA.

### Android Assembly Locations
- Older Xamarin: Assemblies in APK under `assemblies/*.dll`.
- Newer Xamarin / MAUI: Compressed single-blob container:
  - `assemblies/assemblies.blob`
  - `assemblies/assemblies.manifest`
- Compressed assemblies may begin with `Xaba` magic bytes (LZ4 compressed payload).

### Extraction & Decompression
```bash
# Decompress Xaba payload using Python
python3 -c "import lz4.block, sys; data = open(sys.argv[1],'rb').read(); open(sys.argv[2],'wb').write(lz4.block.decompress(data[12:]))" input.dll.lz4 output.dll
```
Once extracted, all `.dll` assemblies can be decompiled with `ilspycmd`.
