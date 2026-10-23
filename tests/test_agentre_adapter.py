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

"""Behavioral regression test for the AgentRE static-analysis OMP adapter."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness2 import config
from harness2.benchmarks.agentre import AgentREAdapter, discover
from harness2.core import runmark as RM
from harness2.core.spec import BenchmarkAdapter

FAKE_OMP = """#!{python}
import json, os, sys
argv = sys.argv[1:]
if "--version" in argv:
    print("omp/18.12.3")
    sys.exit(0)
if "models" in argv:
    print(json.dumps({{"models": [{{"selector": "prov/model-flash"}}]}}))
    sys.exit(0)
cwd = argv[argv.index("--cwd") + 1]
out_dir = os.path.join(cwd, "output")
os.makedirs(out_dir, exist_ok=True)
if os.environ.get("FAKE_AGENTRE_WRITE"):
    with open(os.path.join(out_dir, "analysis.json"), "w") as fh:
        fh.write(os.environ["FAKE_AGENTRE_WRITE"])
    with open(os.path.join(out_dir, "evidence.md"), "w") as fh:
        fh.write("# Evidence\\nStatic inspection.\\n")
print(json.dumps({{"type": "session", "version": 3}}))
print(json.dumps({{"type": "agent_end", "messages": []}}))
sys.exit(0)
"""


def _setup_synthetic_repo(root: Path) -> Path:
    """Build a minimal controlled AgentRE fixture using real scorer and tool schema."""
    repo = root / "synthetic_agentre"
    repo.mkdir(parents=True)
    real_repo = config.agentre_repo()

    # Link real scorer and tool schema for exact behavioral evaluation
    shutil.copy2(real_repo / "scorer.py", repo / "scorer.py")
    (repo / "harness").mkdir()
    shutil.copy2(real_repo / "harness" / "tools.py", repo / "harness" / "tools.py")

    # Synthetic binary dirs
    bin_dir = repo / "binaries"
    bin_dir.mkdir(parents=True)
    pe_dir = repo / "version3" / "binaries" / "windows"
    pe_dir.mkdir(parents=True)

    # Copy genuine compiled binaries so objdump architecture probing succeeds
    shutil.copyfile(real_repo / "binaries" / "level1_TCPServer", bin_dir / "syn_elf_1")
    shutil.copyfile(
        real_repo / "version3" / "binaries" / "windows" / "windows_level14_DLLInjection.exe",
        pe_dir / "syn_pe_1.exe",
    )
    # Ground truths
    gt_dir = repo / "ground_truths"
    gt_dir.mkdir(parents=True)
    (gt_dir / "syn_elf_1.json").write_text(
        json.dumps(
            {
                "sample": "syn_elf_1",
                "tier": "standard",
                "file_type": "ELF64",
                "encoded_strings": True,
                "decoded_c2": None,
                "c2_protocol": None,
                "techniques": ["xor_encoding", "socket_connect"],
            }
        ),
        encoding="utf-8",
    )

    pe_gt_dir = repo / "version3" / "ground_truths"
    pe_gt_dir.mkdir(parents=True)
    (pe_gt_dir / "syn_pe_1.json").write_text(
        json.dumps(
            {
                "sample": "windows_syn_pe_1",
                "tier": "pe_injection",
                "file_type": "PE64",
                "encoded_strings": True,
                "decoded_c2": None,
                "c2_protocol": None,
                "techniques": ["dll_injection"],
                "injection_details": {"method": "CreateRemoteThread"},
                "decoded_strings": {"s1": "kernel32.dll"},
                "anti_analysis": ["isdebuggerpresent"],
                "encryption_details": {"algorithm": "XOR", "key": "5A3C"},
            }
        ),
        encoding="utf-8",
    )

    # Manifests
    (repo / "tasks.json").write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "task_id": "syn_elf_1",
                        "source_file": "samples/syn_elf_1.c",
                        "binary_name": "syn_elf_1",
                        "ground_truth": "ground_truths/syn_elf_1.json",
                        "difficulty": 1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (repo / "version3" / "tasks_v3.json").write_text(
        json.dumps(
            {
                "binary_root": "version3/binaries",
                "tasks": [
                    {
                        "task_id": "syn_pe_1",
                        "binary_name": "windows/syn_pe_1.exe",
                        "display_name": "sample_pe.bin",
                        "ground_truth": "version3/ground_truths/syn_pe_1.json",
                        "difficulty": 14,
                        "variant": "unstripped",
                        "source_file": "version3/sources/syn_pe_1.c",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return repo


class AgentREAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def test_discovery_manifest_identities(self):
        tasks = discover()
        self.assertEqual(len(tasks), 33)
        elf_tasks = [t for t, d in tasks.items() if d == "elf-re"]
        pe_tasks = [t for t, d in tasks.items() if d == "pe-re"]
        self.assertEqual(len(elf_tasks), 13)
        self.assertEqual(len(pe_tasks), 20)
        self.assertIn("level1_TCPServer", tasks)
        self.assertIn("level13_MetamorphicDropper", tasks)
        self.assertIn("v3_l14_u", tasks)
        self.assertIn("v3_l23_s", tasks)

    def test_protocol_and_substrate_rejection(self):
        adapter = AgentREAdapter("omp")
        self.assertIsInstance(adapter, BenchmarkAdapter)
        with self.assertRaises(ValueError):
            AgentREAdapter("oc")
        with self.assertRaises(ValueError):
            AgentREAdapter("cx")

    def test_neutral_prompt_invariants(self):
        adapter = AgentREAdapter("omp")
        elf_prompt = adapter.task_prompt("level1_TCPServer")
        self.assertIn("target.bin", elf_prompt)
        self.assertNotIn("level1_TCPServer", elf_prompt)
        self.assertIn("Static analysis only", elf_prompt)
        self.assertIn("analysis.schema.json", elf_prompt)

        pe_prompt = adapter.task_prompt("v3_l14_u")
        self.assertIn("target.exe", pe_prompt)
        self.assertNotIn("windows_level14_DLLInjection", pe_prompt)
        self.assertIn("Static analysis only", pe_prompt)

    def test_task_files_staging(self):
        adapter = AgentREAdapter("omp")
        files_dir = adapter.task_files("level1_TCPServer")
        self.assertTrue(files_dir.is_dir())
        staged_names = sorted(p.name for p in files_dir.iterdir())
        self.assertEqual(staged_names, ["analysis.schema.json", "target.bin", "tools.json"])
        target = files_dir / "target.bin"
        self.assertEqual(target.stat().st_mode & 0o111, 0)

    def test_delivered_validation_rejects_malformed_and_incomplete_output(self):
        adapter = AgentREAdapter("omp")
        run_dir = self.root / "rollout"
        out_dir = run_dir / "output"
        out_dir.mkdir(parents=True)

        self.assertFalse(adapter.delivered(run_dir))

        (out_dir / "evidence.md").write_text("# Evidence\nDisassembly at 0x401000\n", encoding="utf-8")
        (out_dir / "analysis.json").write_text(json.dumps({"file_type": "ELF64"}), encoding="utf-8")
        self.assertFalse(adapter.delivered(run_dir))

        valid_answer = {
            "file_type": "ELF64",
            "encoded_strings": False,
            "techniques": ["socket_listen", "socket_bind"],
            "decoded_c2": None,
            "c2_protocol": "TCP",
        }
        (out_dir / "analysis.json").write_text(json.dumps(valid_answer), encoding="utf-8")
        (out_dir / "evidence.md").write_text("   \n", encoding="utf-8")
        self.assertFalse(adapter.delivered(run_dir))

        (out_dir / "evidence.md").write_text("Offset 0x120: socket call\n", encoding="utf-8")
        self.assertTrue(adapter.delivered(run_dir))

        (out_dir / "analysis.json").write_text(
            '{"file_type": NaN, "encoded_strings": false, "techniques": []}', encoding="utf-8"
        )
        self.assertFalse(adapter.delivered(run_dir))

    def test_controlled_synthetic_scoring_and_penalties(self):
        syn_repo = _setup_synthetic_repo(self.root)
        with patch.object(config, "agentre_repo", lambda: syn_repo):
            adapter = AgentREAdapter("omp")
            run_dir = self.root / "syn_rollout"
            out_dir = run_dir / "output"
            out_dir.mkdir(parents=True)

            task_id = "syn_elf_1"
            task = adapter._task(task_id)
            from harness2.benchmarks.agentre import _binary, _sha256

            binary_hash = _sha256(_binary(task))

            # 1. Perfect synthetic answer
            perfect_answer = {
                "file_type": "ELF64",
                "encoded_strings": True,
                "decoded_c2": None,
                "c2_protocol": None,
                "techniques": ["xor_encoding", "socket_connect"],
            }
            (out_dir / "analysis.json").write_text(json.dumps(perfect_answer), encoding="utf-8")
            (out_dir / "evidence.md").write_text("Static string inspection.\n", encoding="utf-8")

            RM.mark_complete(
                run_dir,
                run_id="run_syn_1",
                harness_dir=adapter.base_harness(),
                extra={
                    "task_id": task_id,
                    "binary_sha256": binary_hash,
                    "output_fingerprint": RM.fingerprint(out_dir),
                },
            )

            res = adapter.score(run_dir, task_id)
            self.assertIsNotNone(res)
            self.assertEqual(res["final_score"], 1.0)
            self.assertEqual(res["n_passed"], 1.0)
            self.assertEqual(res["n_criteria"], 1)
            self.assertTrue(res["all_pass"])
            self.assertEqual(res["hallucination_penalty"], 0.0)
            self.assertEqual(res["spurious_penalty"], 0.0)

            # 2. Synthetic answer with hallucinated technique penalty
            hallucinated_answer = dict(perfect_answer)
            hallucinated_answer["techniques"] = [
                "xor_encoding",
                "socket_connect",
                "non_existent_fake_technique",
            ]
            (out_dir / "analysis.json").write_text(json.dumps(hallucinated_answer), encoding="utf-8")
            RM.mark_complete(
                run_dir,
                run_id="run_syn_1",
                harness_dir=adapter.base_harness(),
                extra={
                    "task_id": task_id,
                    "binary_sha256": binary_hash,
                    "output_fingerprint": RM.fingerprint(out_dir),
                },
            )
            res_halluc = adapter.score(run_dir, task_id)
            self.assertIsNotNone(res_halluc)
            self.assertGreater(res_halluc["hallucination_penalty"], 0.0)
            self.assertLess(res_halluc["final_score"], 1.0)
            self.assertEqual(res_halluc["n_passed"], res_halluc["final_score"])
            self.assertFalse(res_halluc["all_pass"])

            # 3. Synthetic answer with spurious C2 claims when GT is null
            spurious_answer = dict(perfect_answer)
            spurious_answer["decoded_c2"] = "1.2.3.4:4444"
            spurious_answer["c2_protocol"] = "TCP"
            (out_dir / "analysis.json").write_text(json.dumps(spurious_answer), encoding="utf-8")
            RM.mark_complete(
                run_dir,
                run_id="run_syn_1",
                harness_dir=adapter.base_harness(),
                extra={
                    "task_id": task_id,
                    "binary_sha256": binary_hash,
                    "output_fingerprint": RM.fingerprint(out_dir),
                },
            )
            res_spur = adapter.score(run_dir, task_id)
            self.assertIsNotNone(res_spur)
            self.assertGreater(res_spur["spurious_penalty"], 0.0)
            self.assertLess(res_spur["final_score"], 1.0)

    def test_omp_launcher_staging_and_runmark_lifecycle(self):
        syn_repo = _setup_synthetic_repo(self.root)
        fake = self.root / "fake_omp"
        fake.write_text(FAKE_OMP.format(python=sys.executable), encoding="utf-8")
        fake.chmod(0o755)

        valid_answer = {
            "file_type": "ELF64",
            "encoded_strings": True,
            "decoded_c2": None,
            "c2_protocol": None,
            "techniques": ["xor_encoding", "socket_connect"],
        }
        env_write = json.dumps(valid_answer)

        with patch.object(config, "agentre_repo", lambda: syn_repo), patch.object(
            config, "OMP_BIN", str(fake)
        ), patch.object(config, "OMP_PROFILE", "test-profile"), patch.object(
            config, "SOLVER_MODEL_OMP", "prov/model-flash"
        ), patch.dict(
            "os.environ", {"FAKE_AGENTRE_WRITE": env_write}
        ):
            adapter = AgentREAdapter("omp")
            run_id = "test_omp_rollout_1"
            run_dir = adapter.execute("syn_elf_1", None, run_id)
            self.assertTrue(run_dir.is_dir())
            self.assertTrue(adapter.delivered(run_dir))
            self.assertTrue((run_dir / "output" / "analysis.json").is_file())
            self.assertTrue((run_dir / "output" / "evidence.md").is_file())
            self.assertTrue((run_dir / "omp-output.jsonl").is_file())

            # Verification of runmark completion
            self.assertTrue(RM.is_complete(run_dir, harness_dir=adapter.base_harness()))

            # Rollout idempotence: second execute returns existing run_dir
            run_dir_2 = adapter.execute("syn_elf_1", None, run_id)
            self.assertEqual(run_dir.resolve(), run_dir_2.resolve())
