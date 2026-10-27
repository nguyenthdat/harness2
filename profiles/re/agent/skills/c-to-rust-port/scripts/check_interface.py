#!/usr/bin/env python3
"""Mechanical completion gate for a C-to-Rust port.

Answers, deterministically, questions that `cargo check` cannot:

  1. Does every function declared in the C header have a `pub fn` in the
     Rust sources?  (A missing/renamed public function still compiles, so a
     successful build says nothing about interface completeness.)
  2. Does `src/lib.rs` declare the module that holds the port?
  3. Does any `unsafe` token survive comment/string stripping?
  4. With --cargo-check: does `cargo check` report zero warnings and zero
     errors?  (The crate name in this workspace trips `non_snake_case`, so a
     clean build needs an explicit allow at the crate root.)

Exit codes: 0 = OK, 1 = problems found, 2 = bad input / tool failure.

Usage:
    python3 scripts/check_interface.py [--root .] [--cargo-check]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys

C_FUNC_RE = re.compile(r"([A-Za-z_]\w*)\s*\(")
RS_FUNC_RE = re.compile(r"\bpub\s+fn\s+([A-Za-z_]\w*)")


def fail(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def strip_rust_noise(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    text = re.sub(r'r#*".*?"#*', '""', text, flags=re.S)
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    return text


def find_header(root: str, explicit: str | None) -> str:
    if explicit:
        if not os.path.isfile(explicit):
            fail(f"C header not found: {explicit}")
        return explicit
    candidates = sorted(glob.glob(os.path.join(root, "c_source", "**", "*.h"), recursive=True))
    if not candidates:
        candidates = sorted(glob.glob(os.path.join(root, "**", "include", "*.h"), recursive=True))
    if not candidates:
        fail("no C header found under c_source/**/*.h (pass --c-header)")
    if len(candidates) > 1:
        print("note: multiple headers found, using " + candidates[0], file=sys.stderr)
        print("      others: " + ", ".join(candidates[1:]), file=sys.stderr)
    return candidates[0]


def c_function_names(header: str) -> list[str]:
    names: list[str] = []
    with open(header, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            line = re.sub(r"/\*.*?\*/", " ", line)
            if not line.endswith(";"):
                continue
            m = C_FUNC_RE.search(line)
            if m:
                names.append(m.group(1))
    return list(dict.fromkeys(names))


def rust_sources(root: str) -> list[str]:
    files = sorted(glob.glob(os.path.join(root, "src", "**", "*.rs"), recursive=True))
    if not files:
        fail("no Rust sources under src/ (write the port first)")
    return files


def rust_function_names(files: list[str]) -> set[str]:
    names: set[str] = set()
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as fh:
            names.update(RS_FUNC_RE.findall(fh.read()))
    return names


def unsafe_hits(files: list[str]) -> list[str]:
    hits = []
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as fh:
            body = strip_rust_noise(fh.read())
        for lineno, line in enumerate(body.splitlines(), 1):
            if re.search(r"\bunsafe\b", line):
                hits.append(f"{path}:{lineno}: {line.strip()}")
    return hits


def touch_sources(files: list[str]) -> None:
    for path in files:
        try:
            os.utime(path, None)
        except OSError:
            pass


def cargo_check(root: str, files: list[str]) -> int:
    touch_sources(files)
    cmd = ["cargo", "check", "--message-format=json"]
    try:
        proc = subprocess.run(
            cmd, cwd=root, capture_output=True, text=True, timeout=600
        )
    except FileNotFoundError:
        fail("cargo not found on PATH")
    except subprocess.TimeoutExpired:
        fail("cargo check timed out after 600s")

    diagnostics = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("reason") != "compiler-message":
            continue
        inner = msg.get("message", {})
        if inner.get("level") in ("warning", "error"):
            diagnostics.append(inner)

    errors = [d for d in diagnostics if d.get("level") == "error"]
    warnings = [d for d in diagnostics if d.get("level") == "warning"]

    if proc.returncode != 0 and not errors:
        fail("cargo check failed without parsable diagnostics:\n" + proc.stderr[-4000:])

    for level, items in (("error", errors), ("warning", warnings)):
        for d in items[:20]:
            print(f"  cargo {level}: {d.get('message', '')}")
        if len(items) > 20:
            print(f"  ... {len(items) - 20} more cargo {level}s")

    print(f"cargo check: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if diagnostics else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="C-to-Rust interface and build gate")
    ap.add_argument("--root", default=".", help="crate root (default: .)")
    ap.add_argument("--c-header", default=None, help="C header (default: c_source/**/*.h)")
    ap.add_argument("--module", default=None, help="module stem expected in src/lib.rs (default: infer)")
    ap.add_argument("--cargo-check", action="store_true", help="also require zero cargo warnings/errors")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        fail(f"root is not a directory: {root}")

    header = find_header(root, args.c_header)
    c_names = c_function_names(header)
    if not c_names:
        fail(f"could not parse any prototypes from {header}")

    files = rust_sources(root)
    rs_names = rust_function_names(files)

    module = args.module
    if module is None:
        lib = os.path.join(root, "src", "lib.rs")
        candidates = [p for p in files if os.path.abspath(p) != os.path.abspath(lib)]
        if len(candidates) == 1:
            module = os.path.splitext(os.path.basename(candidates[0]))[0]
        else:
            fail("cannot infer the port module; pass --module <stem>")

    missing = [n for n in c_names if n not in rs_names]

    print(f"header: {header} ({len(c_names)} functions)")
    print(f"rust:   {len(files)} file(s), {len(rs_names)} public functions")

    problems = 0

    if missing:
        problems += 1
        print("MISSING public functions (declared in the C header, absent from src/):")
        for name in missing:
            print(f"  - {name}")

    unsafe = unsafe_hits(files)
    if unsafe:
        problems += 1
        print("UNSAFE code found (the task forbids it):")
        for hit in unsafe:
            print(f"  - {hit}")

    lib = os.path.join(root, "src", "lib.rs")
    if not os.path.isfile(lib):
        problems += 1
        print(f"MISSING {lib}: the crate needs a library root declaring `pub mod {module};`")
    else:
        with open(lib, encoding="utf-8", errors="replace") as fh:
            lib_body = fh.read()
        mod_re = re.compile(rf"\b(?:pub\s+)?mod\s+{re.escape(module)}\s*;")
        if not mod_re.search(lib_body):
            problems += 1
            print(f"MISSING module declaration `pub mod {module};` in {lib}")

    if problems:
        print("RESULT: FAIL")
        return 1

    if args.cargo_check:
        if cargo_check(root, files) != 0:
            print("RESULT: FAIL")
            return 1

    print("RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
