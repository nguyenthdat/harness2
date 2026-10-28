---
name: tool-routing
description: Read before the first IDA, REA, or shell analysis call. Selects the official IDA MCP, REA, or a read-only helper without setup or a second database.
---

# Tool routing

`skill://reverse-engineering` names the REA tool for each format. This rule chooses the engine.

1. Confirm the path and hash with `rule://sample-safety`.
2. For header, import, certificate, resource, note, or archive inventory that a target-free REA tool covers, call that REA tool. Read its live input schema. Do not open a disassembler first.
3. For native decompilation or cross-references, use the official `ida` MCP: `open_database` with `gui: false`, then `execute_python` or the connected query tool, then `close_database` for that instance only. `list_databases` and `reference` are the read-only checks. Use the live schema if an argument differs.
4. Do not also open that file with OMP's native `ida` tool or with REA `provider_id: "ida"`. Those are separate database managers.
5. If the IDA server cannot open the file, use REA `open_binary` on the default Ghidra provider. Do not pass an `.idb`, `.i64`, or other database as the input; pass the original artifact.
6. On an ELF schema task, run this profile's `skills/static-artifact-analysis/scripts/elf_triage.py`. If the workspace has `.omp/skills/static-artifact-analysis/scripts/`, use that copy so it matches `check_deliverables.py`. The script only reads bytes.
7. On a failed REA or IDA call, change the reported argument or classify the timeout using `skill://reverse-engineering` and its recovery note. Do not run setup, doctor, or an installer. One fallback, then record the gap.
8. Do not use a source-code knowledge graph for a binary. Strings and names are not a call graph.
