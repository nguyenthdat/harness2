---
name: anti-analysis
description: Read when claiming a packer, debugger check, VM evasion, process injection, or exploit mitigation. Separates reached checks from dead code and compiler hardening.
---

# Anti-analysis

Call something anti-analysis only when reachable instructions implement the check or the transform.

- Packer, crypter, or overlay: cite the stub, the transform, and the unpacked region. A high entropy section alone is not a packer.
- Debugger or VM checks: cite the call or instruction (`IsDebuggerPresent`, CPUID, timing) and the branch that uses the result. A string naming a debugger tool is not a check.
- Unreachable checks stay in the unknown or dead-code note. Do not promote them to active evasion.
- Process injection requires another process (remote allocate, write, or thread). Mapping the sample's own payload RWX and jumping to it is self-execution, not injection.
- `executable_stack`, missing PIE, missing RELRO, and CET are image properties. Record them as properties, not as techniques and not as evasion.
- Missing S-box, AES-NI, or key schedule means the code is not AES, even if a name says AES. Name the primitive the instructions implement (for example repeating-key XOR) and where the key bytes live.
