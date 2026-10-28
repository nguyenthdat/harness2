---
name: sample-safety
description: Read before opening a malware sample or other untrusted binary. Covers hashing, extraction, and the ban on execution, detonation, and contacting indicators.
---

# Sample safety

`RULES.md` states the execution ban. This rule is how to touch the file.

- Work on the path the parent named. Do not choose a nearby fixture, sample, or example binary.
- Identify it with read-only tools: size, `file`, and SHA-256 (`shasum -a 256` or `sha256sum`). Do not `chmod +x`, do not run it, and do not pass it to a loader, installer, or emulator.
- Hashes and header parses are observations. A type string from `file` is a guess until the header parse agrees.
- Extract embedded members into a new directory under the task workspace. Do not execute an extracted payload, script, or document macro. Decode bytes in a separate buffer or a non-executable temp file.
- Do not `curl`, `ping`, `dig`, browse, or otherwise contact an indicator found in the sample. Parsing a PCAP, HAR, SAZ, or sandbox report the parent already placed on disk is not contact.
- Quote short excerpts. Put long decoded blobs in a workspace file and cite the path, offset, and length. Do not reconstruct a runnable dropper in the answer.
- When the question is finished, close IDA and REA sessions opened for this sample. Do not leave a database lease on an untrusted image.
