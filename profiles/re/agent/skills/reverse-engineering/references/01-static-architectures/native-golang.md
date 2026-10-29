# Native Go Reverse Engineering

## Title & Overview
- **Domain**: Go binaries (compiled with official `gc` toolchain for Linux, macOS, or Windows).
- **Scope**: Reconstructing function boundaries via `.gopclntab`, handling Go 1.17+ register-based ABI, demangling Go types and interfaces, and parsing `moduledata`.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Target binary contains Go-specific sections, symbols, or strings:
  - Sections: `.gopclntab`, `.gosymtab`
  - Strings / Symbols: `runtime.morestack`, `runtime.newobject`, `Go build ID:`
  - Function names containing `/` or `.` (e.g., `main.main`, `github.com/gin-gonic/gin.*`).
- Function prologues check stack bounds: `cmp rsp, qword ptr [r14+10h]; jbe runtime.morestack`.
- Register ABI (Go 1.17+): Function arguments passed in `RAX, RBX, RCX, RDI, RSI, R8, R9, R10, R11` (x86-64) or `R0-R15` (ARM64).

---

## Tooling & CLI/MCP Actions
- **Primary Decompilers & Analyzers**:
  - Headless IDA Pro MCP: `open_binary`, `get_procedure`, `get_pseudocode`.
  - Ghidra / REA: `open_binary`, `inspect_go_binary` (extracts Go compiler version, build flags, packages, and pclntab).
- **Specialized Go Reversing Utilities**:
  - `go-re-scripts` / `IDAGolangHelper`: Renames functions and reconstructs types from pclntab.
  - `redress`: Compiles detailed struct and package information from stripped Go binaries.
  - Helper script: `auto_triage.py` for immediate Go detection.

---

## Key Methodologies & Workflow (Placeholder)

### 1. `pclntab` & Symbol Recovery
- [ ] Locate `.gopclntab` magic bytes (`0xFFFFFFFB` / `0xFFFFFFFA` / `0xFFFFFFF0`).
- [ ] Parse `runtime.moduledata` structure to find function table pointers.
- [ ] Recover stripped function names, entry VMAs, and source file line tables.
- [ ] Rename unknown functions in decompiler database before analyzing control flow.

### 2. Stack Growth & Calling Convention Analysis
- [ ] Identify stack split prologues (`runtime.morestack`) and filter out runtime boilerplates.
- [ ] Distinguish Go stack-based ABI (Go <= 1.16) from register-based ABI (Go >= 1.17).
- [ ] Reconstruct multiple return values (Go functions frequently return pairs like `(result, err)` in registers).

### 3. Go Type System & Interface Disassembly
- [ ] Parse `runtime._type` structures (kind, size, hash, flags).
- [ ] Reconstruct Go strings: 16-byte structure `[ ptr: 8 bytes ][ len: 8 bytes ]`.
- [ ] Reconstruct Go slices: 24-byte structure `[ ptr: 8 bytes ][ len: 8 bytes ][ cap: 8 bytes ]`.
- [ ] Map interfaces: Empty interface `eface` (`_type` + `data`) vs non-empty interface `iface` (`itab` + `data`).

### 4. Goroutines, Channels & Concurrency Patterns
- [ ] Trace calls to `runtime.newproc` to identify spawned goroutine entrypoints.
- [ ] Identify channel synchronization primitives (`runtime.chansend1`, `runtime.chanrecv1`).
- [ ] Map HTTP/RPC handlers registered in `net/http` multiplexers or gRPC servers.

---

## Boundaries & Anti-Patterns
- **Do not analyze Go binaries as standard C ABI**: Assuming System V AMD64 calling conventions will misattribute Go register arguments and return values.
- **Do not mistake runtime memory allocators for application logic**: Operations like `runtime.makeslice` or `runtime.growslice` are runtime support code.
- **Do not attempt to decompile without pclntab recovery**: A stripped Go binary has thousands of unnamed functions; recovering pclntab first saves hours of analysis.
