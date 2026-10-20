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

"""OmpSubstrate contracts: discoverable install layout, isolated direct runs, and evidence."""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from harness2 import config
from harness2.benchmarks.jobbench import JobBenchAdapter
from harness2.core import runmark, tree
from harness2.core.spec import BenchPrompts, BenchSpec, ChannelSpec
from harness2.substrate import omp
from harness2.substrate.omp import OMP_SURFACE, OmpSubstrate

FAKE_OMP = """#!{python}
import json, os, subprocess, sys, time
argv = sys.argv[1:]
if "models" in argv:
    print(json.dumps({{"models": [{{"selector": "prov/model-flash"}}]}}))
    sys.exit(0)
keys = ("OMP_PROFILE", "PI_PROFILE", "PI_CODING_AGENT_DIR")
record = {{"argv": argv, "env": {{k: os.environ.get(k) for k in keys}}, "stdin": sys.stdin.read()}}
with open(os.environ["FAKE_OMP_RECORD"], "w") as fh:
    json.dump(record, fh)
if os.environ.get("FAKE_OMP_HANG"):
    child = subprocess.Popen(["sleep", "60"])
    with open(os.environ["FAKE_OMP_RECORD"] + ".child", "w") as fh:
        fh.write(str(child.pid))
    time.sleep(60)
time.sleep(float(os.environ.get("FAKE_OMP_SLOW", "0")))
if os.environ.get("FAKE_OMP_WRITE"):
    output = os.path.join(argv[argv.index("--cwd") + 1], "output")
    with open(os.path.join(output, os.environ["FAKE_OMP_WRITE"]), "w") as fh:
        fh.write("done\\n")
print(json.dumps({{"type": "session", "version": 3}}))
print(json.dumps({{"type": "agent_end", "messages": []}}))
sys.exit(int(os.environ.get("FAKE_OMP_EXIT", "0")))
"""


def _event(kind: str, **fields) -> str:
    return json.dumps({"type": kind, **fields})


class OmpSubstrateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.substrate = OmpSubstrate()
        fake = self.root / "omp"
        fake.write_text(FAKE_OMP.format(python=sys.executable), encoding="utf-8")
        fake.chmod(0o755)
        for name, value in (("OMP_BIN", str(fake)), ("OMP_PROFILE", "rollout-profile")):
            patcher = patch.object(config, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_materialise_installs_the_layout_omp_discovers(self):
        channel = ChannelSpec("opencode", "local/deterministic")
        spec = BenchSpec(
            name="unit",
            runs_root=self.root / "runs",
            install_mode="omp_root",
            prompts=BenchPrompts(work="unit work"),
            channels={"proposer": channel, "selector": channel},
        )
        harness = tree.write_tree(
            OMP_SURFACE,
            {
                "AGENTS.md": "- When parsing, read `skill://parse` and follow it.\n",
                ".omp/skills/parse/SKILL.md": "---\ndescription: parse things\n---\nSteps.\n",
                ".omp/skills/parse/scripts/run.py": "print('ok')\n",
                "sub_agents/reader/AGENT.md": "---\nname: wrong\ndescription: reads\n---\nRead.\n",
                "sub_agents/bare/AGENT.md": "description: Reads PDFs: one table\nSummarise.\n",
            },
            self.root / "harness",
        )
        (harness / "notes.txt").write_text("off the surface\n", encoding="utf-8")

        install = self.substrate.materialise(harness, spec, {})
        self.addCleanup(shutil.rmtree, install.staging_dir, True)
        staged = Path(install.staging_dir)
        files = sorted(p.relative_to(staged).as_posix() for p in staged.rglob("*") if p.is_file())

        self.assertEqual(
            files,
            [
                ".omp/agents/bare.md",
                ".omp/agents/reader.md",
                ".omp/skills/parse/SKILL.md",
                ".omp/skills/parse/scripts/run.py",
                "AGENTS.md",
            ],
        )
        reader = (staged / ".omp/agents/reader.md").read_text(encoding="utf-8")
        self.assertTrue(reader.startswith("---\nname: reader\ndescription: reads\n---\n"))
        self.assertNotIn("name: wrong", reader)
        bare = (staged / ".omp/agents/bare.md").read_text(encoding="utf-8")
        self.assertTrue(bare.startswith('---\nname: bare\ndescription: "Reads PDFs: one table"'))

    def test_run_isolates_the_profile_and_pins_every_role_to_the_model(self):
        workspace = self.root / "ws"
        (workspace / ".omp" / "agents").mkdir(parents=True)
        (workspace / ".omp" / "agents" / "reader.md").write_text("---\n", encoding="utf-8")
        record = self.root / "record.json"
        env = {
            **os.environ,
            "OMP_PROFILE": "operator",
            "PI_PROFILE": "operator",
            "PI_CODING_AGENT_DIR": str(self.root / "operator-agent"),
            "FAKE_OMP_RECORD": str(record),
        }
        stream = self.root / "traj" / "attempt.jsonl"

        run = self.substrate.run(
            "@task.md is a literal prompt",
            workspace,
            model="prov/m",
            timeout=60,
            stream=stream,
            env=env,
        )

        self.assertEqual((run.exit_code, run.timed_out), (0, False))
        self.assertEqual(len(stream.read_text().splitlines()), 2)
        got = json.loads(record.read_text())
        self.assertEqual(got["stdin"], "@task.md is a literal prompt")
        self.assertEqual(
            got["env"],
            {"OMP_PROFILE": "rollout-profile", "PI_PROFILE": None, "PI_CODING_AGENT_DIR": None},
        )
        argv = got["argv"]
        self.assertEqual(argv[argv.index("--profile") + 1], "rollout-profile")
        self.assertEqual(argv[argv.index("--cwd") + 1], str(workspace))
        settings = json.loads(Path(argv[argv.index("--config") + 1]).read_text())
        self.assertEqual(set(settings["modelRoles"].values()), {"prov/m"})
        self.assertEqual(settings["task"]["agentModelOverrides"], {"reader": "prov/m"})
        self.assertFalse(settings["retry"]["modelFallback"])

    def test_run_past_its_wall_kills_the_whole_process_group(self):
        workspace = self.root / "ws"
        workspace.mkdir()
        record = self.root / "record.json"
        env = {**os.environ, "FAKE_OMP_RECORD": str(record), "FAKE_OMP_HANG": "1"}

        with patch.object(omp, "_KILL_GRACE", 2):
            t0 = time.monotonic()
            run = self.substrate.run(
                "work", workspace, model="prov/m", timeout=0, stream=self.root / "s.jsonl", env=env
            )

        self.assertTrue(run.timed_out)
        self.assertIsNone(run.exit_code)
        self.assertLess(time.monotonic() - t0, 30)
        child = int(Path(str(record) + ".child").read_text())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail("a process the rollout started outlived it")
        rendered = self.substrate.read_trajectory(
            self.root / "s.jsonl", obs_trunc=1000, max_chars=10_000
        )
        self.assertIn("run KILLED at its 0s time limit", rendered)

    def test_a_turn_omp_stops_at_the_time_limit_is_not_a_clean_finish(self):
        workspace = self.root / "ws"
        workspace.mkdir()
        env = {**os.environ, "FAKE_OMP_RECORD": str(self.root / "r.json"), "FAKE_OMP_SLOW": "1.5"}
        stream = self.root / "s.jsonl"

        run = self.substrate.run(
            "work", workspace, model="prov/m", timeout=1, stream=stream, env=env
        )

        self.assertEqual((run.exit_code, run.timed_out), (0, True))
        self.assertEqual(omp.summarize(stream)["n_events"], 2)
        rendered = self.substrate.read_trajectory(stream, obs_trunc=1000, max_chars=10_000)
        self.assertIn("run stopped by OMP at its 1s time limit", rendered)

    def test_jobbench_adopts_a_rollout_only_when_the_runtime_exits_cleanly(self):
        store = self.root / "store"
        task = store / "accountants" / "task1"
        (task / "task_folder").mkdir(parents=True)
        (task / "task_folder" / "TASK_INSTRUCTIONS.txt").write_text("Write x.txt.\n")
        harness = tree.write_tree(OMP_SURFACE, {"AGENTS.md": "Do the task.\n"}, self.root / "h")
        adapter = JobBenchAdapter(substrate="omp", store_root=store, timeout=60)
        env = {"FAKE_OMP_RECORD": str(self.root / "r.json"), "FAKE_OMP_WRITE": "x.txt"}
        run_id, label = "t/accountants/task1/omp1", "t__accountants__task1__omp1"

        def model():
            return patch.object(config, "SOLVER_MODEL_OMP", "prov/model-flash")

        with model(), patch.dict(os.environ, {**env, "FAKE_OMP_EXIT": "1"}):
            with self.assertRaisesRegex(RuntimeError, "exited 1"):
                adapter.execute("accountants/task1", harness, run_id)
        self.assertFalse((task / "model_output" / label).exists())
        self.assertIsNone(runmark.read_mark(task / "model_traj" / label))

        with model(), patch.dict(os.environ, {**env, "FAKE_OMP_EXIT": "0"}):
            out = adapter.execute("accountants/task1", harness, run_id)
        self.assertEqual([p.name for p in out.iterdir()], ["x.txt"])
        self.assertTrue(runmark.is_complete(task / "model_traj" / label, harness_dir=harness))

    def test_preflight_requires_the_exact_model_under_the_profile(self):
        with patch.object(config, "SOLVER_MODEL_OMP", "prov/model"):
            with self.assertRaisesRegex(RuntimeError, "prov/model is not available"):
                self.substrate.preflight()
        with patch.object(config, "SOLVER_MODEL_OMP", "prov/model-flash:high"):
            self.substrate.preflight()

    def test_trajectory_states_calls_a_cut_short_run_never_answered(self):
        stream = self.root / "events.jsonl"
        assistant = {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "plan the read"},
                {"type": "toolCall", "id": "a", "name": "read", "arguments": {"path": "in.csv"}},
                {"type": "toolCall", "id": "b", "name": "write", "arguments": {"path": "out"}},
            ],
            "stopReason": "toolUse",
            "usage": {"input": 10, "output": 5, "cost": {"total": 0.5}},
        }
        failed = {
            "role": "assistant",
            "content": [{"type": "text", "text": "partial"}],
            "stopReason": "error",
            "errorMessage": "provider 500",
        }
        stream.write_text(
            "\n".join(
                [
                    _event("session", version=3),
                    _event("message_end", message={"role": "user", "content": "do it"}),
                    _event("message_update", assistantMessageEvent={"type": "text_delta"}),
                    _event("message_end", message=assistant),
                    _event(
                        "message_end",
                        message={
                            "role": "toolResult",
                            "toolCallId": "a",
                            "toolName": "read",
                            "content": [{"type": "text", "text": "ENOENT"}],
                            "isError": True,
                        },
                    ),
                    _event("message_end", message=failed),
                    "not json",
                ]
            ),
            encoding="utf-8",
        )

        rendered = self.substrate.read_trajectory(stream, obs_trunc=10_000, max_chars=100_000)

        self.assertEqual(
            rendered.splitlines(),
            [
                "[USER] do it",
                "[THINKING] plan the read",
                '[ACTION] read({"path": "in.csv"})',
                '[ACTION] write({"path": "out"})',
                "[OBSERVATION ERROR] read: ENOENT",
                "[ASSISTANT] partial",
                "[ERROR] error: provider 500",
                "[OBSERVATION ERROR] write: (no result -- the run ended before it returned)",
                "[HARNESS] stream ended WITHOUT agent_end (process killed or crashed) | tokens "
                "in=10 cache_read=0 out=5 reasoning=0 cost=$0.5000",
            ],
        )


if __name__ == "__main__":
    unittest.main()
