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

"""Benchmark dependency and runtime readiness checks."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess

from . import config
from .install import PATCHES, missing_runners
from .substrate.opencode import OpencodeSubstrate


def check(adapter, *, judge=False) -> list[str]:
    missing = missing_runners()
    if missing:
        return [missing]
    errors = []

    def probe(label, cmd, *, cwd=None, remedy="run harness2-setup for this benchmark"):
        try:
            r = subprocess.run(
                [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, timeout=45
            )
            if r.returncode:
                errors.append(f"{label} failed; {remedy}")
            return r.returncode == 0
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"{label}: {type(exc).__name__}; see README.md")
            return False

    validators = [
        lambda: config.validate_models(judge=judge),
        adapter.tasks,
        OpencodeSubstrate().preflight,
    ]
    adapter_preflight = getattr(adapter, "preflight", None)
    if adapter.substrate.name == "omp":
        probe("OMP runtime", [config.OMP_BIN, "--version"], remedy="install omp or set HARNESS2_OMP_BIN")
        if adapter_preflight is None:
            validators.append(adapter.substrate.preflight)
    if adapter_preflight is not None:
        validators.append(adapter_preflight)
    for validate in validators:
        try:
            validate()
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(str(exc))

    bench = adapter.spec.name.split("-", 1)[0]
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
        "cybersoc": "CyberSOCEval_data",
    }.get(bench, bench)
    repo = config.DEPENDENCIES / name
    for dependency in (name, "opencode"):
        target = config.DEPENDENCIES / dependency
        if (target / ".git").exists():
            try:
                head = subprocess.check_output(
                    ["git", "-C", str(target), "rev-parse", "HEAD"], text=True
                ).strip()
                if head != config.DEPENDENCY_PINS[dependency]:
                    errors.append(f"{dependency}: checkout differs from the supported pin")
            except subprocess.CalledProcessError:
                errors.append(f"{dependency}: cannot read checkout revision")
        if dependency not in PATCHES:
            continue
        patch = config.THIRD_PARTY / "patches" / PATCHES[dependency]
        probe(
            f"{dependency} patch",
            ["git", "-C", target, "apply", "--reverse", "--check", patch],
        )
    if not (config.OPENCODE_DIR / "node_modules").is_dir():
        errors.append(f"OpenCode dependencies missing; run harness2-setup {bench}")

    executors = (config.SOLVER_MODEL_OC, config.IMPROVER_MODEL) + (
        (config.SOLVER_MODEL_OMP,) if adapter.substrate.name == "omp" else ()
    )
    omp_non_vertex = adapter.substrate.name == "omp" and not config.SOLVER_MODEL_OMP.startswith(
        "google-vertex/"
    )
    needs_adc = any(m.startswith("google-vertex") for m in executors) or (
        judge
        and (bench == "wb" or config.JUDGE_MODEL.startswith(("claude", "gemini")))
        and not omp_non_vertex
    )
    if needs_adc:
        probe(
            "Google Application Default Credentials",
            ["gcloud", "auth", "application-default", "print-access-token"],
        )
    if bench == "lab":
        for binary in ("pandoc", "pdftoppm"):
            if not shutil.which(binary):
                errors.append(f"{binary} missing; install pandoc and poppler-utils (README.md)")
        probe(
            "LAB document and judge dependencies",
            [config.LAB_PYTHON, "-c", "import evaluation.scoring; import google.auth, anthropic"],
            cwd=repo,
        )
    elif bench == "jb" and judge:
        probe(
            "JobBench document and judge dependencies",
            [
                config.JB_JUDGE_PYTHON,
                "-c",
                "import pandas, openpyxl, docx, mammoth, pdfplumber, pptx, openai",
            ],
        )
        if not config.JB_JUDGE_API_BASE:
            errors.append(
                "Set GOOGLE_CLOUD_PROJECT or HARNESS2_JUDGE_BASE_URL for JobBench judging"
            )
        if (
            config.JUDGE_MODEL
            and not config.JB_JUDGE_API_KEY
            and not config.JUDGE_MODEL.startswith("gemini")
        ):
            errors.append(
                "A non-Gemini JobBench judge requires HARNESS2_JUDGE_BASE_URL and HARNESS2_JUDGE_API_KEY"
            )
    elif bench == "wb":
        probe("Docker daemon", ["docker", "info", "--format", "{{.ServerVersion}}"])
        if adapter.spec.name == "wb-office":
            probe(
                "WorkBuddy document rendering",
                [config.WB_RENDER_PY, "-c", "import openpyxl, pptx"],
                remedy="install 'harness2[render]' in the main environment",
            )
        harness_name = {
            "oc": "opencode",
            "cx": "codex-harness",
            "omp": "omp-harness",
        }.get(adapter.substrate.name, adapter.substrate.name)
        probe(
            "WorkBuddy runtime",
            [
                repo / ".venv/bin/python",
                "-c",
                "import harbor; from workbuddy_bench.runner.harness_adapters import HARNESS_ADAPTERS; "
                f"assert {harness_name!r} in HARNESS_ADAPTERS",
            ],
            cwd=repo,
        )
        if adapter.substrate.name == "omp" and not config.SOLVER_MODEL_OMP.startswith("google-vertex/"):
            expected_models = {
                "solver": config.WB_MODEL_NAME,
                "judge": config.JUDGE_MODEL,
            }
        else:
            expected_models = {
                "solver": "google/" + config.SOLVER_MODEL_OC.removeprefix("google-vertex/"),
                "judge": "google/" + config.JUDGE_MODEL,
            }
        for role, expected in expected_models.items():
            path = repo / "configs/models/harness2" / f"{role}.yaml"
            try:
                if json.loads(path.read_text())["model"]["name"] != expected:
                    errors.append(f"WorkBuddy {role} configuration is stale; rerun setup")
            except (OSError, ValueError, KeyError, TypeError):
                errors.append(f"WorkBuddy {role} configuration missing; rerun setup")
    elif bench == "cybersoc":
        from .benchmarks.cybersoc import questions_path

        path = questions_path()
        if not path.is_file():
            errors.append(f"CyberSOCEval questions missing at {path}; run harness2-setup cybersoc")
        else:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != config.CYBERSOC_QUESTIONS_SHA256:
                errors.append("CyberSOCEval questions.json does not match the pinned sha256")
        if not (repo / "data" / "hybrid-analysis").is_dir():
            errors.append("CyberSOCEval hybrid-analysis reports missing; rerun harness2-setup cybersoc")
    elif bench == "agentre":
        for tool in ("file", "strings"):
            if not shutil.which(tool):
                errors.append(f"{tool} missing; required for static reverse engineering analysis")
        has_objdump = any(shutil.which(cmd) for cmd in ("gobjdump", "llvm-objdump", "objdump"))
        if not has_objdump:
            errors.append("objdump (or gobjdump/llvm-objdump) missing; required for AgentRE disassembly")
    return errors


def require_ready(adapter, *, judge=False):
    """Raise before a caller spends anything when this benchmark is not ready to run.

    `judge=True` also demands what grading will need: `HARNESS2_JUDGE_MODEL` set, and,
    where a benchmark grades in its own environment, that environment installed and
    pointed at an endpoint. Those are offline presence and import checks — they catch an
    unset or unbuilt judge, not an account that cannot serve the judge model, which is
    still first learned when the judge actually calls it.
    """
    errors = check(adapter, judge=judge)
    if errors:
        raise config.ConfigError(
            "Setup incomplete; nothing has run yet:\n  - " + "\n  - ".join(errors)
        )
