---
name: evidence-claims
description: Read before stating what a sample does. Separates observation, inference, and unknown, and bounds decode and negative searches.
---

# Evidence claims

Every statement is one of:

- **Observation.** Tool output you can rerun: bytes, address or file offset, instruction, decoded buffer, header field.
- **Inference.** A conclusion that names the observations it uses and what would refute it.
- **Unknown.** Not present in the work you did. Say what was searched and where you stopped.

Rules:

- Cite the tool and the address or file offset for every positive claim. A claim with no citation stays an inference or is dropped.
- A filename, symbol, section name, or string that nothing references is not behavior. Report the bytes that implement the operation.
- An import, string, or function with no caller and no data pointer is present and unreachable. Do not describe it as a runtime effect. It may be listed only with that reachability limit.
- Decode a referenced blob once with the transform the code uses. At most two further attempts, each with a concrete reason (for example raw key bytes versus the ASCII rendering of the key). If none yields text, plausible code, or a literal endpoint, record the negative and stop. Do not sweep key rotations, alphabets, or cipher families.
- Compiler and runtime strings (`http://www.debian.org/Bugs/`, `LD_*`, CRT banners) are not application findings.
- Do not invent a family, campaign, CVE, or standard. Name one only when a distinctive byte pattern is shown and the comparison source is named; otherwise the family is unknown.
- A finished answer says what is confirmed, what is inferred, and what was not checked.
