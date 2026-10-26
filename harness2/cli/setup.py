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


def _install_benchmark_specifics(canonical_name: str, repo, dry: bool, substrate: str, subset: str | None = None):
    """Run benchmark-specific data fetch and post-install steps."""
    if canonical_name == "job-bench-eval":
        install.run(
            ["uv", "pip", "install", "--python", repo / ".venv/bin/python", "python-docx"],
            dry_run=dry,
        )
        install.download_jobbench(dry_run=dry)
    elif canonical_name == "harvey-labs":
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
    elif canonical_name == "workbuddy-bench":
        install.workbuddy_models(dry_run=dry, substrate=substrate)
        subsets = [subset] if subset else ["office", "web", "code", "sec"]
        install.run(
            ["bash", "scripts/dataset/fetch-dataset.sh", *subsets], cwd=repo, dry_run=dry
        )
        if substrate == "oc":
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
    elif canonical_name == "cve-bench":
        # CVE-Bench: metadata-only, no additional setup
        print(f"  [cve] Repo cloned; 40 metadata tasks from src/critical/metadata/CVE-*.yml")
    elif canonical_name == "cybench":
        # Cybench: curated 40-task list from benchmark/**/metadata/metadata.json
        print(f"  [cyber] Repo cloned; 40 curated CTF tasks")
    elif canonical_name == "Rust-SWE-Bench":
        # Rust-SWE-bench: Hugging Face dataset download (discovery only in harness2)
        dataset_dir = config.DEPENDENCIES / "rustbench"
        if not dry:
            dataset_dir.mkdir(parents=True, exist_ok=True)
            print(f"  [rswe] Downloading Hugging Face dataset user2f86/rustbench...")
            try:
                from datasets import load_dataset
                ds = load_dataset("user2f86/rustbench", revision="25020a91c4bba218e4a143ff315d93beb328c78b", split="train")
                ds.to_parquet(dataset_dir / "rustbench.parquet")
                print(f"  [rswe] Saved {len(ds)} instances to {dataset_dir / 'rustbench.parquet'} (discovery-only; upstream execution requires Docker)")
            except ImportError:
                print(f"  [rswe] datasets not installed; saving placeholder. Install with: uv pip install datasets pyarrow")
                (dataset_dir / "README.txt").write_text(
                    "Run: uv pip install datasets pyarrow && python -c "
                    '"from datasets import load_dataset; '
                    'ds=load_dataset(\\"user2f86/rustbench\\",revision=\\"25020a91c4bba218e4a143ff315d93beb328c78b\\",split=\\"train\\"); '
                    f'ds.to_parquet(\\"{dataset_dir}/rustbench.parquet\\")"\n',
                    encoding="utf-8",
                )
        else:
            print(f"  [rswe] Dataset download planned to {dataset_dir / 'rustbench.parquet'}")
    elif canonical_name == "CRUST-bench":
        # CRUST-bench: 100 C projects in data/C-projects
        print(f"  [crust] Repo cloned; 100 CBench/RBench C-to-Rust projects (OMP executor)")
    elif canonical_name == "AgentRE-Bench":
        # AgentRE-Bench: 13 Linux ELF levels (precompiled) + 20 Windows PE levels (shipped)
        print(f"  [agentre] Repo cloned: 13 Linux ELF levels and 20 Windows PE artifacts (static analysis only)")
    elif canonical_name == "BinaryAudit":
        # BinaryAudit: discovery only in harness2
        print(f"  [binaudit] Repo cloned (discovery only; full execution requires upstream Harbor with Ghidra/Radare2 container)")
    else:
        print(f"  [{canonical_name}] Repo cloned and environment configured.")


def main(argv=None):
    choices = sorted(set(install.BENCHMARK_NAMES.keys()) | {"all"})
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Supported benchmarks: 'all' or any of the 31 benchmarks (canonical name or alias, e.g. jb, lab, wb, cve, cyber, rswe, crust, agentre, binaudit, autopenbench, bountybench, ...)",
    )
    p.add_argument(
        "benchmark",
        choices=choices,
        metavar="BENCHMARK",
        help="Benchmark to install (or 'all' for all 31 dependencies). Accepts canonical names and aliases.",
    )
    p.add_argument(
        "--subset",
        choices=("office", "web", "code", "sec"),
        default=None,
        help="wb only: one subset to install; omitted installs office, web, code, and sec",
    )
    p.add_argument("--substrate", choices=SUBSTRATES, default="oc")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    target = args.benchmark
    is_all = target == "all"
    if args.subset and target not in ("wb", "workbuddy-bench", "all"):
        p.error("--subset only applies to wb")
    dry = args.dry_run
    missing = install.missing_runners()
    if missing and not dry:
        p.exit(1, f"setup failed: {missing}\n")
    if missing:
        print(f"Note: {missing}")

    try:
        if not dry:
            need_docker = is_all or target in ("wb", "workbuddy-bench")
            for binary in ("git", "uv", "npm") + (("docker", "curl") if need_docker else ()):
                if not shutil.which(binary):
                    raise RuntimeError(f"Missing {binary}; see README.md")

        # Benchmarks that need OpenCode substrate or when substrate is oc/cx/omp
        if is_all or target in install.BENCHMARK_NAMES or args.substrate in ("oc", "cx", "omp"):
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

        if is_all:
            # Iterate through all 31 dependencies defined in DEPENDENCY_PINS
            for dep_name in config.DEPENDENCY_PINS:
                if dep_name == "opencode":
                    continue
                install.clone(dep_name, dry_run=dry)
                install.patch(dep_name, dry_run=dry)
                install.overlays(dep_name, dry_run=dry)
                repo = config.DEPENDENCIES / dep_name
                install.setup_environment(repo, dry_run=dry)
                _install_benchmark_specifics(
                    dep_name, repo, dry=dry, substrate=args.substrate, subset=args.subset
                )
        else:
            canonical = install.BENCHMARK_NAMES[target]
            if canonical != "opencode":
                install.clone(canonical, dry_run=dry)
                install.patch(canonical, dry_run=dry)
                install.overlays(canonical, dry_run=dry)
                repo = config.DEPENDENCIES / canonical
                install.setup_environment(repo, dry_run=dry)
                _install_benchmark_specifics(
                    canonical, repo, dry=dry, substrate=args.substrate, subset=args.subset
                )

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
