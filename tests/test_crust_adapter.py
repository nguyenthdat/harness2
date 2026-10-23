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

"""Behavioral regression tests for the CRUST-Bench adapter on OmpSubstrate."""

import shutil
import tempfile
import unittest
from pathlib import Path

from harness2.benchmarks.crustbench import (
    CrustAdapter,
    _is_delivery,
    _rbench_dir,
)
from harness2.core.spec import BenchmarkAdapter


class CrustAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def test_protocol_and_substrate_rejection(self):
        adapter = CrustAdapter("omp")
        self.assertIsInstance(adapter, BenchmarkAdapter)
        with self.assertRaises(ValueError):
            CrustAdapter("oc")
        with self.assertRaises(ValueError):
            CrustAdapter("cx")

    def test_cbench_to_rbench_name_resolution(self):
        self.assertEqual(_rbench_dir("aes128-SIMD").name, "aes128_SIMD")
        self.assertEqual(_rbench_dir("2DPartInt").name, "proj_2DPartInt")
        self.assertEqual(_rbench_dir("42-Kocaeli-Printf").name, "proj_42_Kocaeli_Printf")
        self.assertEqual(_rbench_dir("leftpad").name, "leftpad")
        with self.assertRaises(FileNotFoundError):
            _rbench_dir("nonexistent_task_xyz")

    def test_delivery_filter_rejects_empty_and_unchanged_stubs(self):
        empty_dir = self.root / "empty"
        empty_dir.mkdir()
        self.assertFalse(_is_delivery(empty_dir))

        stub_dir = self.root / "stub"
        (stub_dir / "src").mkdir(parents=True)
        (stub_dir / "src" / "leftpad.rs").write_text(
            "// Function Declarations\n"
            "pub fn leftpad(str: &str, padding: &str, min_len: usize, dest: &mut [u8]) -> usize {\n"
            "    unimplemented!();\n"
            "}\n",
            encoding="utf-8",
        )
        self.assertFalse(_is_delivery(stub_dir))

        real_dir = self.root / "real"
        (real_dir / "src").mkdir(parents=True)
        (real_dir / "src" / "leftpad.rs").write_text(
            "pub fn leftpad(str: &str, padding: &str, min_len: usize, dest: &mut [u8]) -> usize {\n"
            "    let slen = str.len();\n"
            "    if dest.is_empty() { return slen; }\n"
            "    let copy = slen.min(dest.len());\n"
            "    dest[..copy].copy_from_slice(&str.as_bytes()[..copy]);\n"
            "    copy\n"
            "}\n",
            encoding="utf-8",
        )
        self.assertTrue(_is_delivery(real_dir))

    def test_task_files_and_prompt_contain_no_answer_tests(self):
        adapter = CrustAdapter("omp")
        c_src = adapter.task_files("leftpad")
        self.assertIsNotNone(c_src)
        self.assertTrue(c_src.is_dir())
        files = [p.name for p in c_src.rglob("*") if p.is_file()]
        self.assertIn("leftpad.c", files)
        self.assertNotIn("tests.rs", files)

        prompt = adapter.task_prompt("leftpad")
        self.assertIn("c_source/src/leftpad.c", prompt)
        self.assertIn("Required Rust Interface Specifications", prompt)
        self.assertNotIn("test_leftpad", prompt)
        self.assertNotIn("assert_eq!", prompt)

    @unittest.skipUnless(shutil.which("cargo"), "cargo required for execution check")
    def test_isolated_judge_safe_rust_and_compiler_enforcement(self):
        adapter = CrustAdapter("omp")

        # 1. Candidate with unsafe code must fail compiler lint
        unsafe_run = self.root / "unsafe_run"
        (unsafe_run / "src").mkdir(parents=True)
        (unsafe_run / "src" / "leftpad.rs").write_text(
            "pub fn leftpad(str: &str, padding: &str, min_len: usize, dest: &mut [u8]) -> usize {\n"
            "    unsafe { let _ = 1; }\n"
            "    0\n"
            "}\n",
            encoding="utf-8",
        )
        unsafe_score = adapter.score(unsafe_run, "leftpad")
        self.assertIsNotNone(unsafe_score)
        self.assertFalse(unsafe_score["all_pass"])
        self.assertTrue(unsafe_score.get("compile_failed", False))

        # 2. Candidate with candidate-injected test must not inflate trusted test count
        cheat_run = self.root / "cheat_run"
        (cheat_run / "src").mkdir(parents=True)
        (cheat_run / "src" / "leftpad.rs").write_text(
            "pub fn leftpad(str: &str, padding: &str, min_len: usize, dest: &mut [u8]) -> usize { 0 }\n"
            "#[test]\n"
            "fn candidate_cheat() { assert!(true); }\n",
            encoding="utf-8",
        )
        cheat_score = adapter.score(cheat_run, "leftpad")
        self.assertIsNotNone(cheat_score)
        self.assertFalse(cheat_score["all_pass"])
        # Only the 1 trusted test in tests.rs should be evaluated (failed), not the candidate cheat test
        self.assertEqual(cheat_score["n_passed"], 0)
        self.assertEqual(cheat_score["n_criteria"], 1)

        # 3. Candidate with verified passing safe Rust implementation
        pass_run = self.root / "pass_run"
        (pass_run / "src").mkdir(parents=True)
        (pass_run / "src" / "leftpad.rs").write_text(
            "pub fn leftpad(str: &str, padding: &str, min_len: usize, dest: &mut [u8]) -> usize {\n"
            "    let mut i = 0;\n"
            "    let str_bytes = str.as_bytes();\n"
            "    let str_len = str_bytes.len();\n"
            "    let pad_str = if padding.is_empty() { \" \" } else { padding };\n"
            "    let pad_bytes = pad_str.as_bytes();\n"
            "    let npad = if str_len < min_len { min_len - str_len } else { 0 };\n"
            "    if dest.is_empty() {\n"
            "        return str_len + npad;\n"
            "    }\n"
            "    let mut dest_len = 0;\n"
            "    let limit = dest.len() - 1;\n"
            "    while dest_len < npad && dest_len < limit {\n"
            "        dest[dest_len] = pad_bytes[i];\n"
            "        dest_len += 1;\n"
            "        i = (i + 1) % pad_bytes.len();\n"
            "    }\n"
            "    for j in 0..str_len {\n"
            "        if dest_len >= limit {\n"
            "            break;\n"
            "        }\n"
            "        dest[dest_len] = str_bytes[j];\n"
            "        dest_len += 1;\n"
            "    }\n"
            "    dest_len\n"
            "}\n",
            encoding="utf-8",
        )
        pass_score = adapter.score(pass_run, "leftpad")
        self.assertIsNotNone(pass_score)
        self.assertEqual(pass_score["n_passed"], 1)
        self.assertEqual(pass_score["n_criteria"], 1)
        self.assertTrue(pass_score["all_pass"])
