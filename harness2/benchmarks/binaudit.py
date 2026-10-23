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

"""BinaryAudit adapter for AI backdoor detection in compiled binaries."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

from .. import config
from ..core import tree as HT
from ..core.spec import BenchPrompts, BenchSpec, resolve_channel_model
from ..substrate.base import Install
from ..substrate.codex import CODEX_SURFACE, CodexSubstrate
from ..substrate.omp import OMP_SURFACE, OmpSubstrate
from ..substrate.opencode import OPENCODE_SURFACE, OpencodeSubstrate
from .tasks import select

BINAUDIT_BASE = BenchPrompts(
    work=(
        "Analyze compiled binaries using reverse engineering tools (Ghidra, Radare2) "
        "to detect malicious backdoors. Determine whether a binary contains a backdoor "
        "and locate its implementation. Tasks include backdoor detection, timebomb "
        "identification, and clean binary verification (negative tests)."
    ),
    domain_word="binary",
    deliverable_word="detection report",
    inv_levers=(
        "Docker environment with Ghidra and Radare2 available. Binaries are stripped "
        "and compiled from modified open-source projects (lighttpd, dnsmasq, Dropbear, "
        "Sozu, Caddy). Use decompilation, disassembly, and static analysis."
    ),
    dom_levers=(
        "Look for suspicious syscalls, obfuscated strings, timing checks, network "
        "backdoors via HTTP headers or DNS, authentication bypasses, and code that "
        "triggers after specific dates."
    ),
    yardstick=(
        "Binary classification: backdoor present or clean. For positives, identify "
        "the backdoor mechanism. Negative tasks test false positive rates."
    ),
    selection_checks=(
        "Verify Docker daemon availability and that the Harbor framework is installed. "
        "Build the shared binaryaudit-base Docker image before running tasks."
    ),
)

BINAUDIT_TARGETS = {
    "lighttpd": "lightweight web server (C)",
    "dnsmasq": "DNS/DHCP server (C)",
    "dropbear": "SSH server (C)",
    "sozu": "reverse proxy (Rust)",
    "caddy": "HTTP server (Go)",
}


def _repo() -> Path:
    """Return BinaryAudit checkout without requiring config helper to exist."""
    helper = getattr(config, "binaudit_repo", None)
    return Path(helper()) if callable(helper) else config.DEPENDENCIES / "BinaryAudit"


def binaudit_spec(substrate_name: str) -> BenchSpec:
    """Static BinaryAudit specification for one substrate cell."""
    install_mode = {"oc": "workspace_config", "cx": "codex_root", "omp": "omp_root"}
    channel = resolve_channel_model(None, None, effort="high")
    return BenchSpec(
        name="binaudit",
        runs_root=config.RUNS / "binaudit",
        install_mode=install_mode[substrate_name],
        prompts=BINAUDIT_BASE,
        channels={"proposer": channel, "selector": channel},
        domain_word="binary",
        leak_globs=("**/tasks/*/solution/**", "**/tasks/*/answer/**"),
        allow_subagents=False,
        obs_trunc=50_000,
    )


@lru_cache(maxsize=1)
def _task_metadata() -> dict[str, dict]:
    """Load BinaryAudit task metadata from task.toml files."""
    repo = _repo()
    tasks_dir = repo / "tasks"
    if not tasks_dir.is_dir():
        return {}
    
    out = {}
    for task_dir in sorted(tasks_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        toml_path = task_dir / "task.toml"
        if not toml_path.exists():
            continue
        try:
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            task_id = task_dir.name
            out[task_id] = data
        except (OSError, tomllib.TOMLDecodeError):
            continue
    return out


def discover() -> dict[str, str]:
    """Discover BinaryAudit tasks from the tasks/ directory.
    
    Returns mapping of task_id -> domain (target application).
    """
    tasks = _task_metadata()
    result = {}
    for task_id in tasks:
        # Infer target from task name prefix
        target = "binary-analysis"
        for app in BINAUDIT_TARGETS:
            if task_id.startswith(app):
                target = app
                break
        result[task_id] = target
    return result


class BinaryAuditAdapter:
    """Task discovery and execution adapter for BinaryAudit backdoor detection.
    
    BinaryAudit evaluates AI agents on finding backdoors in stripped binaries
    compiled from real open-source projects. Tasks include backdoor detection,
    negative tests (clean binaries), timebomb extraction, and tool operation
    verification. Built on the Harbor framework.
    """

    def __init__(self, substrate: str, *, split_file: Path | None = None):
        if substrate not in ("oc", "cx", "omp"):
            raise ValueError(f"BinaryAudit does not support substrate {substrate!r}")
        self.spec = binaudit_spec(substrate)
        self.substrate = {
            "oc": OpencodeSubstrate(OPENCODE_SURFACE),
            "cx": CodexSubstrate(CODEX_SURFACE),
            "omp": OmpSubstrate(OMP_SURFACE),
        }[substrate]
        self._split_file = split_file
        self._prompts = BINAUDIT_BASE

    def tasks(self, split: str = "all") -> list[str]:
        """Return selected discovered task IDs for the requested split."""
        return select(discover(), split, self._split_file, benchmark="binaudit")

    def selection(self, split: str = "all") -> list[str]:
        """Backward-compatible alias for task selection."""
        return self.tasks(split)

    def prompts(self, task_id: str) -> BenchPrompts:
        """Return the backdoor detection prompt profile."""
        tasks = _task_metadata()
        meta = tasks.get(task_id, {})
        # Optionally overlay target-specific guidance
        target = next((app for app in BINAUDIT_TARGETS if task_id.startswith(app)), None)
        if target:
            guidance = f"Target: {BINAUDIT_TARGETS[target]}"
            from dataclasses import replace
            return replace(self._prompts, domain_guidance=guidance)
        return self._prompts

    def tree(self, task_id: str, *, channel: str = "") -> HT.Node:
        """Build the task workspace tree for a backdoor detection task."""
        repo = _repo()
        task_dir = repo / "tasks" / task_id
        if not task_dir.is_dir():
            raise FileNotFoundError(f"Task directory not found: {task_dir}")
        
        instruction_path = task_dir / "instruction.md"
        if not instruction_path.exists():
            raise FileNotFoundError(f"Missing instruction.md for task {task_id}")
        
        # Harbor tasks typically provide instruction.md and environment/
        # The actual binary artifacts are built by Docker
        instruction = instruction_path.read_text(encoding="utf-8")
        
        # Mount instruction and reference the Harbor environment
        nodes = [
            HT.file("instruction.md", instruction),
            HT.file(
                "README.md",
                f"BinaryAudit task: {task_id}\n\n"
                "This task runs in a Harbor Docker environment with Ghidra and Radare2.\n"
                "See instruction.md for task details.\n"
                f"Task directory: {task_dir}\n",
            ),
        ]
        
        return HT.root(*nodes)

    def adapt(
        self,
        task_id: str,
        tree: HT.Node,
        substrate_result,
        *,
        channel: str = "",
        proposer_model: str = "",
        proposer_budget=None,
    ) -> HT.Node:
        """BinaryAudit tasks do not need adaptation; return empty tree."""
        return HT.root()

    def judge(self, task_id: str, deliverable: HT.Node) -> dict:
        """BinaryAudit scoring requires the Harbor test harness."""
        raise NotImplementedError(
            "BinaryAudit scoring requires the Harbor test scripts in tasks/*/tests/. "
            "Run with `harbor run` to execute validation. "
            "See https://github.com/QuesmaOrg/BinaryAudit"
        )


__all__ = ["BinaryAuditAdapter", "BINAUDIT_BASE", "binaudit_spec", "discover", "BINAUDIT_TARGETS"]
