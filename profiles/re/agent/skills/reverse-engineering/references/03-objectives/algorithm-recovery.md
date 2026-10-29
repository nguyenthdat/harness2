# Cryptographic Identification & Algorithm Recovery

## Title & Overview
- **Domain**: Cryptographic routines, custom encryption schemes, key scheduling, and hashing algorithms inside binary artifacts.
- **Scope**: Identifying standard crypto constants (AES, DES, RSA, SHA, MD5), detecting custom bitwise transformations and PRNGs, recovering hardcoded or derived encryption keys, and reimplementing decryptors.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Target contains encrypted strings, encrypted configuration blobs, or encrypted network payloads.
- High entropy (> 7.5) or pseudo-random byte sequences embedded in `.data` or `.rodata`.
- Presence of cryptographic constants, S-Boxes, or initialization vectors (e.g. SHA-256 initial hash values, AES Te0-Te3 tables).
- Extensive use of bitwise operations: `xor`, `rol`/`ror`, `shl`/`shr`, modular arithmetic.

---

## Tooling & CLI/MCP Actions
- **Primary Decompilers & Analyzers**:
  - Headless IDA Pro MCP / Ghidra: Disassembly and decompilation of crypto loops.
  - Crypto Scanning Tools: `findcrypt-yara`, `signsrch`, Ghidra `FindCrypt`.
- **Validation & Prototyping**:
  - Python `cryptography` library, `hashlib`, CyberChef.
  - Verification script: Custom Python decoders running against isolated byte slices.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Crypto Constant & S-Box Scanning
- [ ] Scan binary for known cryptographic constants using `findcrypt`:
  - AES: Forward/inverse S-Box (`0x63, 0x7c, 0x77, 0x7b...`), round constants (`Rcon`).
  - MD5 / SHA-1 / SHA-256: Initial state constants (`0x67452301`, `0xefcdab89`, `0x98badcfe`, etc.).
  - CRC32: Polynomial tables (`0xEDB88320` or `0x04C11DB7`).
  - ChaCha20 / Salsa20: "expand 32-byte k" string constant.
- [ ] Record VMA and cross-references (`xrefs`) for all identified crypto constants.

### 2. Algorithm Flow & Mode Identification
- [ ] Trace functions referencing detected S-boxes or constants.
- [ ] Determine cipher mode:
  - Symmetric block cipher (AES-CBC, AES-CTR, AES-GCM, DES).
  - Stream cipher (RC4, ChaCha20).
  - Public key cryptography (RSA, ECC curve operations).
- [ ] Identify key length (e.g. AES-128 vs AES-256 by counting key expansion rounds: 10, 12, or 14).

### 3. Key & IV Extraction
- [ ] Locate key derivation function (KDF): PBKDF2, HKDF, custom hash chains.
- [ ] Identify hardcoded keys or initialization vectors (IVs): Check static memory or decrypted strings.
- [ ] If key is dynamically derived: Trace memory reads and follow derivation operations from system entropy or hardware IDs.

### 4. Custom Algorithm Analysis & Python Emulation
- [ ] For non-standard crypto (custom XOR, rolling keys, custom substitution/permutation):
  - Isolate the transformation function.
  - Map each bitwise operation and state update.
- [ ] Reimplement the algorithm in Python.
- [ ] Verify decrypted output matches known plaintext markers (magic bytes, readable strings).

---

## Boundaries & Anti-Patterns
- **Do not guess encryption algorithms based on naming alone**: A function named `decryptAES` may actually implement RC4 or custom XOR. Verify constants and mathematical structure.
- **Do not confuse compression with encryption**: Zlib/deflate streams have high entropy and magic headers (`\x78\x9c`); test decompression before assuming encryption.
- **Do not output unverified decrypted blobs**: Always validate that the candidate key decodes to plausible text or structured data.
