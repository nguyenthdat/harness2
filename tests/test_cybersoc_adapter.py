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

"""CyberSOCEval discovery, prompt isolation, and Jaccard scoring."""

import json
import tempfile
import unittest
from pathlib import Path

from harness2.benchmarks.cybersoc import CyberSOCAdapter, _task, discover, jaccard
from harness2.core import runmark as RM


class CyberSOCTest(unittest.TestCase):
    def test_every_question_has_a_report_and_hides_the_key(self):
        tasks = discover()
        self.assertEqual(len(tasks), 608)
        self.assertNotIn("q0424", tasks)
        self.assertEqual(tasks["q0000"], "infostealers")
        adapter = CyberSOCAdapter("omp")
        prompt = adapter.task_prompt("q0000")
        self.assertNotIn("correct_options", prompt)
        self.assertNotIn(_task("q0000")["correct_options"][0] + _task("q0000")["correct_options"][1], prompt)
        staged = adapter.task_files("q0000")
        report = (staged / "report.json").read_text(encoding="utf-8")
        self.assertNotIn("correct_options", report)
        self.assertIn("signatures", report)

    def test_jaccard_uses_letter_sets(self):
        self.assertEqual(jaccard(["a", "B"], ["B", "A"]), 1.0)
        self.assertEqual(jaccard(["A"], ["A", "B"]), 0.5)
        self.assertEqual(jaccard(["C"], ["A"]), 0.0)

    def test_score_matches_the_hidden_key(self):
        adapter = CyberSOCAdapter("omp")
        row = _task("q0000")
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            output = run_dir / "output"
            output.mkdir()
            (output / "answer.json").write_text(
                json.dumps({"correct_answers": list(row["correct_options"])}) + "\n",
                encoding="utf-8",
            )
            RM.mark_complete(
                run_dir,
                run_id="t",
                extra={
                    "task_id": "q0000",
                    "report_sha256": __import__("hashlib").sha256(row["report"].read_bytes()).hexdigest(),
                    "output_fingerprint": RM.fingerprint(output),
                },
            )
            scored = adapter.score(run_dir, "q0000")
        self.assertIsNotNone(scored)
        self.assertEqual(scored["jaccard"], 1.0)
        self.assertTrue(scored["all_pass"])


if __name__ == "__main__":
    unittest.main()
