# Native Rust Reverse Engineering

## Title & Overview
- **Domain**: Compiled Rust binaries (ELF, PE, Mach-O compiled with `rustc`).
- **Scope**: Rust's fat pointer memory model, `Option`/`Result` niche optimization, standard library types, panic signatures, demangling schemes (legacy vs v0), and de-bloating compiler artifacts.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Target binary contains Rust-specific symbols or strings:
  - `rust_eh_personality`, `core::panicking::panic`, `alloc::raw_vec::RawVec`
  - Mangled symbols starting with `_R` (v0 mangling) or containing `..h[0-9a-f]{16}` (legacy mangling).
  - Paths referencing `library/std/src/` or `cargo/registry/`.
- Strings in `.rodata` lack trailing null terminators (`\x00`) and are packed contiguously.
- Functions pass pairs of register arguments for string slices (`ptr` + `len`).

---

## Tooling & CLI/MCP Actions
- **Primary Decompilers & Analyzers**:
  - Headless IDA Pro MCP: `open_binary`, `get_procedure`, `get_pseudocode`.
  - Ghidra / REA: `open_binary`, `inspect_rust_binary` (extracts dependencies and crate tree).
- **Command-Line & Demangling Utilities**:
  - `rustfilt`: Demangles both legacy and RFC 2627 v0 mangled Rust symbols.
  - `readelf -p .dep-v0 <binary>`: Inspects embedded Cargo dependency graph if preserved.
  - `auto_triage.py`: Detects Rust signature and sets initial scope.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Memory Model & Core Type Reconstruction
- [ ] Map 16-byte fat pointers (`&str`, `&[T]`): Separate pointer from explicit element count/length.
- [ ] Map Trait Objects (`&dyn Trait`): 16 bytes (`data_ptr` + `vtable_ptr`). Inspect TraitVTable for drop, size, alignment, and methods.
- [ ] Reconstruct `Vec<T>` and `String` 24-byte layout (`ptr`, `capacity`, `length`).

### 2. Niche Optimization & Enum Tag Analysis
- [ ] Identify non-zero pointer niche optimization: `Option<&T>` or `Option<Box<T>>` (null pointer represents `None`, non-null represents `Some`).
- [ ] Map discriminant byte positions: Check if discriminant tag is stored in structure padding or high unused bits.
- [ ] Reconstruct `Result<T, E>` variant branches and error handling paths.

### 3. Panic & Error Recovery
- [ ] Locate calls to `core::panicking::panic` or `core::panicking::panic_fmt`.
- [ ] Trace panic arguments back to `.rodata` string slices to extract developer assertion messages, source filenames, and line numbers.
- [ ] Use recovered panic messages to assign high-confidence names to enclosing functions.

### 4. CFG De-Bloating & Library Filtering
- [ ] Filter out inlined standard library routines (`alloc::*`, `core::*`, `std::io::*`).
- [ ] Isolate user crate boundaries from dependency and runtime runtime routines.
- [ ] Reconstruct async state machines and polling structures (`core::future::Future::poll`).

---

## Boundaries & Anti-Patterns
- **Do not treat missing null terminators as corrupted strings**: Rust strings store explicit length fields; slicing strings by null byte will truncate or concatenate distinct literals.
- **Do not decompile all inlined standard library code**: Rust aggressively inlines monomorphized generics. Focus strictly on user crate application logic.
- **Do not assume `.dep-v0` absence implies zero dependencies**: Stripped release binaries often strip the dependency section.
