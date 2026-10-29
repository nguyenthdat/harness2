# Dynamic Unpacking, OEP Detection & Memory Dumping

## Title & Overview
- **Domain**: Packed executables, runtime crypters, dynamic loaders, and self-modifying code (PE, ELF, Mach-O).
- **Scope**: Original Entry Point (OEP) identification, memory layout extraction, dumping unmapped/decrypted memory segments, fixing Import Address Tables (IAT), and passive memory carving.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Static analysis reveals packed sections (e.g. `UPX0`, `UPX1`, `.packer`, high entropy > 7.2 across executable sections).
- Executable imports are minimal (e.g. only `LoadLibraryA` + `GetProcAddress` or `dlopen` + `dlsym`).
- Code self-modifies or creates anonymous Read-Write-Execute (`RWX`) memory allocations at runtime.
- Static disassemblers fail to find standard function prologues or valid control flow.

---

## Tooling & CLI/MCP Actions
- **Primary Unpacking & Carving Tools**:
  - Memory Dumper Script: `python3 profiles/re/agent/skills/reverse-engineering/scripts/dump_memory.py <pid> -o <dump_dir>`.
  - Windows PE: `x64dbg` / `Scylla` (IAT reconstruction), `procdump`, PE-sieve.
  - Linux ELF: `/proc/<pid>/maps` + `/proc/<pid>/mem` reading, `gcore`.
  - macOS: `lldb` `process save-core`.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Packer Signature & Entropy Screening
- [ ] Calculate entropy per section: Identify packed payload sections.
- [ ] Match known packer signatures (UPX, ASPack, Themida, VMProtect).
- [ ] If known open-source packer (e.g. UPX): Run static unpacker first (`upx -d <target>`).
- [ ] If custom or unknown: Prepare VM environment for dynamic OEP tracing.

### 2. Original Entry Point (OEP) Detection
- [ ] **Tail Jump Pattern**: Track packer transition from stub to unpacked code (often a large jump register/memory like `jmp eax` or `popad; jmp OEP`).
- [ ] **Memory Protection Breakpoints**:
  - Set hardware execute breakpoint on `.text` section of the main binary.
  - Run target inside debugger until execution transitions from loader stub into `.text`.
- [ ] **API Call Transitions**: Set breakpoints on high-level APIs called after initialization (e.g., `GetCommandLineA`, `__libc_start_main`).

### 3. Memory Dumping at OEP
- [ ] Halt target immediately when execution reaches OEP.
- [ ] Dump running process memory regions using `dump_memory.py` or Scylla.
- [ ] Inspect dumped memory mappings for valid PE/ELF/Mach-O headers or executable shellcode blocks.

### 4. Import Address Table (IAT) Reconstruction
- [ ] Locate IAT in dumped PE memory.
- [ ] Scan for function pointers resolved via `GetProcAddress`.
- [ ] Rebuild IAT pointers and PE section headers using Scylla or manual header fixup scripts.
- [ ] Transition rebuilt binary back to static analysis (IDA Pro / Ghidra).

---

## Boundaries & Anti-Patterns
- **Do not detonate malware or unknown packers on host workstations**: Run all dynamic unpacking in disposable VMs.
- **Do not attempt to execute dumped memory slices directly**: Memory dumps are for static offline inspection in disassemblers, not for standalone execution.
- **Do not confuse Virtual Size vs Raw Size**: Ensure section headers are properly aligned when converting a memory dump back to a valid disk file.
