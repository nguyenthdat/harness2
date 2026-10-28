# Upstream pins and patches

`harness2/config.py` is the authoritative pin table. All 31 benchmark dependencies
are managed as standalone checkouts tracking personal forks under `github.com/nguyenthdat/`
(or specified upstream remotes), NOT as git submodules, specifically avoiding git index
bloat, status lag, and IDE performance issues.

Clone or update dependencies using `bash scripts/clone_dependencies.sh`.

| Repository | Pinned Commit / Branch | Remote Origin |
|---|---|---|
| job-bench-eval | `fa03a17f9ff662f136798a274e10011c3aa00fd0` | `https://github.com/Job-Bench/job-bench-eval.git` |
| workbuddy-bench | `625b2233093ae4f23e76be28c1f341d41cc70373` | `https://github.com/nguyenthdat/workbuddy-bench.git` |
| harvey-labs | `b58a28ae9fde5ee4b810e53b4fd0a1915325a35d` | `https://github.com/harveyai/harvey-labs.git` |
| opencode | `23fb5e0516c99ac04a1aa46c193efda2e1b9bb24` | `https://github.com/anomalyco/opencode.git` |
| cybench | `ca483c6443f17a20ba7d6bac3d274859a1721e51` | `https://github.com/andyzorigin/cybench.git` |
| cve-bench | `9fb3e068f260b00dd899ef87951b88e9c60061f1` | `https://github.com/uiuc-kang-lab/cve-bench.git` |
| Rust-SWE-Bench | `6275b18be51ce3242de9e959a32260dd59909595` | `https://github.com/GhabiX/Rust-SWE-Bench.git` |
| CRUST-bench | `4b4702544b800a3821feea128c5b9e413665dc83` | `https://github.com/anirudhkhatry/CRUST-bench.git` |
| AgentRE-Bench | `654c4042bb0022b32b522769d99f76b103f5d504` | `https://github.com/agentrebench/AgentRE-Bench.git` |
| CyberSOCEval_data | `ce7daa5bc7da51559ca97476d2277be02631783e` | `https://github.com/CrowdStrike/CyberSOCEval_data.git` |
| BinaryAudit | `175b7ec1a39b7ba1545ae008a9e93106348c3b4e` | `https://github.com/QuesmaOrg/BinaryAudit.git` |
| autopenbench | `9c4890a7195896a399339f4b1b0e0c498fdd27cb` | `https://github.com/nguyenthdat/auto-pen-bench.git` |
| bountybench | `8ece6aab0b954f7c85b5705e69f0142eeaf2c5d1` | `https://github.com/nguyenthdat/bountybench.git` |
| hptsa | `ab4c77ce0ecd44fa9f1b9adc82779312342d9a2e` | `https://github.com/nguyenthdat/HPTSA.git` |
| hackworld | `7eddbe396d2adb3042482134fd08508e8ea21a3f` | `https://github.com/nguyenthdat/HackWorld.git` |
| nyu-ctf-bench | `4c5744f55a31a58e03d6118c9dbb1c18e5bbdfa9` | `https://github.com/nguyenthdat/NYU_CTF_Bench.git` |
| intercode | `c3e46d827cfc9d4c704ec078f7abf9f41e3191d8` | `https://github.com/nguyenthdat/intercode.git` |
| xbow-validation | `a16cb1ba0701b20d63913846536fc7b0672082af` | `https://github.com/nguyenthdat/validation-benchmarks.git` |
| maleval | `c906fa1e83d89c5f2473f9ef4f93320382cae3df` | `https://github.com/nguyenthdat/MalEval.git` |
| droidbench | `a57fa6f42f278591695672f1aa8b37c275139370` | `https://github.com/nguyenthdat/DroidBench.git` |
| ghera | `31dc21e922ecd327b6ec90a10a507aac7f813700` | `https://github.com/nguyenthdat/android-app-vulnerability-benchmarks.git` |
| mobilecybench | `d196c46fb23d9f6ad6391819ea62d025e1b29693` | `https://github.com/nguyenthdat/mobilecybench.git` |
| mas-crackmes | `d27a4857b79289cdd88fda423f519f8cd4c42db1` | `https://github.com/nguyenthdat/mas-crackmes.git` |
| mastg | `8bee312ba8fa45f7d617f0d806ac14920f2ad3d0` | `https://github.com/nguyenthdat/mastg.git` |
| cybergym | `c6fe2027d39471375920b92cf1025e23a99ffda5` | `https://github.com/nguyenthdat/cybergym.git` |
| cybergym-e2e | `d0ae0f02e76ebc084389bf21e755f4b41ac9765a` | `https://github.com/nguyenthdat/cybergym-e2e.git` |
| fuzzingbrain-bench | `6010bb4f98524157a13a2a68c3b6921d44c7f830` | `https://github.com/nguyenthdat/FuzzingBrain-Bench.git` |
| crsbench | `b4ec940f93ab531d70425cd274696651a84bf5e8` | `https://github.com/nguyenthdat/CRSBench.git` |
| oss-crs | `69cbcb6981f212fc125c7022eda880b4fdad02ce` | `https://github.com/nguyenthdat/oss-crs.git` |
| sec-bench | `31eb43485a3de47da260be0f978528b1f2314415` | `https://github.com/nguyenthdat/SEC-bench.git` |
| sec-bench-pro | `da80928ee20dc417ca6a068a1213e1d9d279df20` | `https://github.com/nguyenthdat/SEC-bench-Pro.git` |
| calif-publications | `0a1c715b06477a32155329bd0c535f30c91bdabf` | `https://github.com/nguyenthdat/publications.git` |
## Included patches

- `opencode-compat.diff`: fixes a moving Git dependency to the commit already in
  the upstream lock and adds Opus 4.8 adaptive-thinking support to the pinned
  provider adapter.
- `job-bench-eval-judge.diff`: passes reasoning effort, raises the judge output
  cap, and rejects empty completions.
- `harvey-labs-judge-vertex-anthropic.diff`: adds Claude and Gemini Vertex judges
  using ADC and improves malformed/ambiguous response handling.
- `workbuddy-bench-runtime.diff`: registers the release's executor adapters,
  preserves declared harness mounts, refreshes short-lived credentials, and
  preserves Gemini thought signatures across tool calls. It also fixes an
  undefined constant in the upstream Anthropic route support.

Patches are checked before applying and skipped if already applied. Derived runner
files belong in `harness2/third_party/{jb,lab,wb}_runner/`, which this copy does not
include; setup copies the LAB and WorkBuddy overlays into the upstream checkouts.

The upstream dependency locks are used for Python installations. OpenCode uses
Bun 1.3.11 and the patched lock. Codex uses the version in `config.CODEX_VERSION`.
JobBench's Hugging Face revision is resolved once for a download and recorded in
`dataset/main/.harness2-download.json`. WorkBuddy's dataset fetcher, as patched
by setup, verifies each archive against the dataset repository's `SHA256SUMS` and
refuses one it cannot verify; see
[the WorkBuddy guide](../docs/BENCHMARKS.md#workbuddy-bench). LAB task files are part of its pinned Git checkout.

These inputs support the public execution workflow. Historical paper runs may
have used different tasks, model deployments, and additional local tooling;
see [experiment notes](../README.md#experiments).
