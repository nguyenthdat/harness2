# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CRUST-Bench adapter: C-to-safe-Rust transpilation tasks, internal runner."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import threading
import tomllib
from dataclasses import replace
from pathlib import Path

from .. import config
from ..core import runmark as RM
from ..core import tree as HT
from ..core.spec import BenchPrompts, BenchSpec, resolve_channel_model
from ..substrate.base import Install, RunRequest
from ..substrate.omp import OMP_SURFACE, OmpSubstrate
from .tasks import discover, select

_TIMEOUT_DEFAULT = {"omp": 3600}
_HELPER_LIBS = frozenset({"bostree", "fslib"})
_ROOT_IMPLEMENTATION_LIBS = frozenset({"emlang", "libbeaufort", "libm17", "murmurhash_c"})


def _project_key(name: str) -> str:
    """Normalize only the documented CBench/RBench spelling differences."""
    key = name.casefold().replace("-", "_")
    return key.removeprefix("proj_")

def _rbench_dir(task_id: str) -> Path:
    """Resolve a CBench name against the exact RBench inventory, rejecting ambiguity."""
    root = config.crust_repo() / "datasets" / "RBench"
    matches = sorted(
        p for p in root.iterdir() if p.is_dir() and _project_key(p.name) == _project_key(task_id)
    )
    if not matches:
        raise FileNotFoundError(f"No RBench project maps unambiguously to CBench task {task_id!r}")
    if len(matches) != 1:
        raise ValueError(f"Ambiguous RBench mapping for {task_id!r}: {[p.name for p in matches]}")
    return matches[0]


def _cbench_dir(task_id: str) -> Path:
    path = config.crust_repo() / "datasets" / "CBench" / task_id
    if not path.is_dir():
        raise FileNotFoundError(f"CBench sources missing for {task_id}: {path}")
    return path

CRUST_BASE = BenchPrompts(
    work="""\
Transpile the provided C repository into safe, idiomatic Rust code that matches the given 
interface specifications and passes all test cases. The Rust implementation must be memory-safe 
(avoid unsafe blocks unless explicitly required by the interface), maintain the semantics of the 
original C code, and conform to Rust idioms.""",
    domain_word="category",
    inv_levers="""\
The generated Rust code MUST:
- Implement every function signature declared in the provided interfaces
- Compile without errors or warnings
- Pass all provided test cases
- Use safe Rust (no unsafe blocks unless the interface itself declares unsafe functions)
- Handle memory safely (no raw pointers, manual allocation, or undefined behavior)""",
    dom_levers="",
    yardstick="Correctness is measured by successful compilation and test pass rate.",
    deliverable_word="Rust source files",
    domain_guidance="",
    selection_checks="""\
The Rust implementation must compile cleanly and pass the provided test suite. Type correctness 
and memory safety are enforced by the Rust compiler.""",
    selection_lead="",
    selection_conformance="full",
    prompt_pack="adapt",
)

CRUST_DOMAINS = {
    "cryptography": "Cryptographic functions and security primitives",
    "networking": "Network protocols and socket programming",
    "data-structures": "Data structure implementations (trees, lists, graphs)",
    "algorithms": "Algorithmic implementations (sorting, searching, mathematical)",
    "system-utilities": "System-level utilities and general-purpose code",
}


def _infer_domain(project_name: str) -> str:
    """Infer CRUST task domain from project name patterns."""
    name_lower = project_name.lower()
    if any(x in name_lower for x in ["hash", "crypt", "encrypt", "aes", "sha", "cipher"]):
        return "cryptography"
    if any(x in name_lower for x in ["net", "tcp", "udp", "http", "socket", "protocol"]):
        return "networking"
    if any(x in name_lower for x in ["tree", "list", "queue", "stack", "graph", "heap"]):
        return "data-structures"
    if any(x in name_lower for x in ["sort", "search", "genetic", "math", "algorithm"]):
        return "algorithms"
    return "system-utilities"


