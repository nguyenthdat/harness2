# Vulnerability Research, Patch Analysis & Binary Diffing

## Title & Overview
- **Domain**: Binary diffing, 1-day vulnerability analysis, patch reversal, and symbol propagation across binary versions.
- **Scope**: Structural and graph diffing (BinDiff, BSim, Diaphora), identifying security patches, root cause analysis of vulnerabilities, and propagating renamed symbols between binary revisions.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Task involves two revisions of a binary (e.g. unpatched vs patched release, CVE analysis).
- Need to locate security fixes or vulnerability mitigations introduced in an update.
- Need to port symbols, decompiled types, or annotations from an analyzed or debug build to a stripped release.

---

## Tooling & CLI/MCP Actions
- **Primary Binary Diffing Engines**:
  - `BinDiff`: Industry-standard AST and graph-based binary differ (IDA Pro / Ghidra plugin).
  - Ghidra `BSim`: Function feature vector matching for finding similar functions across large codebases.
  - `Diaphora`: Pure Python diffing engine for IDA Pro / Ghidra.
- **Command-Line & Automation**:
  - `bindiff --primary=<unpatched.idb> --secondary=<patched.idb> --output_dir=<out>`
  - Radare2 `radiff2`: Fast binary delta comparison from CLI.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Database Preparation & Normalization
- [ ] Ensure both target binaries are analyzed under identical decompiler versions and compiler settings.
- [ ] Run full initial auto-analysis on both unpatched and patched samples.
- [ ] Export decompiler database exports (e.g. BinDiff export `.BinExport`).

### 2. Graph & Instruction Diffing Pass
- [ ] Run BinDiff or Diaphora across both exported databases.
- [ ] Sort matched functions by similarity score:
  - 1.0 (Identical): Exact match in instructions and basic block flow.
  - 0.5 – 0.99 (Changed): Modified functions containing security fixes or refactored logic.
  - 0.0 (Unmatched / New): Newly added helper routines or removed dead code.

### 3. Patch Identification & Delta Analysis
- [ ] Inspect changed basic blocks within modified functions:
  - Added bounds checks or integer overflow validations (`cmp`, `jb`, `jae`).
  - Added null pointer checks (`test reg, reg; jz error`).
  - Replaced unsafe string/buffer APIs (`strcpy` -> `strncpy`, `sprintf` -> `snprintf_s`).
  - Modified memory allocation sizes or resource cleanup paths.

### 4. Symbol & Type Migration
- [ ] Import high-confidence matches (similarity > 0.95) to automatically transfer function names and prototypes from old database to new target.
- [ ] Verify imported type signatures against decompiled pseudocode.

---

## Boundaries & Anti-Patterns
- **Do not assume all differences are security patches**: Compilers alter basic block layouts due to optimization, inlining, or compiler version upgrades. Filter out noise.
- **Do not ignore compiler inlining differences**: An apparent missing function may have simply been inlined into its caller.
- **Do not diff binaries compiled with different optimization flags without normalising**: Debug vs Release builds will produce massive false positives.
