# Apple iOS / macOS Native Application Reverse Engineering

## Title & Overview
- **Domain**: Apple iOS and macOS native applications (IPA packages, Mach-O binaries).
- **Scope**: Decrypted Mach-O binaries, Objective-C runtime metadata (`objc_msgSend`), Swift 5 ABI metadata and mangling, FairPlay DRM boundary, and Apple security entitlements.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Target is an iOS IPA package (`Payload/*.app`), macOS `.app` bundle, or Mach-O binary.
- Mach-O sections contain Objective-C metadata:
  - `__DATA,__objc_classlist`, `__DATA,__objc_catlist`, `__TEXT,__objc_methname`, `__objc_protolist`
- Mach-O sections contain Swift metadata:
  - `__TEXT,__swift5_proto`, `__TEXT,__swift5_types`, `__TEXT,__swift5_reflstr`
  - Symbols prefixed with `$s` or `_$s` (Swift 5 mangling).
- Mach-O load command `LC_ENCRYPTION_INFO` or `LC_ENCRYPTION_INFO_64` indicates whether binary is encrypted (`cryptid != 0`).

---

## Tooling & CLI/MCP Actions
- **Primary Decompilers & Analyzers**:
  - Headless IDA Pro MCP: Native Mach-O loading with Objective-C type parsing.
  - Ghidra / REA: `open_binary`, `open_bundle_resources` (extracts Info.plist, entitlements, assets).
- **Specialized Apple Utilities**:
  - `class-dump`: Extracts Objective-C class interfaces and header declarations.
  - `swift-demangle`: Decodes Swift 5 mangled symbol names.
  - `otool` / `llvm-objdump`: `otool -l <macho>` to inspect load commands and encryption status.
  - iOS Jailbreak / Decryption tools: `frida-ios-dump`, `dumpdecrypted`, `vphone-cli`.

---

## Key Methodologies & Workflow (Placeholder)

### 1. DRM Encryption Verification & Decryption Check
- [ ] Inspect `cryptid` using `otool -l <binary> | grep -A 4 LC_ENCRYPTION_INFO`.
- [ ] If `cryptid == 1` (FairPlay DRM active): Target cannot be statically analyzed until decrypted from memory on a research device or VM.
- [ ] If `cryptid == 0`: Proceed with static decompilation of the decrypted slice.

### 2. Objective-C Runtime Metadata Extraction
- [ ] Parse `__objc_classlist` pointers to extract class hierarchy.
- [ ] Reconstruct method selectors, return types, and parameter types from `__objc_methname` and `__objc_methtype`.
- [ ] Analyze dynamic message dispatch: Identify `objc_msgSend(receiver, selector, ...)` calls and map receiver type to the target implementation.

### 3. Swift 5 Metadata & Reflection Recovery
- [ ] Demangle Swift symbols using `swift-demangle`.
- [ ] Locate Swift Type Descriptors (`__swift5_types`) to recover structs, classes, and enums.
- [ ] Map Swift protocols and protocol witness tables (`__swift5_protos`).
- [ ] Distinguish direct Swift function calls from dynamic vtable/witness table dispatch.

### 4. Entitlements & IPC Security Architecture
- [ ] Extract embedded provisioning profiles (`embedded.mobileprovision`) and code sign entitlements.
- [ ] Audit App Sandbox entitlements: `com.apple.security.app-sandbox`, keychain sharing access groups, App Groups.
- [ ] Trace inter-process communication: XPC services, URL schemes, and Universal Links.

---

## Boundaries & Anti-Patterns
- **Do not attempt to decompile FairPlay encrypted Mach-O files**: Static analysis on an encrypted binary yields only ciphertext/pseudorandom instructions.
- **Do not ignore `objc_msgSend` selector arguments**: In Objective-C, the second parameter (`RSI` / `X1`) is the selector pointer; it reveals the called method name.
- **Do not confuse iOS Simulator x86_64/arm64 slices with native iOS device binaries**: Ensure the correct architecture slice is analyzed.
