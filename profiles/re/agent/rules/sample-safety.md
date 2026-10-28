---
name: sample-safety
description: Read before opening a malware sample or other untrusted binary. Covers hashing, extraction, and when execution, detonation, and contacting indicators are still forbidden.
---

# Sample safety

`RULES.md` states when execution is allowed. This rule is how to touch the file.

- Static is the default. Dynamic analysis is allowed when the parent asks, or when bytes cannot answer the question: a debugger, Frida, an emulator, or a proxy, on a target the parent named. The do-not-run and do-not-contact lines below yield in that case.
- A static contract still wins. If the task says static-only, or `tools.json` names only `file`, `strings`, and `objdump`, or the deliverable is schema JSON plus `evidence.md` under `skill://static-artifact-analysis`, do not execute, debug, emulate, or detonate.
- Do not launch a suspicious sample on the host, mark it executable, or contact a host, URL, or address found in it, unless the parent explicitly asked to run that sample or to capture that traffic. Offline reads of a capture the parent already supplied stay allowed.

- Work on the path the parent named. Do not choose a nearby fixture, sample, or example binary.
- Identify it with read-only tools: size, `file`, and SHA-256 (`shasum -a 256` or `sha256sum`). Do not `chmod +x`, do not run it, and do not pass it to a loader, installer, or emulator.
- Hashes and header parses are observations. A type string from `file` is a guess until the header parse agrees.
- Extract embedded members into a new directory under the task workspace. Do not execute an extracted payload, script, or document macro. Decode bytes in a separate buffer or a non-executable temp file.
- Do not `curl`, `ping`, `dig`, browse, or otherwise contact an indicator found in the sample. Parsing a PCAP, HAR, SAZ, or sandbox report the parent already placed on disk is not contact.
- Quote short excerpts. Put long decoded blobs in a workspace file and cite the path, offset, and length. Do not reconstruct a runnable dropper in the answer.
- When the question is finished, close IDA and REA sessions opened for this sample. Do not leave a database lease on an untrusted image.
