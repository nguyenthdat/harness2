# Unity IL2CPP Reverse Engineering

Actionable guidance for reverse engineering Unity games and applications built with the IL2CPP (Intermediate Language To C++) toolchain.

---

## 1. IL2CPP Architecture & Artifact Pairing

Unity's IL2CPP ahead-of-time compiler translates C# CIL bytecode into C++ source code, which is then compiled into a native machine code shared library.

### Key Artifacts
Reverse engineering IL2CPP requires two paired components:
1. **The Native Binary**:
   - Windows: `GameAssembly.dll`.
   - Android: `libil2cpp.so` (located in `lib/<arch>/`).
   - iOS: `UnityFramework` (Mach-O binary inside `Frameworks/`).
2. **Metadata File**:
   - `global-metadata.dat` (located in `Data/Managed/Metadata/` or `assets/bin/Data/Managed/Metadata/`).

### `global-metadata.dat` Header & Magic
- **Magic Bytes**: `0xFAB11BAF` (Little-endian bytes: `\xAF\x1B\xB1\xFA` or `\xAF\x1E\x44\xFA`).
- **Supported Versions**:
  - v24: Unity 2019.1 - 2019.4
  - v27: Unity 2020.1 - 2020.3
  - v29: Unity 2021.1 - 2021.3
  - v31: Unity 2022.1+
  - v39: Modern Unity releases
- **Header Structure**:
  Contains offsets and lengths for string literals, type definitions, method definitions, field definitions, properties, events, and parameter tables.

---

## 2. REA MCP: `inspect_il2cpp_metadata`

Target-free static analysis of `global-metadata.dat` without opening a disassembler or running external tools:
```json
{
  "path": "/path/to/global-metadata.dat",
  "detail": "summary"
}
```

Follow up using `inspect_analysis_view` with the returned `parent_evidence_id`:
- Query specific types:
  ```json
  {
    "evidence_id": "<parent_evidence_id>",
    "view": {
      "collection": "types",
      "names": ["PlayerController", "GameManager", "EncryptionUtils"]
    }
  }
  ```
- Query method signatures or parameters:
  ```json
  {
    "evidence_id": "<parent_evidence_id>",
    "view": {
      "collection": "methods",
      "fields": ["name", "return_type", "parameter_count"]
    }
  }
  ```
- Query embedded string literals:
  ```json
  {
    "evidence_id": "<parent_evidence_id>",
    "view": {
      "collection": "string_literals"
    }
  }
  ```

---

## 3. Il2CppDumper Workflow & Symbol Reconstruction

When analyzing the native binary (`libil2cpp.so` or `GameAssembly.dll`) in IDA Pro or Ghidra, function names and types are stripped. `Il2CppDumper` correlates the native binary and `global-metadata.dat` to restore symbols.

### Operation
1. **CLI Execution**:
   ```bash
   Il2CppDumper <executable_file> <global-metadata.dat> <output_dir>
   ```
2. **Generated Files**:
   - `dump.cs`: Human-readable C# pseudo-code containing class declarations, field offsets (`// Offset: 0x28`), and method RVAs (`// RVA: 0x1A2B3C`).
   - `script.json`: Machine-readable mapping containing method names, addresses, and type signatures.
   - `ida.py` / `ghidra.py`: Automated scripts to import symbols, method signatures, and field structures directly into IDA or Ghidra.

---

## 4. IL2CPP Native Memory Structures

Understanding native IL2CPP structures enables manual decompilation and memory inspection in IDA/Ghidra/Frida:

### Object Layout (`Il2CppObject`)
Every managed object instance on the heap starts with an 8-byte pointer to its class metadata:
```c
struct Il2CppObject {
    struct Il2CppClass* klass;    // Pointer to class type metadata
    struct MonitorData* monitor;  // Synchronization/locking monitor
};
```

### Class Metadata (`Il2CppClass`)
```c
struct Il2CppClass {
    void*               image;          // Il2CppImage*
    void*               gc_desc;
    const char*         name;           // Name of class (e.g., "Player")
    const char*         namespaze;      // Namespace (e.g., "Game.Core")
    struct Il2CppType   byval_arg;
    struct Il2CppType   this_arg;
    struct Il2CppClass* element_class;
    struct Il2CppClass* parent;         // Superclass
    struct MethodInfo** methods;        // Array of MethodInfo pointers
    struct FieldInfo*   fields;         // Array of FieldInfo structs
    uint32_t            instance_size;  // Size of object on heap
    ...
};
```

### Method Calling Convention
IL2CPP compiled native functions pass `this` as the first argument, followed by method arguments, and frequently append a trailing `MethodInfo* method` argument:
```c
// C# signature: public int CalculateDamage(int baseDmg, float multiplier);
// IL2CPP Native signature:
int32_t Player__CalculateDamage(Player* this, int32_t baseDmg, float32_t multiplier, MethodInfo* method);
```

---

## 5. Metadata Boundaries & Constraints

### Supported Scope:
- Static analysis covers valid `global-metadata.dat` files with supported version headers (v24, v27, v29, v31, v39) and intact magic `0xFAB11BAF`.
- Analysis is conducted statically using `inspect_il2cpp_metadata` or `Il2CppDumper`.

### Unsupported & Encrypted Metadata:
- If `global-metadata.dat` lacks the valid magic bytes (`\xAF\x1B\xB1\xFA` or `\xAF\x1E\x44\xFA`) or has custom encrypted headers, it is classified as unsupported.
- Do not attempt runtime hooking, memory dumping, or anti-cheat bypasses. Record the corrupted or encrypted magic as a bounded negative finding.
