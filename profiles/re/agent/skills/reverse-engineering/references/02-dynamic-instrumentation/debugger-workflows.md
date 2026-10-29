# Debugger Workflows & Instruction-Level Tracing

## Title & Overview
- **Domain**: Native and managed runtime debuggers (GDB, LLDB, WinDbg, x64dbg).
- **Scope**: Controlled execution, hardware and software breakpoints, register/memory inspection, stack frame reconstruction, and anti-debugging evasion handling inside isolated virtual machines.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Static analysis is insufficient to determine runtime state, complex computed jumps, or unpack dynamic payloads.
- Authorized environment: Debugging is performed inside an isolated VM (UTM, QEMU, research sandbox).
- Need to trace dynamic register values, inspect heap allocations, or step through decryption loops at the machine code level.

---

## Tooling & CLI/MCP Actions
- **Primary Debugger Engines**:
  - **Linux ELF**: `gdb` (with `gef` or `pwndbg` extensions).
  - **macOS / iOS Mach-O**: `lldb` (CLI or debugserver).
  - **Windows PE**: `windbg` / `cdb` (command-line), `x64dbg` (GUI).
- **Automation & Scripting**:
  - GDB Python API, LLDB Python scripting, WinDbg JavaScript (`dx` / JavaScript provider).

---

## Key Methodologies & Workflow (Placeholder)

### 1. VM Isolation & Session Launch
- [ ] Ensure execution occurs inside an isolated VM snapshot (UTM disposable mode or QEMU guest).
- [ ] Disable Address Space Layout Randomization (ASLR) if deterministic reproduction is required:
  - Linux: `gdb -ex "set disable-randomization on" <target>`
- [ ] Set initial breakpoint at Entry Point or `main`.

### 2. Breakpoint Strategies & Control Flow Observation
- [ ] Hardware Breakpoints (`hbreak`): Use for observing memory access or bypassing simple software-breakpoint checks.
- [ ] Conditional Breakpoints: Log variable states and continue execution without stalling user interaction.
- [ ] Stepping Strategy: Step over (`nexti` / `p`) routine calls to avoid entering third-party libraries; step into (`stepi` / `t`) only target logic.

### 3. Memory & Register State Inspection
- [ ] Inspect calling convention arguments before call instructions (`RDI`, `RSI`, `RDX` or `RCX`, `RDX`, `R8`, `R9`).
- [ ] Dump memory buffers: `x/16gx $rsp`, `x/s <address>`, `dump binary memory <out.bin> <start> <end>`.
- [ ] Trace return values in `RAX` / `X0` immediately upon function return (`finish` / `pt`).

### 4. Anti-Debugging Detection & Evasion
- [ ] Detect standard anti-debugging flags:
  - Linux: `ptrace(PTRACE_TRACEME)`, `/proc/self/status` `TracerPid`.
  - Windows: `BeingDebugged` flag in PEB, `CheckRemoteDebuggerPresent()`, `NtGlobalFlag`, hardware breakpoint register checks (`DR0-DR7`).
- [ ] Apply non-destructive debugger patches or environment flags to maintain passive observation.

---

## Boundaries & Anti-Patterns
- **Do not run untrusted or malicious targets on the host operating system**: All debugger sessions must be contained within isolated VMs.
- **Do not modify control flow to exploit or alter software behavior**: Observe return values and memory passively; do not inject exploit payloads.
- **Do not step blindly through complex standard library functions**: Set targeted breakpoints on caller and callee boundaries.
