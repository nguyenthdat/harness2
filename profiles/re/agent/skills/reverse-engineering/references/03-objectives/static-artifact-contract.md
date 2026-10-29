# Static Artifact Analysis & Evidence Contract

## Title & Overview
- **Domain**: Automated static artifact evaluation, JSON schema conformance, and verifiable observation ledger generation.
- **Scope**: Producing a strictly valid analysis JSON matching `analysis.schema.json` paired with an audited, cited `evidence.md` ledger, bounding disassembly to application spans, and passing automated validation checks.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Assignment requires delivering a structured schema JSON plus `evidence.md`.
- Task specifies static analysis only and forbids runtime execution, emulation, or dynamic attachment.
- Automated validation via `check_deliverables.py` is required for acceptance.

---

## Tooling & CLI/MCP Actions
- **Triage & Symbol Isolation Helpers**:
  - `python3 profiles/re/agent/skills/reverse-engineering/scripts/elf_triage.py <binary>`
  - `python3 profiles/re/agent/skills/reverse-engineering/scripts/elf_symbols.py <binary>`
- **Automated Validation**:
  - `python3 profiles/re/agent/skills/reverse-engineering/scripts/check_deliverables.py <json_file> <evidence_file>`
- **Decompilers**:
  - Headless IDA Pro MCP or Ghidra for bounded procedure extraction.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Deterministic Format & Section Triage
- [ ] Run `elf_triage.py` to inspect ELF/PE headers, segment LOAD deltas (`vma - file_offset`), and executable stack flags.
- [ ] Run `elf_symbols.py` to identify application entrypoints (`main`, user routines) vs runtime glue.
- [ ] Record base address and memory mappings in `evidence.md`.

### 2. Bounded Disassembly & Application Code Focus
- [ ] Do not dump full-binary disassembly.
- [ ] Isolate exact spans of application code starting from `main`.
- [ ] Decompile only procedures reachable from application logic.
- [ ] Trace all string and data cross-references (`xrefs`) back to memory offsets.

### 3. Strict JSON Field Contract Conformance
- [ ] `file_type`: Normalized token (e.g. `ELF64` or `PE32+`), never a raw sentence.
- [ ] `encoded_strings`: `true` only if transformed data decodes to valid text strings; otherwise `false`.
- [ ] `decoded_c2`: Exact URL, IP, or `host:port` string if reachable code communicates with it; otherwise `null`.
- [ ] `c2_protocol`: Protocol token (`tcp`, `http`, `dns`) if valid C2 exists; otherwise `null`.
- [ ] `techniques`: Short mechanism names, each backed by an exact instruction/address in evidence.
- [ ] `encryption_details`: Object with `algorithm`, `key`, and `key_storage` (offset/VMA).
- [ ] `decoded_strings`: Array of verified text strings only.
- [ ] `anti_analysis`: Array of verified anti-analysis routines. Label unreachable routines as unreachable.

### 4. Evidence Pairing & Automated Verification
- [ ] Ensure every field in the deliverable JSON is cited with a reproducible tool command, VMA, and file offset in `evidence.md`.
- [ ] Run automated deliverable validator:
  ```bash
  python3 profiles/re/agent/skills/reverse-engineering/scripts/check_deliverables.py analysis.json evidence.md
  ```
- [ ] Confirm output reports `RESULT: PASS`.

---

## Boundaries & Anti-Patterns
- **Do not execute or emulate the target under any circumstances**: When static contract is active, dynamic observation is forbidden.
- **Do not infer values from filenames, labels, or challenge titles**: Report only what the artifact bytes establish.
- **Do not report unverified decoded blobs as text strings**: Non-ASCII or random data must be classified as raw data blobs.
