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

"""AgentRE-Bench adapter for long-horizon reverse engineering tasks."""

from __future__ import annotations

import json
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

AGENTRE_BASE = BenchPrompts(
    work=(
        "Analyze this compiled binary using static reverse engineering tools. "
        "The binary is provided without source code or meaningful filenames. "
        "Use the available toolset to identify behavior, extract configuration details, "
        "and document techniques. Submit structured findings."
    ),
    domain_word="binary",
    deliverable_word="analysis",
    inv_levers=(
        "Static analysis tools are available: file, strings, readelf/pe_info, objdump, "
        "nm, hexdump, and entropy. Use them systematically to understand the program. "
        "Follow references across tool outputs."
    ),
    dom_levers=(
        "Look for encoded strings, API calls, control flow patterns, anti-analysis checks, "
        "encryption artifacts, and network configuration. Cross-reference findings."
    ),
    yardstick=(
        "Structured answer fields are validated against ground truth. "
        "Exact matches for scalars; Jaccard overlap for technique sets. "
        "Unsupported technique claims carry a penalty."
    ),
    selection_checks=(
        "Verify binary type and available analysis tools before proceeding. "
        "Budget tool calls carefully; complex binaries may require multiple passes."
    ),
)


def _repo() -> Path:
    """Return AgentRE-Bench checkout without requiring config helper to exist."""
    helper = getattr(config, "agentre_repo", None)
    return Path(helper()) if callable(helper) else config.DEPENDENCIES / "AgentRE-Bench"


def agentre_spec(substrate_name: str) -> BenchSpec:
    """Static AgentRE-Bench specification for one substrate cell."""
    install_mode = {"oc": "workspace_config", "cx": "codex_root", "omp": "omp_root"}
    channel = resolve_channel_model(None, None, effort="high")
    return BenchSpec(
        name="agentre",
        runs_root=config.RUNS / "agentre",
        install_mode=install_mode[substrate_name],
        prompts=AGENTRE_BASE,
        channels={"proposer": channel, "selector": channel},
        domain_word="binary",
        leak_globs=("**/ground_truths/**",),
        allow_subagents=False,
        obs_trunc=50_000,
    )


@lru_cache(maxsize=1)
def _ground_truths() -> dict[str, dict]:
    """Load ground truth metadata for task discovery and validation."""
    repo = _repo()
    gt_dir = repo / "ground_truths"
    if not gt_dir.is_dir():
        return {}
    out = {}
    for path in sorted(gt_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        task_id = path.stem
        out[task_id] = data
    return out


def discover() -> dict[str, str]:
    """Discover AgentRE-Bench tasks from ground truth files.
    
    Returns mapping of task_id -> domain classification.
    ELF levels (1-13) map to 'elf-re', PE levels (14-23) map to 'pe-re'.
    """
    tasks = _ground_truths()
    if not tasks:
        return {}
    result = {}
    for task_id in tasks:
        # Infer domain from level naming: levelN_description
        if task_id.startswith("level"):
            try:
                level_num = int(task_id.split("_")[0].replace("level", ""))
                domain = "pe-re" if level_num >= 14 else "elf-re"
            except (ValueError, IndexError):
                domain = "reverse-engineering"
        else:
            domain = "reverse-engineering"
        result[task_id] = domain
    return result


class AgentREAdapter:
    """Task discovery and execution adapter for AgentRE-Bench reverse engineering tasks.
    
    AgentRE-Bench provides 23 levels: 13 Linux ELF (levels 1-13) and 10 Windows PE
    (levels 14-23, with stripped/unstripped pairs). Tasks cover reverse shells,
    covert channels, process injection, anti-analysis, and obfuscation techniques.
    """

    def __init__(self, substrate: str, *, split_file: Path | None = None):
        if substrate not in ("oc", "cx", "omp"):
            raise ValueError(f"AgentRE-Bench does not support substrate {substrate!r}")
        self.spec = agentre_spec(substrate)
        self.substrate = {
            "oc": OpencodeSubstrate(OPENCODE_SURFACE),
            "cx": CodexSubstrate(CODEX_SURFACE),
            "omp": OmpSubstrate(OMP_SURFACE),
        }[substrate]
        self._split_file = split_file
        self._prompts = AGENTRE_BASE

    def tasks(self, split: str = "all") -> list[str]:
        """Return selected discovered task IDs for the requested split."""
        return select(discover(), split, self._split_file, benchmark="agentre")

    def selection(self, split: str = "all") -> list[str]:
        """Backward-compatible alias for task selection."""
        return self.tasks(split)

    def prompts(self, task_id: str) -> BenchPrompts:
        """Return the reverse engineering prompt profile."""
        return self._prompts

    def tree(self, task_id: str, *, channel: str = "") -> HT.Node:
        """Build the task workspace tree for a reverse engineering binary."""
        repo = _repo()
        gt = _ground_truths().get(task_id)
        if not gt:
            raise ValueError(f"Task {task_id} not found in ground truths")
        
        # AgentRE-Bench binaries are in binaries/ directory
        binary_name = f"{task_id}.bin"
        binary_path = repo / "binaries" / binary_name
        if not binary_path.exists():
            # Try alternate naming schemes
            for candidate in repo.glob(f"binaries/{task_id}*"):
                if candidate.is_file():
                    binary_path = candidate
                    break
        
        if not binary_path.exists():
            raise FileNotFoundError(f"Binary not found for task {task_id}")
        
        # Mount the binary and provide instruction
        instruction = (
            f"Analyze the binary at /workspace/{binary_path.name}.\n"
            "Available tools: file, strings, readelf (ELF) or pe_info (PE), "
            "objdump, nm, hexdump, entropy.\n"
            "Budget: ~25 tool calls. Static analysis only.\n"
            "Submit structured findings with final_answer."
        )
        
        return HT.root(
            HT.file("instruction.md", instruction),
            HT.file(binary_path.name, binary_path),
        )

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
        """AgentRE-Bench tasks do not need adaptation; return empty tree."""
        return HT.root()

    def judge(self, task_id: str, deliverable: HT.Node) -> dict:
        """AgentRE-Bench scoring requires the upstream deterministic scorer."""
        raise NotImplementedError(
            "AgentRE-Bench scoring requires the upstream harness/metrics.py scorer. "
            "See https://github.com/agentrebench/AgentRE-Bench for the scoring implementation."
        )


__all__ = ["AgentREAdapter", "AGENTRE_BASE", "agentre_spec", "discover"]