def crust_prompts(*, domain: str = "") -> BenchPrompts:
    """CRUST-wide profile plus domain overlay."""
    guidance = CRUST_DOMAINS.get(domain, "")
    if guidance:
        guidance = f"Domain: {guidance}\n\n{guidance}"
    return replace(CRUST_BASE, domain_guidance=guidance)


def crust_spec(substrate: str) -> BenchSpec:
    """The CRUST BenchSpec for one substrate cell."""
    if substrate != "omp":
        raise ValueError(
            f"CRUST only supports the 'omp' substrate currently; got {substrate!r}. "
            "OpenCode and Codex do not have working CRUST runners."
        )
    channel = resolve_channel_model(None, None, effort="high")
    return BenchSpec(
        name="crust",
        runs_root=config.RUNS / "crust",
        install_mode="omp_root",
        prompts=CRUST_BASE,
        channels={"proposer": channel, "selector": channel},
        domain_word="category",
        leak_globs=(
            "RBench/*/bin/**",
            "RBench/*/tests/**",
            "RBench/*/src/bin/**",
            "src/bin/**",
        ),
        allow_subagents=False,
        proposer_deliverables="contents",
        obs_trunc=50_000,
    )


def _compose_task_prompt(task_id: str) -> str:
    """Build CRUST task prompt: honest instructions, C sources, and Rust module interfaces."""
    cbench = _cbench_dir(task_id)
    rbench = _rbench_dir(task_id)

    parts = [f"# C-to-Rust Transpilation Task: {task_id}\n"]

    # Collect C sources
    c_files = sorted(cbench.rglob("*.c")) + sorted(cbench.rglob("*.h"))
    if c_files:
        parts.append("## Original C Sources\n")
        parts.append("Complete C project files are staged under `c_source/` in your workspace.\n\n")
        for cf in c_files:
            rel = cf.relative_to(cbench)
            try:
                content = cf.read_text(encoding="utf-8", errors="replace")
                parts.append(f"### c_source/{rel.as_posix()}\n```c\n{content}\n```\n")
            except OSError:
                parts.append(f"### c_source/{rel.as_posix()}\n(unreadable)\n")

    # Collect Rust interface specifications from src/interfaces
    iface_dir = rbench / "src" / "interfaces"
    if iface_dir.is_dir():
        rs_files = sorted(iface_dir.glob("*.rs"))
        if rs_files:
            parts.append("## Required Rust Interface Specifications\n")
            parts.append(
                "Interface scaffolds are staged under `src/` in your workspace. "
                "Implement every function signature in safe Rust:\n\n"
            )
            for rf in rs_files:
                rel = rf.relative_to(iface_dir)
                try:
                    content = rf.read_text(encoding="utf-8", errors="replace")
                    parts.append(f"### src/{rel.as_posix()}\n```rust\n{content}\n```\n")
                except OSError:
                    parts.append(f"### src/{rel.as_posix()}\n(unreadable)\n")

    # Inform about test suite count from pristine src/bin without leaking contents
    test_dir = rbench / "src" / "bin"
    if test_dir.is_dir():
        test_files = list(test_dir.glob("*.rs"))
        if test_files:
            parts.append(
                f"\n## Test Suite\n{len(test_files)} private validation target(s) will evaluate your implementation.\n"
            )

    parts.append("\n## Instructions\n")
    parts.append("""\
Transpile the C code into safe, idiomatic Rust that:
1. Implements every function in the interface specifications under `src/`
2. Maintains the original C semantics
3. Strictly uses safe Rust (no `unsafe` blocks; the compiler lint `forbid(unsafe_code)` is enforced)
4. Compiles cleanly without errors
5. Passes the private validation test suite

Deliver your implementation in `src/` matching the crate module structure.""")

    return "\n".join(parts)


_BASE_LOCK = threading.Lock()
_BASE_DONE: set[Path] = set()


