# Binary Diffing & Patch Analysis

Actionable guidance for cross-version binary diffing, vulnerability patch analysis, and symbol migration across builds (x86, x64, ARM, ARM64) using BinDiff, Ghidra BSim, and REA MCP tools.

---

## 1. Diffing Objectives & Workflows

Binary diffing compares two compiled binaries (e.g., vulnerable version vs. patched version, or unstripped debug build vs. stripped release build) to isolate structural and behavioral divergences:

### Primary Use Cases:
1. **Patch Analysis / 1-Day Triage**: Pinpoint security fixes, integer overflow checks, bounds verifications, and logic adjustments between release versions.
2. **Symbol & Type Migration**: Port recovered function names, comments, and struct definitions from a symbolicated binary to an obfuscated or stripped binary.
3. **Cross-Architecture / Compiler Matching**: Correlate functions across different compiler optimization levels (`-O0` vs `-O3`) or architectures (x86 vs ARM).

---

## 2. Graph & Function Matching Algorithms

Automated diff engines evaluate similarity using a hierarchy of matching heuristics:

| Algorithm / Heuristic | Mechanism | Confidence |
|---|---|---|
| **Exact Function Hash** | MD5/SHA256 of normalized instruction bytes (relocations masked) | 1.00 (Identical) |
| **Call Graph Topology** | Matches nodes by identical caller/callee structural edges | 0.90 - 0.98 |
| **CFG Graph Isomorphism** | Matches basic block counts, edge counts, and loop structures | 0.80 - 0.95 |
| **Instruction Mnemonic Hash** | Compares opcode sequences while ignoring register names and constants | 0.75 - 0.90 |
| **String Cross-References** | Matches functions referencing identical string literal constants | 0.70 - 0.85 |
| **Dominator Tree / Cyclomatic** | Compares complexity metrics and control flow dominators | 0.60 - 0.80 |

---

## 3. Tooling Workflows

### 1. BinDiff (Google / Zynamics)
- **Plugin for IDA Pro & Ghidra**:
  1. Export `.BinExport` files from both disassembly databases:
     - Target A: `app_v1.BinExport`
     - Target B: `app_v2.BinExport`
  2. Run BinDiff comparison:
     ```bash
     bindiff app_v1.BinExport app_v2.BinExport --output_dir=/tmp/diff_results
     ```
  3. Outputs similarity score (`0.0` to `1.0`) and confidence score (`0.0` to `1.0`) for every function pair.

### 2. Ghidra BSim (Feature Vector Similarity)
- Stores function feature vectors in an SQLite or PostgreSQL database.
- Scales across large binary corpuses to identify code provenance, statically linked third-party libraries, and shared vulnerabilities without full graph alignment.

### 3. REA MCP: `match_native_functions`
Target-free function matching across two analysis evidence bundles:
- `match_native_functions` pairs functions using exact names and observed instruction bodies without opening a heavy graphical diffing interface.
- Follow up with `compare_functions` on selected candidate pairs to inspect detailed control flow divergences and basic block transitions.

---

## 4. Patch Analysis Methodology

Follow a structured triage process to isolate security patches between two binary versions:

### Step 1: Filter Unchanged Code
Discard all functions with a similarity score of `1.00`. In most software updates, 90–95% of functions are structurally identical.

### Step 2: Triage Modified Functions (`0.50 < Similarity < 0.99`)
Sort modified functions by name and complexity. Prioritize functions that match:
- High cyclomatic complexity.
- Network parsers, file format decoders, authentication handlers, or memory allocation routines.

### Step 3: Analyze Control Flow Graph (CFG) Divergences
Inspect added, deleted, or altered basic blocks in the patched binary:
1. **Added Boundary & Range Checks**:
   - New `cmp` instructions followed by conditional jumps (`ja`, `jg`, `jbe`) returning an error code.
   - Example: Adding `if (len > MAX_BUFFER_SIZE) return -1;` to prevent buffer overflows.
2. **Integer Overflow Guards**:
   - New checks testing for integer wrap-around before calling allocation routines:
     ```asm
     ; Patched overflow check
     mov  rax, [count]
     imul rax, [elem_size]
     jo   handle_integer_overflow    ; jump if overflow flag set
     ```
3. **Null Pointer Validation**:
   - New tests verifying return values of allocation or lookup calls:
     ```asm
     test rax, rax
     jz   handle_null_pointer
     ```
4. **Memory Management Adjustments**:
   - Replacement of unsafe CRT routines (`strcpy`, `sprintf`, `gets`) with bounded equivalents (`strncpy`, `snprintf_s`).

---

## 5. Operational Boundaries

1. **Defensive Analysis Focus**: Patch analysis is performed strictly for root cause identification, vulnerability classification, and patch verification.
2. **No Exploit Weaponization**: Do not construct proof-of-concept exploit payloads, shellcode, or weaponization chains from observed patch differences.
