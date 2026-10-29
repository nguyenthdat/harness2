# iOS Application & Mach-O Reverse Engineering

Actionable reference for reverse engineering iOS IPAs, decrypted Mach-O binaries, Objective-C runtime metadata, Swift 5 ABI, entitlements, and dynamic instrumentation using rooted research VMs (`vphone-cli`).

---

## 1. IPA Structure & FairPlay DRM Decryption

An iOS application package (`.ipa`) is a standard ZIP archive.
```text
Sample.ipa (ZIP)
└── Payload/
    └── Target.app/
        ├── Target              # Mach-O universal or ARM64 executable
        ├── Info.plist          # Bundle identifier, permissions, URL schemes
        ├── embedded.mobileprovision # Code signing profile and entitlements
        ├── Assets.car          # Compiled asset catalog (images, icons)
        └── Frameworks/         # Embedded dynamic frameworks (.framework / .dylib)
```

### FairPlay DRM & `LC_ENCRYPTION_INFO`
Binaries downloaded directly from the official Apple App Store are encrypted using FairPlay DRM:
- The Mach-O load command `LC_ENCRYPTION_INFO` (32-bit) or `LC_ENCRYPTION_INFO_64` (64-bit) specifies:
  - `cryptoff`: File offset to encrypted text segment.
  - `cryptsize`: Size of encrypted region.
  - `cryptid`: Encryption flag (`1` = encrypted, `0` = decrypted).
- **Decompilation Boundary**: A binary with `cryptid == 1` cannot be decompiled statically in IDA or Ghidra. It must first be decrypted by running it on a jailbroken device or research VM and dumping the unencrypted memory region (`cryptid` set to `0`).

---

## 2. Objective-C Runtime & Class Recovery

Objective-C relies heavily on dynamic dispatch via the runtime. The Mach-O binary contains explicit class and method metadata tables.

### Metadata Sections in Mach-O:
- `__DATA,__objc_classlist`: Array of pointers to all defined classes.
- `__DATA,__objc_classrefs`: External classes referenced by this binary.
- `__TEXT,__objc_methname`: Null-terminated method name strings (selectors).
- `__TEXT,__objc_methtype`: Type encoding strings (argument and return types).
- `__DATA,__objc_const`: Read-only class structures, method lists, and ivar offsets.

### Message Dispatch: `objc_msgSend`
In disassembly, method invocations do not appear as direct calls to method addresses, but as calls to the runtime dispatcher:
```asm
; Objective-C: [target authenticateUser:username withToken:token]
mov x0, x19                 ; x0 = receiver (target instance)
adrp x1, #sel_auth          ; x1 = SEL (selector "authenticateUser:withToken:")
ldr x1, [x1, #sel_auth_off]
mov x2, x20                 ; x2 = first argument (username)
mov x3, x21                 ; x3 = second argument (token)
bl _objc_msgSend            ; call dispatcher
```
- In IDA Pro / Ghidra, configure Objective-C type propagation plugins to automatically resolve selector calls into target function references.

### Class Dumping Tools
- **`class-dump`** / **`dsymutil`**: Extracts header files (`.h`) containing all Objective-C interfaces, properties, and methods from unencrypted Mach-O binaries.

---

## 3. Swift 5+ Stable ABI & Metadata

Modern iOS applications are predominantly written in Swift.

### Swift Mangling & Demangling
- Swift 5+ symbols start with `$s` or `_$s`.
- Demangle symbols via Xcode CLI:
  ```bash
  xcrun swift-demangle '$s6Target10CryptoUtilC14decryptPayloady10Foundation4DataVAFKF'
  # Output: Target.CryptoUtil.decryptPayload(Foundation.Data) throws -> Foundation.Data
  ```

### Swift Memory & Calling Convention (ARM64)
- **`self` pointer**: Passed in register `X20`.
- **Error return (`throws`)**: The `swifterror` register is `X21`. If an exception is thrown, `X21` contains a pointer to the `Swift.Error` existential container.
- **Metadata Sections**:
  - `__TEXT,__swift5_types`: Nominal type descriptors.
  - `__TEXT,__swift5_proto`: Protocol conformance descriptors.
  - `__TEXT,__swift5_fieldmd`: Field metadata (record types, struct field names, enums).

---

## 4. Entitlements & App Sandboxing

Entitlements define the application's granted capabilities within the iOS sandbox.

### Extraction
1. Extract embedded entitlements from the Mach-O binary:
   ```bash
   codesign -d --entitlements :- /path/to/Target.app/Target
   ```
2. Or read from `embedded.mobileprovision`:
   ```bash
   security cms -D -i /path/to/Target.app/embedded.mobileprovision | plutil -p -
   ```
### Critical Entitlements to Audit:
- `get-task-allow`: If `true`, enables debugging via LLDB (development build).
- `com.apple.security.application-groups`: Shared container access across app extensions.
- `keychain-access-groups`: Keychain items accessible by the application.

---

## 5. Dynamic Observation & Research VM (`vphone-cli`)

Static analysis is the default. Dynamic observation is permitted only when `RULES.md` allows it (when the parent requests dynamic analysis or when bytes cannot answer the question).

For dynamic observation on Apple Silicon macOS, `vphone-cli` provisions an isolated iOS research guest:
- Used for observing unencrypted runtime memory or tracing method dispatch on a target named by the parent.
- Dynamic hooks must be strictly passive (logging arguments and observed return values). Never modify return values, alter control flow, or bypass security verifications.
- Do not build exploits or payload injectors.
