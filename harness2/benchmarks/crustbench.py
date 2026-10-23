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

import json
import os
import shutil
import subprocess
import tempfile
import threading
from dataclasses import replace
from pathlib import Path

from .. import config
from ..core import runmark as RM
from ..core.spec import BenchPrompts, BenchSpec, resolve_channel_model
from ..substrate.codex import CodexSubstrate
from ..substrate.omp import OmpSubstrate
from ..substrate.opencode import OpencodeSubstrate
from ..substrate.base import Install, RunRequest
from .tasks import discover, select

_TIMEOUT_DEFAULT = {"oc": 3600, "cx": 3600, "omp": 3600}

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
    install_mode = {"oc": "workspace_config", "cx": "codex_root", "omp": "omp_root"}
    if substrate not in install_mode:
        raise ValueError(f"substrate must be one of {tuple(install_mode)}, got {substrate!r}")
    channel = resolve_channel_model(None, None, effort="high")
    return BenchSpec(
        name="crust",
        runs_root=config.RUNS / "crust",
        install_mode=install_mode[substrate],
        prompts=CRUST_BASE,
        channels={"proposer": channel, "selector": channel},
        domain_word="category",
        leak_globs=("RBench/*/bin/**", "RBench/*/tests/**"),
        allow_subagents=False,
        proposer_deliverables="contents",
        obs_trunc=50_000,
    )


def _compose_task_prompt(task_id: str) -> str:
    """Build CRUST task prompt: C sources + Rust interface spec + instruction."""
    cbench = config.crust_repo() / "datasets" / "CBench" / task_id
    rbench = config.crust_repo() / "datasets" / "RBench" / task_id
    
    if not cbench.is_dir():
        raise FileNotFoundError(f"C sources missing for {task_id}: {cbench}")
    if not rbench.is_dir():
        raise FileNotFoundError(f"Rust interfaces missing for {task_id}: {rbench}")
    
    parts = [f"# C-to-Rust Transpilation Task: {task_id}\n"]
    
    # Collect C sources
    c_files = sorted(cbench.rglob("*.c")) + sorted(cbench.rglob("*.h"))
    if c_files:
        parts.append("## Original C Sources\n")
        for cf in c_files[:20]:  # Cap at 20 files
            rel = cf.relative_to(cbench)
            try:
                content = cf.read_text(encoding="utf-8", errors="replace")
                parts.append(f"### {rel}\n```c\n{content[:8000]}\n```\n")
            except OSError:
                parts.append(f"### {rel}\n(unreadable)\n")
    
    # Collect Rust interface specifications
    iface_dir = rbench / "interfaces"
    if iface_dir.is_dir():
        rs_files = sorted(iface_dir.glob("*.rs"))
        if rs_files:
            parts.append("## Required Rust Interface Specifications\n")
            parts.append("Implement these function signatures in safe Rust:\n\n")
            for rf in rs_files:
                rel = rf.relative_to(rbench)
                try:
                    content = rf.read_text(encoding="utf-8", errors="replace")
                    parts.append(f"### {rel}\n```rust\n{content}\n```\n")
                except OSError:
                    parts.append(f"### {rel}\n(unreadable)\n")
    
    # List test files (not included in prompt to avoid leaking expected behavior)
    test_dir = rbench / "bin"
    if test_dir.is_dir():
        test_files = list(test_dir.glob("*.rs"))
        if test_files:
            parts.append(f"\n## Test Suite\n{len(test_files)} test(s) will validate your implementation.\n")
    
    parts.append("\n## Instructions\n")
    parts.append("""\
Transpile the C code into safe, idiomatic Rust that:
1. Implements every function in the interface specifications
2. Maintains the original C semantics
3. Uses safe Rust (avoid `unsafe` unless the interface requires it)
4. Compiles without errors
5. Passes all provided tests

Deliver your implementation as complete Rust source files (.rs) matching the interface structure.""")
    
    return "\n".join(parts)


