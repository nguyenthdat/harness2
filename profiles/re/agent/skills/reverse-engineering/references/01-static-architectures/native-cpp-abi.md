# Native C/C++ ABI, Calling Conventions & Data Structures

## Title & Overview
- **Domain**: Native compiled binaries (C and C++ across MSVC, GCC, Clang for x86-64, ARM64, and MIPS).
- **Scope**: Memory layouts, calling conventions, virtual method tables (vtables), Run-Time Type Information (RTTI), Standard Template Library (STL) containers, and symbol demangling.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Target format is ELF, PE, or Mach-O without managed runtime headers (.NET, Go, Rust, JVM).
- Strings contain standard C++ symbols or RTTI signatures:
  - MSVC: `.?AV<ClassName>@@`, `??_7<ClassName>@@6B@`
  - GCC/Clang (Itanium ABI): `_ZTV`, `_ZTI`, `_ZTS`, `_ZN`
- Disassembly shows indirect calls via vtables (`call [rax + offset]`).
- Function signatures utilize standard register parameter passing without garbage collection or goroutine headers.

---

## Tooling & CLI/MCP Actions
- **Primary Decompilers**:
  - Headless IDA Pro MCP: `open_binary`, `get_procedure`, `get_pseudocode`, `get_type_info`.
  - Ghidra / REA: `open_binary`, `inspect_binary_layout`.
- **Command-Line & Triage Utilities**:
  - Linux / GCC / Clang: `c++filt <mangled_symbol>`, `nm -C <binary>`, `readelf -Ws <binary>`.
  - Windows / MSVC: `undname <mangled_symbol>`, `dumpbin /exports /headers <binary.exe>`.
  - Helper script: `python3 profiles/re/agent/skills/reverse-engineering/scripts/elf_triage.py <binary>`.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Calling Convention Normalization & Parameter Recovery
- [ ] Determine architecture ABI (System V AMD64 vs Microsoft x64 vs ARM64 AAPCS).
- [ ] Map first 4–6 parameters to designated registers (`RDI, RSI, RDX, RCX...` or `RCX, RDX, R8, R9`).
- [ ] Identify `this` pointer convention (`RDI` on SysV, `RCX` on MSVC, `X0` on ARM64).
- [ ] Reconstruct 32-byte shadow space in MSVC call frames.

### 2. Vtable Identification & Polymorphic Dispatch
- [ ] Scan `.rdata` / `.rodata` for arrays of code pointers.
- [ ] Reconstruct class inheritance hierarchies from single and multiple vptrs.
- [ ] Resolve virtual dispatch calls (`mov rax, [rdi]; call [rax + 0x18]`) to concrete method candidates.
- [ ] Identify multiple inheritance `this`-pointer adjustment thunks (`sub rcx, offset; jmp target`).

### 3. RTTI Type Recovery
- [ ] **MSVC**: Navigate `vtable[-1]` -> `_RTTICompleteObjectLocator` -> `pTypeDescriptor` -> demangle `.?AV` class name.
- [ ] **Itanium (GCC/Clang)**: Navigate `vtable[-1]` -> `abi::__class_type_info` -> extract `type_name` and recursively follow `base_type`.
- [ ] Propagate recovered class names and member types across the decompilation database.

### 4. STL Container Layout Recognition
- [ ] Recognize `std::string` (SSO buffer vs heap pointer, 32-byte size).
- [ ] Reconstruct `std::vector<T>` 3-pointer layouts (`start`, `finish`, `end_of_storage`).
- [ ] Map `std::unique_ptr` (8 bytes) and `std::shared_ptr` (16 bytes, control block + object pointer).

---

## Boundaries & Anti-Patterns
- **Do not treat mangled symbol names as source code**: Compilers inline methods and fold identical code sequences (ICF). Verify call graph edges.
- **Do not assume zero-terminated strings in non-C containers**: C++ STL strings store explicit length fields; reading past length causes false assumptions.
- **Do not mix MSVC and Itanium calling conventions**: Ensure target toolchain ABI is identified before assigning function argument types.
