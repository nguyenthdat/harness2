# Flutter Applications & Dart AOT Reverse Engineering

Actionable guidance for reverse engineering Flutter applications, `libapp.so`, `libflutter.so`, and Dart Ahead-Of-Time (AOT) snapshots across Android and iOS.

---

## 1. Flutter Engine Architecture & Binaries

Flutter compiles application code directly to native machine code (ARM64 or x86-64) without producing Dalvik DEX or JavaScript:

### Key Binary Components
1. **`libflutter.so`**:
   - The Flutter Engine (written in C++).
   - Bundles the Skia 2D rendering graphics library, Dart runtime VM, platform channel plumbing, and BoringSSL/cryptography routines.
2. **`libapp.so`** (Android) or `App.framework/App` (iOS):
   - The compiled application code (Dart AOT snapshot).
   - Contains all user-written widgets, state management, cryptographic routines, and API communication logic.

---

## 2. Dart AOT Snapshot Sections

`libapp.so` exports four symbol tables defining the snapshot sections:

```text
libapp.so / App.framework
├── kDartVmSnapshotData           # VM-level isolate heap objects & primitive types
├── kDartVmSnapshotInstructions   # Pre-compiled VM helper code & stubs
├── kDartIsolateSnapshotData      # App isolate heap: strings, class definitions, fields
└── kDartIsolateSnapshotInstructions # App isolate native machine code for all methods
```

### Snapshot Header & Engine Hash
- The snapshot header begins with magic bytes followed by a 32-byte snapshot hash (derived from the exact Dart SDK version and build flags).
- **Snapshot Versioning**: Dart does not guarantee snapshot compatibility across SDK versions. The snapshot header must match the engine in `libflutter.so`.
- To identify the matching Dart SDK commit:
  ```bash
  strings libflutter.so | grep -E "^[0-9a-f]{40}$"
  ```
  The 40-character hexadecimal string corresponds to the Flutter engine commit on GitHub.

---

## 3. Dart Runtime Memory Model

Understanding Dart's object tagging is critical when inspecting disassembly in IDA Pro or Ghidra:

### Tagged Pointers
Dart uses pointer tagging to distinguish immediate integers from heap pointers without allocation:
- **Small Integers (Smi)**:
  - Lowest bit is `0` (`value & 1 == 0`).
  - Stored as `value << 1`. To recover the integer value, arithmetic right-shift by 1 (`value >> 1`).
- **Heap Object Pointers**:
  - Lowest bit is `1` (`value & 1 == 1`).
  - Stored as `actual_heap_address + 1`.
  - In disassembly, heap pointer access typically subtracts `1` or uses an offset of `-1` (e.g., `ldr x0, [x1, #-1]`).

### Calling Conventions (ARM64)
Dart uses custom register allocations for internal calls:
- `X0` - `X7`: Function arguments and return values.
- `X26` / `X27`: Thread-local state pointer (`THR`) / Current isolate.
- `X28`: Heap allocation pointer (used by inline bump-pointer allocators).
- `SP`: Separate stack pointer for Dart execution.

---

## 4. Reverse Engineering Tooling & Workflows

### Static Analysis with `blutter`
`blutter` parses the `kDartIsolateSnapshotData` and `kDartIsolateSnapshotInstructions` symbols from `libapp.so` using the exact Dart SDK commit hash:
```bash
python3 blutter.py /path/to/arm64-v8a/libapp.so out_dir/ --rebuild
```
- Reconstructs class hierarchies, field types, and method RVAs.
- Produces synthetic C++ dummy headers and IDA/Ghidra symbol renaming scripts.

### Manual String & Symbol Extraction
If automated tools fail due to an unsupported Dart SDK version:
1. Extract printable strings from `kDartIsolateSnapshotData`:
   ```bash
   strings -n 6 -t x libapp.so > strings_with_offsets.txt
   ```
2. Search for sensitive endpoint URLs, cryptographic keys, or JSON field names.
3. Find code cross-references pointing to the string's offset in `kDartIsolateSnapshotInstructions`.

---

## 5. Analysis Boundaries & Verification Rules

1. **Static First**: Always perform static inspection of the Dart snapshot sections before considering runtime observation.
2. **Citing Evidence**: Do not claim application behavior or business logic from an extracted Dart string or class label alone. Verify that the method containing the reference is reachable from the application's entry routines.
3. **No Exploit / Repackaging**: Do not build patched engine libraries or generate bypass payloads. Record SSL pinning or integrity checks as observed security features.
