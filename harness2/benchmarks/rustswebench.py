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

"""Rust-SWE-bench adapter for repository-level Rust issue resolution tasks."""

from __future__ import annotations

import json
from pathlib import Path

from .. import config
from ..core import tree as HT
from ..core.spec import BenchPrompts, BenchSpec, resolve_channel_model
from ..substrate.base import Install
from ..substrate.codex import CODEX_SURFACE, CodexSubstrate
from ..substrate.omp import OMP_SURFACE, OmpSubstrate
from ..substrate.opencode import OPENCODE_SURFACE, OpencodeSubstrate
from .tasks import discover, select

RSWE_BASE = BenchPrompts(
    work=(
        "Repository-level Rust software engineering: diagnose and resolve a reported issue in "
        "an open-source Rust codebase by reading the problem statement, exploring the repository, "
        "locating relevant code, understanding the failure, implementing a minimal fix, and "
        "verifying the solution against existing tests. The fix must resolve the issue without "
        "breaking other functionality."
    ),
    domain_word="repository",
    deliverable_word="patch",
    inv_levers=(
        "- read the full problem statement and hints before exploring the codebase\n"
        "- identify test files that demonstrate the failure\n"
        "- trace from test invocations to the implementation being tested\n"
        "- reproduce the issue locally before editing\n"
        "- implement the minimal code change addressing the root cause\n"
        "- verify the fix resolves the reported failure without breaking passing tests"
    ),
    dom_levers=(
        "- understand Rust ownership, borrowing, lifetimes, trait bounds, and type inference\n"
        "- distinguish compile-time errors from runtime panics and logic bugs\n"
        "- check module structure, visibility rules, and dependency constraints\n"
        "- preserve API contracts, error-handling patterns, and edge-case coverage"
    ),
    yardstick=(
        "Did the agent understand the failure mechanism, produce a focused patch addressing the "
        "root cause, and verify that the originally failing tests now pass?"
    ),
    selection_checks=(
        "Prefer the fix that directly addresses the root cause; correctly handles the reported "
        "failure; maintains API contracts and test coverage; uses idiomatic Rust; and includes "
        "verification that the originally failing tests now pass."
    ),
)


def rswe_spec(substrate_name: str) -> BenchSpec:
    install_mode = {"oc": "workspace_config", "cx": "codex_root", "omp": "omp_root"}
    if substrate_name not in install_mode:
        raise ValueError(f"substrate must be one of {tuple(install_mode)}, got {substrate_name!r}")
    channel = resolve_channel_model(None, None, effort="high")
    return BenchSpec(
        name="rswe",
        runs_root=config.RUNS / "rswe",
        install_mode=install_mode[substrate_name],
        prompts=RSWE_BASE,
        channels={"proposer": channel, "selector": channel},
        domain_word="repository",
        leak_globs=("patch", "test_patch", "FAIL_TO_PASS", "PASS_TO_PASS"),
        allow_subagents=True,
        proposer_deliverables="contents",
        obs_trunc=50_000,
    )