class CrustAdapter:
    """CRUST-Bench behind the BenchmarkAdapter protocol, on any substrate."""
    
    def __init__(
        self,
        substrate: str = "oc",
        *,
        timeout: int | None = None,
        split_file: Path | None = None,
    ):
        self.split_file = split_file
        self.spec = crust_spec(substrate)
        launcher_map = {
            "oc": (self._launch_oc, OpencodeSubstrate),
            "cx": (self._launch_cx, CodexSubstrate),
            "omp": (self._launch_omp, OmpSubstrate),
        }
        launcher, cls = launcher_map[substrate]
        self.substrate = cls(launcher=launcher)
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
        d = config.crust_repo() / "datasets" / "CBench" / task_id
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
            print(f"  [crust] {run_id} produced no Rust files; left unmarked", flush=True)
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
    
    def _launch_oc(self, req: RunRequest, install: Install) -> list[Path]:
        """OpenCode launcher: direct bun run."""
        dirs = []
        for run_id in req.run_ids:
            run_dir = self._run_dir(run_id).resolve()
            run_dir.mkdir(parents=True, exist_ok=True)
            ws = Path(tempfile.mkdtemp(prefix="crust-oc-"))
            try:
                if install.extras.get("harness") != "base":
                    for entry in install.staging_dir.iterdir():
                        dest = ws / entry.name
                        if entry.is_dir():
                            shutil.copytree(entry, dest)
                        else:
                            shutil.copy2(entry, dest)
                
                prompt = self.task_prompt(req.task_ref)
                stream = run_dir / "opencode_session.jsonl"
                argv = self.substrate.run_argv(
                    prompt, ws, config.SOLVER_MODEL_OC, title=run_id, session=str(stream)
                )
                env = self.substrate.run_env(os.environ, ws)
                
                subprocess.run(
                    argv, cwd=ws, env=env, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=req.timeout + 300
                )
                
                # Collect Rust outputs
                for src in ws.rglob("*.rs"):
                    if "target/" not in src.parts:  # Skip cargo build artifacts
                        dest = run_dir / src.relative_to(ws)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dest)
            finally:
                shutil.rmtree(ws, ignore_errors=True)
            dirs.append(run_dir)
        return dirs
    
    def _launch_cx(self, req: RunRequest, install: Install) -> list[Path]:
        """Codex launcher: direct codex exec."""
        dirs = []
        for run_id in req.run_ids:
            run_dir = self._run_dir(run_id).resolve()
            run_dir.mkdir(parents=True, exist_ok=True)
            ws = Path(tempfile.mkdtemp(prefix="crust-cx-"))
            try:
                # Install harness to workspace root
                for entry in install.staging_dir.iterdir():
                    dest = ws / entry.name
                    if entry.is_dir():
                        shutil.copytree(entry, dest)
                    else:
                        shutil.copy2(entry, dest)
                
                prompt = self.task_prompt(req.task_ref)
                stream = run_dir / "codex_session.jsonl"
                argv = self.substrate.exec_argv(prompt, ws, config.SOLVER_MODEL_CX, reasoning_effort="high")
                env = self.substrate.exec_env(os.environ, codex_home=config.CODEX_HOME_DIR)
                
                # Capture session to stream
                with stream.open("w", encoding="utf-8") as out:
                    subprocess.run(
                        argv, cwd=ws, env=env, stdin=subprocess.DEVNULL,
                        stdout=out, stderr=subprocess.DEVNULL,
                        timeout=req.timeout + 300
                    )
                
                # Collect Rust outputs
                for src in ws.rglob("*.rs"):
                    if "target/" not in src.parts:
                        dest = run_dir / src.relative_to(ws)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dest)
            finally:
                shutil.rmtree(ws, ignore_errors=True)
            dirs.append(run_dir)
        return dirs
    
    def _launch_omp(self, req: RunRequest, install: Install) -> list[Path]:
        """OMP launcher: direct omp runtime."""
        base = install.extras.get("harness") == "base"
        if base:
            install = self.substrate.materialise(install.staging_dir, self.spec, {})
        try:
            return [self._roll_omp(req.task_ref, run_id, install, req.timeout) for run_id in req.run_ids]
        finally:
            if base:
                shutil.rmtree(install.staging_dir, ignore_errors=True)
    
    def _roll_omp(self, task_id: str, run_id: str, install: Install, timeout: int) -> Path:
        run_dir = self._run_dir(run_id).resolve()
        run_dir.mkdir(parents=True, exist_ok=True)
        ws = Path(tempfile.mkdtemp(prefix="crust-omp-"))
        try:
            self.substrate.install(install, ws)
            prompt = self.task_prompt(task_id)
            stream = run_dir / "omp_events.jsonl"
            
            run = self.substrate.run(
                prompt, ws, model=config.SOLVER_MODEL_OMP,
                timeout=timeout, stream=stream, thinking="high", env=os.environ
            )
            
            # Collect Rust outputs
            for src in ws.rglob("*.rs"):
                if "target/" not in src.parts:
                    dest = run_dir / src.relative_to(ws)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
            
            if run.exit_code != 0 or run.timed_out:
                print(f"  [crust-omp] {run_id} exited {run.exit_code}, timed_out={run.timed_out}", flush=True)
        finally:
            shutil.rmtree(ws, ignore_errors=True)
        
        return run_dir
    
    def delivered(self, run_dir: Path) -> bool:
        """Did the rollout produce at least one Rust file?"""
        return any(Path(run_dir).glob("**/*.rs"))
    
    def trajectory(self, run_dir: Path, *, obs_trunc: int) -> str:
        name = {
            "oc": "opencode_session.jsonl",
            "cx": "codex_session.jsonl",
            "omp": "omp_events.jsonl",
        }[self.substrate.name]
        stream = Path(run_dir) / name
        if not stream.is_file():
            return f"(no trajectory recorded for {Path(run_dir).name})"
        return self.substrate.read_trajectory(stream, obs_trunc=obs_trunc, max_chars=10**9)
    
    def deliverable_files(self, run_dir: Path) -> dict[str, str]:
        """filename -> Rust source content."""
        files = {}
        for p in Path(run_dir).glob("**/*.rs"):
            if "target/" not in p.parts:
                try:
                    files[p.name] = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    files[p.name] = "(unreadable)"
        return files
    
    def deliverable_text(self, run_dir: Path) -> str:
        """Concatenated Rust source."""
        files = self.deliverable_files(run_dir)
        return "\n\n".join(f"// {name}\n{content}" for name, content in sorted(files.items()))
    
    def base_harness(self) -> Path:
        """Minimal AGENTS.md baseline."""
        base = config.THIRD_PARTY / "crust_runner" / "base"
        if not base.is_dir():
            base.mkdir(parents=True, exist_ok=True)
            (base / "AGENTS.md").write_text(
                "You are a C-to-Rust transpilation specialist. Follow the task instructions.\n",
                encoding="utf-8"
            )
        return base
    
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
        
        # Quick task count check
        projects = [d.name for d in cbench.iterdir() if d.is_dir()]
        if len(projects) < 50:
            print(
                f"  [crust] WARNING: only {len(projects)} projects found in CBench/; "
                f"expected ~100", flush=True
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
        """Assemble Rust project and run cargo test."""
        rbench = config.crust_repo() / "datasets" / "RBench" / task_id
        if not rbench.is_dir():
            print(f"  [crust] RBench missing for {task_id}; judge failed", flush=True)
            return None
        
        # Build temporary Cargo project
        with tempfile.TemporaryDirectory(prefix="crust-judge-") as tmp:
            proj = Path(tmp) / "project"
            proj.mkdir()
            src_dir = proj / "src"
            src_dir.mkdir()
            
            # Copy transpiled sources
            for src in Path(run_dir).glob("**/*.rs"):
                if "target/" not in src.parts:
                    dest = src_dir / src.name
                    shutil.copy2(src, dest)
            
            # Copy test files
            tests_dir = proj / "tests"
            tests_dir.mkdir()
            test_src = rbench / "bin"
            if test_src.is_dir():
                for test_file in test_src.glob("*.rs"):
                    shutil.copy2(test_file, tests_dir / test_file.name)
            
            # Generate Cargo.toml
            manifest = proj / "Cargo.toml"
            manifest.write_text(f"""\
[package]
name = "crust_task_{task_id.replace('/', '_').replace('-', '_')}"
version = "0.1.0"
edition = "2021"

[dependencies]
""", encoding="utf-8")
            
            # Run cargo test
            try:
                result = subprocess.run(
                    ["cargo", "test", "--manifest-path", str(manifest), "--", "--nocapture"],
                    cwd=proj,
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
                output = result.stdout + result.stderr
            except (subprocess.TimeoutExpired, OSError) as exc:
                print(f"  [crust] cargo test failed for {task_id}: {exc}", flush=True)
                return None
            
            # Parse test output
            passed, failed, total = 0, 0, 0
            for line in output.splitlines():
                if "test result:" in line:
                    # Example: "test result: ok. 5 passed; 0 failed; 0 ignored"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed;":
                            passed = int(parts[i - 1])
                        elif part == "failed;":
                            failed = int(parts[i - 1])
            
            total = passed + failed
            if total == 0:
                # Compilation likely failed
                if result.returncode != 0:
                    return {"n_passed": 0, "n_criteria": 1, "all_pass": False, "compile_failed": True}
                return None
            
            return {
                "n_passed": passed,
                "n_criteria": total,
                "all_pass": passed == total,
                "metric": "test_pass_rate",
            }


__all__ = ["CrustAdapter", "crust_spec", "crust_prompts", "CRUST_BASE"]
