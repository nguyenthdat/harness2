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

"""Install a benchmark's pinned tools, runner overlays, dependencies, and data."""

from __future__ import annotations

import argparse
import shutil
import subprocess

from harness2 import config, install
from harness2.cli._common import SUBSTRATES


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("benchmark", choices=("jb", "lab", "wb", "cve", "cyber", "rswe", "crust", "agentre", "binaudit"))
    p.add_argument(
        "--subset",
        choices=("office", "web", "code", "sec"),
        default=None,
        help="wb only: one subset to install; omitted installs office, web, code, and sec",
    )
    p.add_argument("--substrate", choices=SUBSTRATES, default="oc")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    if args.subset and args.benchmark != "wb":
        p.error("--subset only applies to wb")
    dry = args.dry_run
    missing = install.missing_runners()
    if missing and not dry:
        p.exit(1, f"setup failed: {missing}\n")
    if missing:
        print(f"Note: {missing}")
    name = {
        "jb": "job-bench-eval",
        "lab": "harvey-labs",
        "wb": "workbuddy-bench",
        "cve": "cve-bench",
        "cyber": "cybench",
        "rswe": "Rust-SWE-Bench",
        "crust": "CRUST-bench",
        "agentre": "AgentRE-Bench",
        "binaudit": "BinaryAudit",
    }[args.benchmark]
    try:
        if not dry:
            for binary in ("git", "uv", "npm") + (
                ("docker", "curl") if args.benchmark == "wb" else ()
            ):
                if not shutil.which(binary):
                    raise RuntimeError(f"Missing {binary}; see README.md")
        
        # Benchmarks that need OpenCode substrate
        needs_opencode = args.benchmark in ("jb", "lab", "wb", "cve", "cyber", "rswe", "crust", "agentre", "binaudit")
        if needs_opencode or args.substrate in ("oc", "cx", "omp"):
            install.clone("opencode", dry_run=dry)
            install.patch("opencode", dry_run=dry)
            install.run(
                ["npm", "install", "--prefix", config.DEPENDENCIES / "tools", "bun@1.3.11"], dry_run=dry
            )
            install.run(
                [config.BUN, "install", "--frozen-lockfile", "--ignore-scripts"],
                cwd=config.OPENCODE_DIR,
                dry_run=dry,
            )
        
        install.clone(name, dry_run=dry)
        install.patch(name, dry_run=dry)
        install.overlays(name, dry_run=dry)
        repo = config.DEPENDENCIES / name
        
        # Use project-managed dependencies when available. Older benchmark repositories
        # without pyproject.toml get an isolated uv environment instead.
        if args.benchmark in ("jb", "lab", "wb"):
            if (repo / "pyproject.toml").is_file():
                install.run(["uv", "sync", "--locked", "--python", "3.12"], cwd=repo, dry_run=dry)
            else:
                install.run(["uv", "venv", repo / ".venv", "--python", "3.12"], cwd=repo, dry_run=dry)
                requirements = repo / "requirements.txt"
                if requirements.is_file() or dry:
                    install.run(
                        ["uv", "pip", "install", "--python", repo / ".venv/bin/python", "-r", requirements],
                        cwd=repo,
                        dry_run=dry,
                    )
        if args.benchmark == "jb":
            install.run(
                ["uv", "pip", "install", "--python", repo / ".venv/bin/python", "python-docx"],
                dry_run=dry,
            )
            install.download_jobbench(dry_run=dry)
        elif args.benchmark == "lab":
            install.run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    repo / ".venv/bin/python",
                    "google-auth[requests]",
                ],
                dry_run=dry,
            )
        elif args.benchmark == "wb":
            install.workbuddy_models(dry_run=dry)
            subsets = [args.subset] if args.subset else ["office", "web", "code", "sec"]
            install.run(
                ["bash", "scripts/dataset/fetch-dataset.sh", *subsets], cwd=repo, dry_run=dry
            )
            if args.substrate == "oc":
                install.run(
                    [
                        "uv",
                        "run",
                        "--no-sync",
                        "bash",
                        "scripts/harness/build-harness-mounts.sh",
                        "--harness",
                        "opencode/1.14.18",
                    ],
                    cwd=repo,
                    dry_run=dry,
                )
        elif args.benchmark == "cve":
            # CVE-Bench: metadata-only, no additional setup
            print(f"  [cve] Repo cloned; 40 metadata tasks from src/critical/metadata/CVE-*.yml")
        elif args.benchmark == "cyber":
            # Cybench: curated 40-task list from benchmark/**/metadata/metadata.json
            print(f"  [cyber] Repo cloned; 40 curated CTF tasks")
        elif args.benchmark == "rswe":
            # Rust-SWE-bench: Hugging Face dataset download
            dataset_dir = config.DEPENDENCIES / "rustbench"
            if not dry:
                dataset_dir.mkdir(parents=True, exist_ok=True)
                print(f"  [rswe] Downloading Hugging Face dataset user2f86/rustbench...")
                try:
                    from datasets import load_dataset
                    ds = load_dataset("user2f86/rustbench", revision="25020a91c4bba218e4a143ff315d93beb328c78b", split="train")
                    ds.to_parquet(dataset_dir / "rustbench.parquet")
                    print(f"  [rswe] Saved {len(ds)} instances to {dataset_dir / 'rustbench.parquet'}")
                except ImportError:
                    print(f"  [rswe] datasets not installed; saving placeholder. Install with: uv pip install datasets pyarrow")
                    (dataset_dir / "README.txt").write_text(
                        "Run: uv pip install datasets pyarrow && python -c "
                        '"from datasets import load_dataset; '
                        'ds=load_dataset(\\"user2f86/rustbench\\",revision=\\"25020a91c4bba218e4a143ff315d93beb328c78b\\",split=\\"train\\"); '
                        f'ds.to_parquet(\\"{dataset_dir}/rustbench.parquet\\")"\n',
                        encoding="utf-8",
                    )
        elif args.benchmark == "crust":
            # CRUST-bench: 100 C projects in data/C-projects
            print(f"  [crust] Repo cloned; 100 CBench/RBench C-to-Rust projects")
        elif args.benchmark == "agentre":
            # AgentRE-Bench: build binaries from sources
            print(f"  [agentre] Repo cloned; run ./build_binaries.sh to compile 23 levels")
            if not dry:
                build_script = repo / "build_binaries.sh"
                if build_script.exists():
                    print(f"  [agentre] Building binaries...")
                    install.run(["bash", str(build_script)], cwd=repo, dry_run=dry)
        elif args.benchmark == "binaudit":
            # BinaryAudit: requires Harbor and Docker base image
            print(f"  [binaudit] Repo cloned; install Harbor with: uv tool install harbor")
            print(f"  [binaudit] Build base image: docker build --platform linux/amd64 -t binaryaudit-base:latest -f docker/base.Dockerfile {repo}")
        
        if args.substrate == "cx":
            install.codex(dry_run=dry)
        if args.substrate == "omp":
            install.omp(dry_run=dry)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        p.exit(1, f"setup failed: {exc}\n")
    print(
        "Setup plan complete."
        if dry
        else "Installation complete. Run harness2-check before an experiment."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