class RustSWEBenchAdapter:
    """Task discovery and prompt adapter for user2f86/rustbench (500 train instances).

    Full Docker validation remains in the upstream GhabiX/Rust-SWE-Bench harness; harness2's
    non-evaluation integration intentionally exposes discovery and task context only.
    """

    def __init__(self, *, substrate: str = "oc", split_file: Path | None = None):
        self.split_file = split_file
        self.spec = rswe_spec(substrate)
        if substrate == "oc":
            self.substrate = OpencodeSubstrate(launcher=self._launch_oc)
        elif substrate == "cx":
            self.substrate = CodexSubstrate(launcher=self._launch_cx)
        else:
            self.substrate = OmpSubstrate(launcher=self._launch_omp)
        self._dataset: dict[str, dict] | None = None

    def tasks(self, split: str = "all") -> list[str]:
        return select(discover("rswe"), split, self.split_file, benchmark="rswe")

    def domain_of(self, task_id: str) -> str:
        return task_id.split("__", 1)[0] if "__" in task_id else task_id

    def reference_domain_order(self) -> list[str]:
        return sorted(set(discover("rswe").values()))

    def prompts_for(self, task_id: str) -> BenchPrompts:
        return RSWE_BASE

    def task_prompt(self, task_id: str) -> str:
        instance = self._load_instance(task_id)
        parts = [f"# Issue: {task_id}"]
        if repo := instance.get("repo"):
            parts.append(f"**Repository:** {repo}")
        if version := instance.get("version"):
            parts.append(f"**Version:** {version}")
        if problem := instance.get("problem_statement"):
            parts.append(f"## Problem Statement\n\n{problem.strip()}")
        if hints := instance.get("hints_text"):
            parts.append(f"## Hints\n\n{hints.strip()}")
        return "\n\n".join(parts)

    def task_files(self, task_id: str) -> Path | None:
        return None

    def _load_instance(self, task_id: str) -> dict:
        if self._dataset is None:
            self._dataset = {}
            root = config.DEPENDENCIES / "rustbench"
            files = sorted(root.glob("**/*.jsonl"))
            if files:
                for path in files:
                    for line in path.read_text(encoding="utf-8").splitlines():
                        if line.strip():
                            obj = json.loads(line)
                            if obj.get("instance_id"):
                                self._dataset[obj["instance_id"]] = obj
            else:
                files = sorted(root.glob("**/*.json"))
                if files:
                    for path in files:
                        value = json.loads(path.read_text(encoding="utf-8"))
                        for obj in value if isinstance(value, list) else [value]:
                            if obj.get("instance_id"):
                                self._dataset[obj["instance_id"]] = obj
                else:
                    files = sorted(root.glob("**/*.parquet"))
                    if files:
                        try:
                            import pyarrow.parquet as pq
                        except ImportError as exc:
                            raise RuntimeError(
                                "Parquet dataset requires pyarrow; rerun harness2-setup rswe"
                            ) from exc
                        for path in files:
                            for obj in pq.read_table(path).to_pylist():
                                if obj.get("instance_id"):
                                    self._dataset[obj["instance_id"]] = obj
            if not self._dataset:
                raise FileNotFoundError(
                    f"Rust-SWE-bench dataset missing or empty under {root}; "
                    "run harness2-setup rswe"
                )
        try:
            return self._dataset[task_id]
        except KeyError as exc:
            raise ValueError(f"task {task_id!r} not found in rustbench dataset") from exc

    def execute(self, task_id: str, harness_dir: Path | None, run_id: str, *, timeout: int | None = None) -> Path:
        raise NotImplementedError(
            "Rust-SWE-bench execution requires the upstream Docker validation harness; "
            "this integration is discovery-only"
        )

    def _launch_oc(self, req, install: Install) -> list[Path]:
        raise NotImplementedError("rswe execution is provided by the upstream harness")

    def _launch_cx(self, req, install: Install) -> list[Path]:
        raise NotImplementedError("rswe execution is provided by the upstream harness")

    def _launch_omp(self, req, install: Install) -> list[Path]:
        raise NotImplementedError("rswe execution is provided by the upstream harness")

    def delivered(self, run_dir: Path) -> bool:
        patch = Path(run_dir) / "patch.diff"
        return patch.is_file() and patch.stat().st_size > 0

    def trajectory(self, run_dir: Path, *, obs_trunc: int) -> str:
        return "(trajectory extraction not implemented for rswe)"

    def deliverable_files(self, run_dir: Path) -> dict[str, str]:
        patch = Path(run_dir) / "patch.diff"
        return {"patch.diff": patch.read_text(encoding="utf-8", errors="replace")} if patch.is_file() else {}

    def deliverable_text(self, run_dir: Path) -> str:
        files = self.deliverable_files(run_dir)
        return files.get("patch.diff", "")

    def base_harness(self) -> Path:
        d = self.spec.runs_root / f"_base_harness_{self.substrate.name}"
        if not d.exists():
            surface = OPENCODE_SURFACE if self.substrate.name == "oc" else CODEX_SURFACE if self.substrate.name == "cx" else OMP_SURFACE
            files = ({
                "systemprompt.md": "Read the Rust issue, explore the repository, implement and verify a focused fix.",
                "guardrails.md": "", "LongTermMEMORY.md": "", "tool_descriptions/tool_guidance.md": "",
            } if self.substrate.name == "oc" else {
                "AGENTS.md": "Read the Rust issue, explore the repository, implement and verify a focused fix."
            })
            HT.write_tree(surface, files, d, stubs=True)
        return d

    def validate_tree(self, tree: dict[str, str]) -> None:
        return None

    def preflight(self) -> None:
        tasks = discover("rswe")
        if len(tasks) != 500:
            raise RuntimeError(f"expected 500 Rust-SWE-bench tasks, found {len(tasks)}")

    def score(self, run_dir: Path, task_id: str) -> dict | None:
        raise NotImplementedError("Rust-SWE-bench scoring requires the upstream Docker validation harness")