def _has_implementation(content: str) -> bool:
    clean = re.sub(r"//.*", "", content)
    clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL)
    bodies = re.findall(r"\{([^{}]*)\}", clean)
    if not bodies:
        return False
    for b in bodies:
        b_clean = re.sub(r"\b(unimplemented|todo)\s*!\s*(\([^)]*\))?\s*;?", "", b).strip()
        if b_clean:
            return True
    return False


def _is_delivery(run_dir: Path) -> bool:
    """Return True only if candidate produced non-empty, modified Rust code beyond stubs."""
    run_path = Path(run_dir)
    src_dir = run_path / "src"
    search_root = src_dir if src_dir.is_dir() else run_path
    src_files = [
        p
        for p in search_root.rglob("*.rs")
        if "target" not in p.parts and "src/bin" not in p.as_posix()
    ]
    if not src_files:
        return False

    for sf in src_files:
        try:
            content = sf.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if _has_implementation(content):
            return True
    return False

class CrustAdapter:
    """CRUST-Bench behind the BenchmarkAdapter protocol, running directly on OmpSubstrate."""

    def __init__(
        self,
        substrate: str = "omp",
        *,
        timeout: int | None = None,
        split_file: Path | None = None,
    ):
        if substrate != "omp":
            raise ValueError(
                f"CrustAdapter only supports substrate 'omp' (got {substrate!r}). "
                "OpenCode and Codex do not have working CRUST runners."
            )
        self.split_file = split_file
        self.spec = crust_spec(substrate)
        self.substrate = OmpSubstrate(launcher=self._launch_omp)
        self.timeout = int(timeout or _TIMEOUT_DEFAULT[substrate])
        self._results_root = config.RUNS / "crust" / "results" / self.substrate.name
        self._judge_cache: dict[str, dict | None] = {}
        self._judge_lock = threading.Lock()

    def tasks(self, split: str = "all") -> list[str]:
        return select(discover("crust"), split, self.split_file, benchmark="crust")

    def domain_of(self, task_id: str) -> str:
        return discover("crust")[task_id]

    def reference_domain_order(self) -> list[str]:
        return sorted(set(discover("crust").values()))

    def prompts_for(self, task_id: str) -> BenchPrompts:
        return crust_prompts(domain=self.domain_of(task_id))

    def task_prompt(self, task_id: str) -> str:
        """C sources + Rust interface spec as the agent received it."""
        return _compose_task_prompt(task_id)

    def task_files(self, task_id: str) -> Path | None:
        """The C source directory."""
        d = _cbench_dir(task_id)
        return d if d.is_dir() else None

    def _run_dir(self, run_id: str) -> Path:
        return self._results_root / run_id

    def execute(
        self, task_id: str, harness_dir: Path | None, run_id: str, *, timeout: int | None = None
    ) -> Path:
        out = self._run_dir(run_id)
        if RM.is_complete(out, harness_dir=harness_dir) and self.delivered(out):
            return out
        if out.is_dir() and any(out.iterdir()):
            reason = RM.why_not(out, harness_dir=harness_dir)
            print(f"  [crust-{self.substrate.name}] re-rolling {run_id}: {reason}", flush=True)
            shutil.rmtree(out, ignore_errors=True)

        install = self._install(harness_dir)
        try:
            self.substrate.execute(task_id, install, [run_id], int(timeout or self.timeout))
        finally:
            if install.extras.get("harness") == "staged":
                shutil.rmtree(install.staging_dir, ignore_errors=True)

        if not self.delivered(out):
            print(f"  [crust] {run_id} produced no non-stub Rust files; left unmarked", flush=True)
        else:
            RM.mark_complete(out, run_id=run_id, harness_dir=harness_dir)

        return out

    def _install(self, harness_dir: Path | None) -> Install:
        if harness_dir is None:
            return Install(
                staging_dir=self.base_harness(), fingerprint="base", extras={"harness": "base"}
            )
        inst = self.substrate.materialise(Path(harness_dir), self.spec, {})
        return Install(
            staging_dir=inst.staging_dir,
            fingerprint=inst.fingerprint,
            extras={**inst.extras, "harness": "staged"},
        )

    def _launch_omp(self, req: RunRequest, install: Install) -> list[Path]:
        """OMP launcher: direct omp runtime."""
        base = install.extras.get("harness") == "base"
        if base:
            install = self.substrate.materialise(install.staging_dir, self.spec, {})
        try:
            return [
                self._roll_omp(req.task_ref, run_id, install, req.timeout)
                for run_id in req.run_ids
            ]
        finally:
            if base:
                shutil.rmtree(install.staging_dir, ignore_errors=True)

    def _roll_omp(self, task_id: str, run_id: str, install: Install, timeout: int) -> Path:
        run_dir = self._run_dir(run_id).resolve()
        run_dir.mkdir(parents=True, exist_ok=True)
        ws = Path(tempfile.mkdtemp(prefix="crust-omp-"))
        try:
            cbench = _cbench_dir(task_id)
            rbench = _rbench_dir(task_id)

            # 1. Stage complete C sources under c_source/
            dest_c = ws / "c_source"
            dest_c.mkdir(parents=True, exist_ok=True)
            for f in sorted(cbench.rglob("*")):
                if not f.is_file() or ".git" in f.parts:
                    continue
                target = dest_c / f.relative_to(cbench)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)

            # 2. Stage Cargo project manifest & lock
            shutil.copy2(rbench / "Cargo.toml", ws / "Cargo.toml")
            if (rbench / "Cargo.lock").is_file():
                shutil.copy2(rbench / "Cargo.lock", ws / "Cargo.lock")

            # 3. Stage interface modules into src/
            ws_src = ws / "src"
            ws_src.mkdir(parents=True, exist_ok=True)
            iface_dir = rbench / "src" / "interfaces"
            if iface_dir.is_dir():
                for f in sorted(iface_dir.rglob("*.rs")):
                    if not f.is_file():
                        continue
                    target = ws_src / f.relative_to(iface_dir)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, target)

            # 4. Stage src/lib.rs according to 3-tier policy
            pristine_lib = rbench / "src" / "lib.rs"
            if pristine_lib.is_file():
                if rbench.name in _HELPER_LIBS:
                    mod_lines = [
                        line
                        for line in pristine_lib.read_text(encoding="utf-8").splitlines()
                        if line.strip().startswith("pub mod ")
                    ]
                    (ws_src / "lib.rs").write_text("\n".join(mod_lines) + "\n", encoding="utf-8")
                else:
                    shutil.copy2(pristine_lib, ws_src / "lib.rs")

            # 5. Install harness (AGENTS.md, etc.) onto ws
            self.substrate.install(install, ws)

            prompt = self.task_prompt(task_id)
            stream = run_dir / "omp_events.jsonl"

            run = self.substrate.run(
                prompt,
                ws,
                model=config.SOLVER_MODEL_OMP,
                timeout=timeout,
                stream=stream,
                thinking="high",
                env=os.environ,
            )

            # 6. Collect candidate Rust files from ws/src preserving relative paths
            for src in ws_src.rglob("*.rs"):
                if "target" not in src.parts:
                    rel = src.relative_to(ws_src)
                    dest = run_dir / "src" / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)

            if run.exit_code != 0 or run.timed_out:
                print(
                    f"  [crust-omp] {run_id} exited {run.exit_code}, timed_out={run.timed_out}",
                    flush=True,
                )
        finally:
            shutil.rmtree(ws, ignore_errors=True)

        return run_dir

    def delivered(self, run_dir: Path) -> bool:
        """Did the rollout produce actual modified Rust code beyond unchanged stubs?"""
        return _is_delivery(Path(run_dir))

    def trajectory(self, run_dir: Path, *, obs_trunc: int) -> str:
        stream = Path(run_dir) / "omp_events.jsonl"
        if not stream.is_file():
            return f"(no trajectory recorded for {Path(run_dir).name})"
        return self.substrate.read_trajectory(stream, obs_trunc=obs_trunc, max_chars=10**9)

    def deliverable_files(self, run_dir: Path) -> dict[str, str]:
        """relative_path -> Rust source content."""
        files = {}
        src_dir = Path(run_dir) / "src"
        search_root = src_dir if src_dir.is_dir() else Path(run_dir)
        for p in search_root.rglob("*.rs"):
            if "target" not in p.parts and "src/bin" not in p.as_posix():
                rel = p.relative_to(search_root).as_posix()
                try:
                    files[rel] = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    files[rel] = "(unreadable)"
        return files

    def deliverable_text(self, run_dir: Path) -> str:
        """Concatenated Rust source."""
        files = self.deliverable_files(run_dir)
        return "\n\n".join(f"// {name}\n{content}" for name, content in sorted(files.items()))

    def base_harness(self) -> Path:
        """H0 baseline harness on OMP_SURFACE."""
        d = self.spec.runs_root / f"_base_harness_{self.substrate.name}_{os.getpid()}"
        with _BASE_LOCK:
            if d not in _BASE_DONE:
                HT.write_tree(
                    OMP_SURFACE,
                    {
                        "AGENTS.md": (
                            "Transpile the C code in `c_source/` into safe, idiomatic Rust. "
                            "Implement the module interfaces under `src/` to satisfy the crate specifications. "
                            "Do not use `unsafe` blocks. Ensure your implementation compiles cleanly with `cargo check`."
                        )
                    },
                    d,
                    stubs=True,
                )
                _BASE_DONE.add(d)
        return d

    def validate_tree(self, tree: dict) -> None:
        """No special CRUST-specific invariants."""
        pass

    def preflight(self) -> None:
        """Check Rust toolchain and dataset presence."""
        self.substrate.preflight()

        if not shutil.which("cargo"):
            raise RuntimeError(
                "Rust toolchain (cargo) not found on PATH; install via rustup or set PATH"
            )

        cbench = config.crust_repo() / "datasets" / "CBench"
        rbench = config.crust_repo() / "datasets" / "RBench"
        if not cbench.is_dir() or not rbench.is_dir():
            raise RuntimeError(
                f"CRUST datasets missing at {config.crust_repo()}/datasets/; "
                f"run harness2-setup crust"
            )

        projects = [d.name for d in cbench.iterdir() if d.is_dir()]
        if len(projects) < 50:
            print(
                f"  [crust] WARNING: only {len(projects)} projects found in CBench/; expected ~100",
                flush=True,
            )

    def score(self, run_dir: Path, task_id: str) -> dict | None:
        """Run cargo test on assembled Rust project; return pass/fail counts."""
        cache_key = f"{run_dir.resolve()}::{task_id}"
        with self._judge_lock:
            if cache_key in self._judge_cache:
                return self._judge_cache[cache_key]

        if not self.delivered(run_dir):
            result = {"n_passed": 0, "n_criteria": 0, "all_pass": False, "no_output": True}
            with self._judge_lock:
                self._judge_cache[cache_key] = result
            return result

        result = self._run_cargo_test(run_dir, task_id)
        with self._judge_lock:
            self._judge_cache[cache_key] = result
        return result

    def _run_cargo_test(self, run_dir: Path, task_id: str) -> dict | None:
        """Assemble pristine RBench project, overlay candidate implementation, and run cargo test."""
        rbench = _rbench_dir(task_id)
        if not rbench.is_dir():
            print(f"  [crust] RBench missing for {task_id}; judge failed", flush=True)
            return None

        with tempfile.TemporaryDirectory(prefix="crust-judge-") as tmp:
            proj = Path(tmp) / "project"
            proj.mkdir()

            # 1. Copy pristine Cargo.toml and Cargo.lock
            shutil.copy2(rbench / "Cargo.toml", proj / "Cargo.toml")
            if (rbench / "Cargo.lock").is_file():
                shutil.copy2(rbench / "Cargo.lock", proj / "Cargo.lock")

            proj_src = proj / "src"
            proj_src.mkdir(parents=True, exist_ok=True)

            # 2. Copy pristine test files (src/bin)
            shutil.copytree(rbench / "src" / "bin", proj_src / "bin")

            # 3. Copy pristine lib.rs
            pristine_lib = rbench / "src" / "lib.rs"
            shutil.copy2(pristine_lib, proj_src / "lib.rs")

            # 4. Copy pristine interface scaffolds as fallback baseline
            iface_dir = rbench / "src" / "interfaces"
            if iface_dir.is_dir():
                for f in sorted(iface_dir.rglob("*.rs")):
                    if f.is_file():
                        dest = proj_src / f.relative_to(iface_dir)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, dest)

            # 5. Overlay candidate implementation files from run_dir/src
            candidate_src = Path(run_dir) / "src"
            search_root = candidate_src if candidate_src.is_dir() else Path(run_dir)
            for src_file in sorted(search_root.rglob("*.rs")):
                if not src_file.is_file() or "target" in src_file.parts:
                    continue
                rel = src_file.relative_to(search_root)
                # Protect trusted test namespace: candidate cannot write into src/bin
                if rel.parts and rel.parts[0] == "bin":
                    continue
                # Handle lib.rs overlay: only allow for _ROOT_IMPLEMENTATION_LIBS
                if rel.as_posix() == "lib.rs":
                    if rbench.name in _ROOT_IMPLEMENTATION_LIBS:
                        cand_text = src_file.read_text(encoding="utf-8", errors="replace")
                        pristine_mods = [
                            line
                            for line in pristine_lib.read_text(encoding="utf-8").splitlines()
                            if line.strip().startswith("pub mod ")
                        ]
                        missing_mods = [m for m in pristine_mods if m not in cand_text]
                        if missing_mods:
                            cand_text = "\n".join(missing_mods) + "\n" + cand_text
                        (proj_src / "lib.rs").write_text(cand_text, encoding="utf-8")
                    continue

                dest = proj_src / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest)

            # 6. Determine test command based on whether Cargo.toml defines [[test]]
            has_tests = False
            try:
                data = tomllib.loads((proj / "Cargo.toml").read_text(encoding="utf-8"))
                has_tests = bool(data.get("test"))
            except Exception:
                has_tests = False

            cmd = (
                ["cargo", "test", "--test", "*", "--no-fail-fast", "--", "--nocapture"]
                if has_tests
                else ["cargo", "test", "--bins", "--no-fail-fast", "--", "--nocapture"]
            )

            # Enforce forbid(unsafe_code) through rustc compiler lint
            test_env = os.environ.copy()
            test_env["RUSTFLAGS"] = "-F unsafe_code"

            try:
                result = subprocess.run(
                    cmd,
                    cwd=proj,
                    capture_output=True,
                    text=True,
                    timeout=600,
                    env=test_env,
                )
                output = result.stdout + "\n" + result.stderr
            except (subprocess.TimeoutExpired, OSError) as exc:
                print(f"  [crust] cargo test failed for {task_id}: {exc}", flush=True)
                return None

            # 7. Parse test results
            passed, failed = 0, 0
            for line in output.splitlines():
                if "test result:" in line:
                    m = re.search(r"(\d+)\s+passed;\s*(\d+)\s+failed;", line)
                    if m:
                        passed += int(m.group(1))
                        failed += int(m.group(2))

            total = passed + failed
            if total == 0:
                if result.returncode != 0:
                    return {
                        "n_passed": 0,
                        "n_criteria": 1,
                        "all_pass": False,
                        "compile_failed": True,
                    }
                return {
                    "n_passed": 0,
                    "n_criteria": 0,
                    "all_pass": False,
                    "no_tests": True,
                }

            return {
                "n_passed": passed,
                "n_criteria": total,
                "all_pass": (passed == total and passed > 0),
                "metric": "test_pass_rate",
            }


__all__ = ["CrustAdapter", "crust_spec", "crust_prompts", "CRUST_BASE"]
