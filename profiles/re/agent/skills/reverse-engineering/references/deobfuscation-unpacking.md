# Deobfuscation, Devirtualization & Unpacking

Actionable guidance for unpacking protected executables, de-flattening obfuscated control flow, recovering encrypted strings, and devirtualizing VM-protected bytecode.

---

## 1. Unpacking Protected Executables & Identifying OEP

Packers compress or encrypt the original binary and prepend an unpacking stub that executes first.

### Unpacking Execution Lifecycle:
```text
[ Packer Entry Point ]
         │
         ▼
[ Allocate RWX Memory ] (VirtualAlloc / mmap)
         │
         ▼
[ Decrypt / Decompress Payload ] (AES, RC4, LZMA, aPLib, custom XOR)
         │
         ▼
[ Resolve Import Address Table ] (LoadLibraryA / GetProcAddress loops)
         │
         ▼
[ Tail Jump to OEP ] (jmp / push OEP + ret)
         │
         ▼
[ Original Entry Point (OEP) ] (.text code execution begins)
```

### Techniques to Locate the Original Entry Point (OEP):
1. **Section Transition**:
   - Packers typically execute in dedicated sections (`UPX0`, `UPX1`, `.pack`, `.stub`).
   - The transition to an address in `.text` via an inter-section jump indicates the OEP.
2. **Stack Balance (ESP Trick)**:
   - Unpacking stubs save initial register states using `pushad` / `pusha`.
   - Before jumping to the OEP, the stub restores registers via `popad` / `popa`.
   - The instruction immediately following `popad` is usually a jump or return to the OEP (`jmp eax`, `push <oep>; ret`).
3. **Rebuilding the Dumped Image**:
   - When dumping unpacked memory at OEP, the Import Address Table (IAT) must be aligned and re-pointed to valid DLL imports using tools like Scylla or `pefile`.

---

## 2. Control Flow Flattening (CFF)

Control Flow Flattening breaks normal structured flow (loops, if-else) into basic blocks managed by an infinite switch-case loop controlled by a state variable.

### Structure of a Flattened Function:
```text
                [ Function Prologue ]
                          │
                          ▼
                  [ Init State Var ]
                          │
                          ▼
            ┌───► [ Central Dispatcher ] ◄───┐
            │     (switch on StateVar)       │
            │           │                    │
            │     ┌─────┴──────────┐         │
            │     ▼                ▼         │
            │  [ Case A ]       [ Case B ]   │
            │  (Update State)   (Update State)
            └─────┘                └─────────┘
```

### Static De-flattening Workflow:
1. **Identify the State Variable**: Look for a local stack variable or register compared against multiple integer constants in a jump table or chained `cmp`/`je` dispatcher.
2. **Identify Dispatcher Blocks**: Mark the basic block that evaluates the state variable and performs indirect dispatch.
3. **Extract State Transitions**:
   - Analyze each basic block assigned to a `case`.
   - Trace the assignment that updates the state variable (e.g., `state = 0x2A;` or `state = condition ? 0x14 : 0x3B;`).
4. **Reconstruct the Clean CFG**:
   - Replace the jump back to the central dispatcher with a direct jump (`jmp`) or conditional jump (`jcc`) to the successor block mapped to that state value.
   - Utilize symbolic execution (Triton, angr, or Miasm) to solve path constraints and automatically link case blocks to their successors.

---

## 3. String & Constant Decryption

Malware and protected binaries encrypt sensitive strings, URLs, and API names in `.rodata` or `.data` to hinder static string extraction.

### Common Decryption Patterns:
- **Stack Strings**: Constructed byte-by-byte or word-by-word into local stack variables immediately before use.
- **Dedicated Decryptor Functions**: An encrypted buffer and key are passed to a helper function before each API call:
  ```asm
  lea  rcx, [encrypted_blob]
  mov  edx, 0x24            ; length
  lea  r8, [xor_key]
  call decrypt_string
  ```

### Static Deobfuscation Strategies:
1. **Static Python Solver**: If the cipher is simple (XOR, ROT, RC4), re-implement the algorithm in a Python script to decode all referenced buffers and annotate the disassembly database with comments.
2. **Emulated Execution (Radare2 ESIL / Unicorn Engine)**:
   - Map the `.rodata` and `.data` segments into an emulator.
   - Set up the CPU registers with arguments.
   - Emulate only the decryption function instructions until return (`ret`), and read the decrypted buffer from memory.
   - *Boundary*: Do not execute the whole binary; isolate strictly the math/cryptographic basic blocks.

---

## 4. Virtual Machine-Based Obfuscation (Devirtualization)

VM protectors (VMProtect, CodeVirtualizer, custom DSLs) compile native machine code into custom bytecode executed by an embedded software interpreter.

### Architecture of an Embedded VM:
1. **Virtual Program Counter (VPC)**: A register (e.g., `ESI` or `R12`) pointing into the custom bytecode buffer.
2. **Virtual Stack**: Stack pointer used by the interpreter to store intermediate computation results.
3. **Central Dispatcher**:
   - Reads the next opcode from `*VPC++`.
   - Fetches handler function pointer from a static handler table: `handler = handler_table[opcode]`.
   - Jumps to the handler: `jmp handler`.
4. **Opcode Handlers**: Small native basic blocks implementing specific operations (`VM_ADD`, `VM_SUB`, `VM_LOAD`, `VM_STORE`, `VM_JMP`). Each handler ends by returning to the central dispatcher or fetching the next opcode directly (threaded code).

### Devirtualization Methodology:
1. Locate the entry stub where native execution switches to the virtual interpreter (`vm_entry`).
2. Identify the central dispatcher and extract the handler table array.
3. Reverse engineer and document each handler's semantics (e.g., Opcode `0x03` = pop two values, add, push result).
4. Write a custom disassembler to parse the bytecode stream into human-readable virtual assembly (e.g., `VPUSH`, `VADD`, `VPOP`).
5. Reconstruct native assembly or Intermediate Representation (IR) from the parsed bytecode trace.

---

## 5. Operational Boundaries

1. **A Transform is a Candidate**: A decoded string or unpacked payload is a candidate until verified against reachable execution paths.
2. **No Payload Rebuild**: Do not package unpacked code into a runnable standalone exploit or re-weaponized artifact.
3. **Static Bounds**: Maintain strict isolation between static instruction analysis and target execution.
