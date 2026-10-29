# React Native Applications & Hermes Bytecode

Actionable reference for reverse engineering React Native applications, Metro JavaScript bundles, Hermes bytecode (`.hbc`), and native module bridges across Android and iOS.

---

## 1. React Native Application Anatomy

React Native applications bundle JavaScript or bytecode alongside a native execution engine:

### Application Bundle Locations:
- **Android APK**: `assets/index.android.bundle`.
- **iOS IPA**: `Payload/<App>.app/main.jsbundle`.

### Framework Architecture:
1. **JavaScript Runtime**: Runs UI logic, state management, and business workflows.
2. **Native Modules (Bridge / TurboModules)**: Expose platform-specific APIs (camera, storage, biometrics, cryptography) to JavaScript.
3. **Hermes Engine (`libhermes.so`)**: Meta's lightweight, ahead-of-time bytecode interpreter optimized for React Native.

---

## 2. Hermes Bytecode (`.hbc`) Analysis

Modern React Native applications compile JavaScript into Hermes bytecode rather than shipping raw text.

### Magic Signatures & Header
Check the first 8 bytes of `index.android.bundle`:
- **Magic**: `0x1F 0x04 0x8C 0x1F` (Little-endian: `\x1F\x8C\x04\x1F`) or Hermes format `\xc6\x1f\xbc\x03`.
- **Version Byte**: Follows immediately after magic bytes. Specifies Hermes Bytecode version (e.g., version 74, 84, 90).

### Decompilation & Disassembly Tools:
- **`hermes-engine` CLI**:
  ```bash
  # Disassemble Hermes bytecode into human-readable opcode stream
  hermes -dump-bytecode index.android.bundle -out disassembly.txt
  ```
- **`hbctool`**: Disassembles and unpacks `.hbc` files into instruction dumps and string tables.
- **`hermes-dec`**: Decompiler that lifts Hermes bytecode instructions back into pseudo-JavaScript.

### Bytecode Structure:
- **String Table**: All string literals (URLs, API keys, JSON keys, method names) are stored in a contiguous pool at the beginning of the file.
- **Function Headers**: Define parameter count, register count, and instruction bytecode offsets.
- **Opcode Syntax**: Register-based machine:
  - `LoadConstString r0, 12`: Load string table index 12 into register `r0`.
  - `Call2 r1, r2, r0`: Call function in `r2` with argument `r0`, store result in `r1`.
  - `GetById r0, r1, 3, "data"`: Access property `"data"` on object in `r1`.

---

## 3. Plain JavaScript Bundle Triage (Metro Bundler)

If Hermes is not used, the bundle is plain minified JavaScript packaged by Metro.

### Metro Module Wrapper:
Metro wraps each module in a standard closure:
```javascript
__d(function(global, require, importDefault, importAll, module, exports, _dependencyMap) {
    // Module code
    var ApiClient = require(_dependencyMap[0]);
    exports.login = function(username, password) { ... };
}, 124, [105]); // Module ID 124, dependencies: [105]
```
- The second argument (`124`) is the numeric **Module ID**.
- The third argument (`[105]`) maps dependency indices to other Module IDs.
- Search for sensitive strings, locate the enclosing `__d(...)` wrapper, and trace cross-module calls via `_dependencyMap`.

---

## 4. Native Bridge & TurboModules

Critical business logic often delegates to native code via the bridge:

### Android Bridge (Java / Kotlin):
- Classes extending `ReactContextBaseJavaModule`.
- Methods exposed to JavaScript are annotated with `@ReactMethod`:
  ```java
  public class EncryptionModule extends ReactContextBaseJavaModule {
      @ReactMethod
      public void encryptData(String data, Promise promise) {
          // Native implementation
      }
  }
  ```
- Decompile with `jadx` and cross-reference the module name returned by `getName()`.

### Modern TurboModules (C++ / JSI - JavaScript Interface):
- In the React Native New Architecture, JavaScript calls C++ directly via JSI host objects without JSON serialization over the bridge.
- Search for native libraries (`libappmodules.so`) in `lib/<arch>/` and examine exported C++ JSI bindings in IDA Pro or Ghidra.

---

## 5. Verification & Boundary Rules

1. **Labels vs Behavior**: Do not claim runtime behavior from component labels, JSX prop names, or state variable names alone.
2. **Verify Reachability**: Trace the call path from user action or component mount to confirm whether a sensitive native module or API call is actually invoked.
3. **No Exploits / Payloads**: Static analysis focuses on identifying exported endpoints, cryptographic implementations, and exposed secrets.
