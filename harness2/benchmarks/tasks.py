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

"""Task discovery and optional user-created partitions; no bundled task lists."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from .. import config


def discover(bench: str, subset: str | None = None) -> dict[str, str]:
    """Return sorted task IDs mapped to their dataset-provided domain."""
    if bench == "jb":
        root = config.jb_repo() / "dataset" / "main"
        tasks = {
            p.parent.parent.relative_to(root).as_posix(): p.parent.parent.relative_to(root).parts[0]
            for p in sorted(root.glob("*/*/task_folder/TASK_INSTRUCTIONS.txt"))
        }
    elif bench == "lab":
        root = config.lab_repo() / "tasks"
        tasks = {
            p.parent.relative_to(root).as_posix(): p.parent.relative_to(root).parts[0]
            for p in sorted(root.glob("*/*/task.json"))
        }
    elif bench == "wb" and subset in ("office", "web", "code", "sec"):
        root = config.wb_repo() / "datasets" / f"wb-bench-{subset}-v1.0" / "tasks"
        tasks = {}
        field = "role" if subset == "code" else "category"
        for p in sorted(root.glob("*/task.toml")):
            meta = tomllib.loads(p.read_text(encoding="utf-8")).get("metadata", {})
            domain = meta.get(field)
            if not isinstance(domain, str) or not domain.strip():
                raise ValueError(f"{p}: metadata.{field} must be a nonempty string")
            # Some sec tasks use README.md or steps/ for multi-step scenarios
            has_instruction = (p.parent / "instruction.md").is_file()
            has_readme = (p.parent / "README.md").is_file()
            if not has_instruction and not has_readme and subset != "sec":
                raise FileNotFoundError(f"Missing task instructions: {p.parent / 'instruction.md'}")
            tasks[p.parent.name] = domain.strip()
    elif bench == "cve":
        from .cvebench import discover as cve_discover
        return cve_discover()
    elif bench == "cyber":
        from .cybench import CybenchAdapter
        # Cybench uses custom discovery logic
        repo = config.cyber_repo()
        from .cybench import _task_list
        tasks = {}
        for task_id in _task_list(repo):
            # Domain from metadata; use generic for now
            tasks[task_id] = "ctf"
        return tasks
    elif bench == "rswe":
        # Rust-SWE-bench from Hugging Face dataset
        root = config.DEPENDENCIES / "rustbench"
        tasks = {}
        # Try jsonl first
        files = sorted(root.glob("**/*.jsonl"))
        if files:
            for path in files:
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        obj = json.loads(line)
                        if task_id := obj.get("instance_id"):
                            repo = obj.get("repo", "rust")
                            tasks[task_id] = repo.split("/")[-1] if "/" in repo else repo
        else:
            # Try json
            files = sorted(root.glob("**/*.json"))
            if files:
                for path in files:
                    value = json.loads(path.read_text(encoding="utf-8"))
                    for obj in (value if isinstance(value, list) else [value]):
                        if task_id := obj.get("instance_id"):
                            repo = obj.get("repo", "rust")
                            tasks[task_id] = repo.split("/")[-1] if "/" in repo else repo
            else:
                # Try parquet (requires pyarrow)
                files = sorted(root.glob("**/*.parquet"))
                if files:
                    try:
                        import pyarrow.parquet as pq
                        for path in files:
                            for obj in pq.read_table(path).to_pylist():
                                if task_id := obj.get("instance_id"):
                                    repo = obj.get("repo", "rust")
                                    tasks[task_id] = repo.split("/")[-1] if "/" in repo else repo
                    except ImportError:
                        pass
        if not tasks:
            return {}
        return tasks
    elif bench == "crust":
        from .crustbench import CrustAdapter
        repo = config.crust_repo()
        cbench = repo / "datasets" / "CBench"
        if not cbench.is_dir():
            return {}
        tasks = {}
        for proj_dir in sorted(cbench.iterdir()):
            if proj_dir.is_dir():
                task_id = proj_dir.name
                from .crustbench import _infer_domain
                tasks[task_id] = _infer_domain(task_id)
        return tasks
    elif bench == "agentre":
        from .agentre import discover as agentre_discover
        return agentre_discover()
    elif bench == "binaudit":
        from .binaudit import discover as binaudit_discover
        return binaudit_discover()
    elif bench == "cybersoc":
        from .cybersoc import discover as cybersoc_discover
        return cybersoc_discover()
    if not tasks:
        raise FileNotFoundError(
            f"No {bench} tasks found. Run harness2-setup "
            f"{bench}" + (f" --subset {subset}" if subset else "") + "."
        )
    return tasks


def select(tasks: dict[str, str], split: str, path: Path | None, *, benchmark: str) -> list[str]:
    if split not in ("all", "train", "test"):
        raise ValueError(f"Unknown split {split!r}; use all, train, or test")
    if path is None:
        if split != "all":
            raise ValueError(
                "--split train/test requires --split-file; create one with "
                "python scripts/split_tasks.py, or use --split all"
            )
        return sorted(tasks)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("benchmark") != benchmark:
        raise ValueError(f"{path}: expected a split for {benchmark}")
    halves = []
    for name in ("train", "test"):
        ids = data.get(name)
        if not isinstance(ids, list) or any(not isinstance(t, str) for t in ids):
            raise ValueError(f"{path}: {name} must be a list of task IDs")
        if len(set(ids)) != len(ids):
            raise ValueError(f"{path}: duplicate task IDs in {name}")
        halves.append(set(ids))
    if halves[0] & halves[1]:
        raise ValueError(f"{path}: train and test overlap")
    unknown = (halves[0] | halves[1]) - tasks.keys()
    if unknown:
        raise ValueError(f"{path}: task IDs absent from the dataset: {sorted(unknown)[:5]}")
    return sorted(halves[0] | halves[1] if split == "all" else data[split])
