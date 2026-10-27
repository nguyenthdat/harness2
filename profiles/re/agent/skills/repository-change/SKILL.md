---
name: repository-change
description: Read before changing code in this repository — fixes, API contracts, features, refactors. Covers locating the target and its callers, reproducing behavior, keeping the diff scoped, testing with throwaway scripts, and reviewing the final change.
---

# Repository change

## Procedure

1. Translate a terse or non-English request into observable behavior in one or two lines: inputs, outputs, error type/code/position, and what must keep working.
2. Read the target module and every caller, test, and package export that touches it. List its current public names and accepted input grammar; everything the request does not name keeps its current behavior. Docs that point at missing files are not a specification. Use `git log` only to understand the target file, not to hunt for a reference patch.
3. Reproduce the current behavior with a short `python3 - <<'PY'` script before editing.
4. Edit the smallest existing surface that satisfies the request. Keep public names and behavior outside the request. Do not rewrite README/docs, broaden package exports, or add speculative aliases, parameters, or abstractions unless the request or a caller requires them.
5. Test with a throwaway script, not a new committed test suite: normal nesting, text that was already literal, and each requested error with its exact code and position. A successful write is not verification.
6. Review the change: `git status --short`, `git diff`, `git diff --check`. Remove generated `__pycache__`/`*.pyc` and any scratch file you created. Confirm only intended files changed and the change is still present.
7. Finish with a short report: files changed, observable behavior, commands run.
