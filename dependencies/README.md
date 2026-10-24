# Third-party code and data

Benchmark tools are downloaded into this directory and excluded from version
control. Pins are defined in `harness2/config.py`; setup commands are in the
[benchmark guides](../docs/BENCHMARKS.md).

| Upstream | License | Release integration |
|---|---|---|
| [Job-Bench/job-bench-eval](https://github.com/Job-Bench/job-bench-eval) | Apache 2.0 | Derived Codex shell runner, baseline harnesses, and judge patch |
| [harveyai/harvey-labs](https://github.com/harveyai/harvey-labs) | MIT | Derived LAB runners and Vertex judge patch |
| [Tencent/workbuddy-bench](https://github.com/Tencent/workbuddy-bench) | Custom Tencent license | Derived Harbor agents, harness configs, and runtime patch |
| [anomalyco/opencode](https://github.com/anomalyco/opencode) | MIT | Runtime dependency and compatibility patch |

The WorkBuddy license includes a territorial limitation concerning use within
the European Union. The derived runners, the patches, and the upstream license
notices that cover them are bundled in [`third_party/`](../third_party/README.md).

Dataset licenses are separate from software licenses. Data is downloaded from
its upstream distribution and is not redistributed in Harness². Generated
model configuration, cloud credentials, local task partitions, and run artifacts
are not release assets.


## Benchmark dependencies

All 31 benchmark dependencies are managed as standalone checkouts tracking personal forks under
`github.com/nguyenthdat/` (and upstream repositories where applicable), NOT as git submodules,
specifically to avoid git status lag, index bloat, and IDE performance degradation.

To clone or update all dependencies, or clone an individual benchmark, use:
```bash
# Clone/update all 31 dependencies
bash scripts/clone_dependencies.sh

# Dry run
bash scripts/clone_dependencies.sh --dry-run

# Clone or update a single dependency
bash scripts/clone_dependencies.sh autopenbench
```

| Path | Upstream repo | Fork / Remote repo | Branch / Pin | Domain | Status / Notes |
|---|---|---|---|---|---|
| `dependencies/job-bench-eval` | `Job-Bench/job-bench-eval` | `https://github.com/Job-Bench/job-bench-eval.git` | `fa03a17f9ff662f136798a274e10011c3aa00fd0` | SWE / Codex | Upstream tracking, judge patch |
| `dependencies/workbuddy-bench` | `Tencent/workbuddy-bench` | `https://github.com/nguyenthdat/workbuddy-bench.git` | `625b2233093ae4f23e76be28c1f341d41cc70373` | General / Sec / Office / Code | Fork, custom Tencent license |
| `dependencies/harvey-labs` | `harveyai/harvey-labs` | `https://github.com/harveyai/harvey-labs.git` | `b58a28ae9fde5ee4b810e53b4fd0a1915325a35d` | Legal / LAB | Upstream tracking, Vertex judge patch |
| `dependencies/opencode` | `anomalyco/opencode` | `https://github.com/anomalyco/opencode.git` | `23fb5e0516c99ac04a1aa46c193efda2e1b9bb24` | Agent substrate | Upstream tracking, runtime dep |
| `dependencies/cybench` | `andyzorigin/cybench` | `https://github.com/andyzorigin/cybench.git` | `ca483c6443f17a20ba7d6bac3d274859a1721e51` | CTF challenges | Upstream tracking (40 tasks) |
| `dependencies/cve-bench` | `uiuc-kang-lab/cve-bench` | `https://github.com/uiuc-kang-lab/cve-bench.git` | `9fb3e068f260b00dd899ef87951b88e9c60061f1` | Webapp 1-day CVEs | Upstream tracking (40 tasks) |
| `dependencies/Rust-SWE-Bench` | `GhabiX/Rust-SWE-Bench` | `https://github.com/GhabiX/Rust-SWE-Bench.git` | `6275b18be51ce3242de9e959a32260dd59909595` | Rust SWE | Upstream tracking |
| `dependencies/CRUST-bench` | `anirudhkhatry/CRUST-bench` | `https://github.com/anirudhkhatry/CRUST-bench.git` | `4b4702544b800a3821feea128c5b9e413665dc83` | C-to-Rust transpilation | Upstream tracking |
| `dependencies/AgentRE-Bench` | `agentrebench/AgentRE-Bench` | `https://github.com/agentrebench/AgentRE-Bench.git` | `654c4042bb0022b32b522769d99f76b103f5d504` | Desktop RE (ELF / PE) | Upstream tracking (23 levels, 33 binaries) |
| `dependencies/BinaryAudit` | `QuesmaOrg/BinaryAudit` | `https://github.com/QuesmaOrg/BinaryAudit.git` | `175b7ec1a39b7ba1545ae008a9e93106348c3b4e` | Backdoor detection | Upstream tracking (33 tasks) |
| `dependencies/autopenbench` | `lucagioacchini/auto-pen-bench` | `https://github.com/nguyenthdat/auto-pen-bench.git` | `9c4890a7195896a399339f4b1b0e0c498fdd27cb` (main) | Webapp pentest | Fork tracking (33 tasks) |
| `dependencies/bountybench` | `bountybench/bountybench` | `https://github.com/nguyenthdat/bountybench.git` | `8ece6aab0b954f7c85b5705e69f0142eeaf2c5d1` (main) | Webapp pentest | Fork tracking (40 bug bounties) |
| `dependencies/hptsa` | `uiuc-kang-lab/HPTSA` | `https://github.com/nguyenthdat/HPTSA.git` | `ab4c77ce0ecd44fa9f1b9adc82779312342d9a2e` (main) | Webapp pentest | Fork tracking (14 zero-days) |
| `dependencies/hackworld` | `GUI-Agent/HackWorld` | `https://github.com/nguyenthdat/HackWorld.git` | `7eddbe396d2adb3042482134fd08508e8ea21a3f` (main) | Webapp pentest (GUI agent) | Fork tracking |
| `dependencies/xbow-validation` | `xbow-engineering/validation-benchmarks` | `https://github.com/nguyenthdat/validation-benchmarks.git` | `a16cb1ba0701b20d63913846536fc7b0672082af` (main) | Webapp pentest | Fork tracking (sanity check only) |
| `dependencies/nyu-ctf-bench` | `NYU-LLM-CTF/NYU_CTF_Bench` | `https://github.com/nguyenthdat/NYU_CTF_Bench.git` | `4c5744f55a31a58e03d6118c9dbb1c18e5bbdfa9` (main) | Desktop RE / CTF | Fork tracking (CSAW CTF challenges) |
| `dependencies/intercode` | `princeton-nlp/intercode` | `https://github.com/nguyenthdat/intercode.git` | `c3e46d827cfc9d4c704ec078f7abf9f41e3191d8` (master) | Desktop RE / CTF | Fork tracking (picoCTF subset) |
| `dependencies/maleval` | `ZhengXR930/MalEval` | `https://github.com/nguyenthdat/MalEval.git` | `c906fa1e83d89c5f2473f9ef4f93320382cae3df` (main) | Android RE | Fork tracking (malware behavior, 255 apps) |
| `dependencies/droidbench` | `secure-software-engineering/droidbench` | `https://github.com/nguyenthdat/DroidBench.git` | `a57fa6f42f278591695672f1aa8b37c275139370` (master) | Android RE | Fork tracking (taint analysis) |
| `dependencies/ghera` | `JoyMitra/android-app-vulnerability-benchmarks` | `https://github.com/nguyenthdat/android-app-vulnerability-benchmarks.git` | `31dc21e922ecd327b6ec90a10a507aac7f813700` (master) | Mobile pentest | Fork tracking (60 benchmarks) |
| `dependencies/mobilecybench` | `bountybench/mobilecybench` | `https://github.com/nguyenthdat/mobilecybench.git` | `d196c46fb23d9f6ad6391819ea62d025e1b29693` (main) | Mobile pentest | Fork tracking (13 apps, 495 probes) |
| `dependencies/mas-crackmes` | `OWASP/mas-crackmes` | `https://github.com/nguyenthdat/mas-crackmes.git` | `d27a4857b79289cdd88fda423f519f8cd4c42db1` (master) | iOS RE | Fork tracking |
| `dependencies/mastg` | `OWASP/mastg` | `https://github.com/nguyenthdat/mastg.git` | `8bee312ba8fa45f7d617f0d806ac14920f2ad3d0` (master) | iOS RE reference | Fork tracking (MASTG guide) |
| `dependencies/cybergym` | `sunblaze-ucb/cybergym` | `https://github.com/nguyenthdat/cybergym.git` | `c6fe2027d39471375920b92cf1025e23a99ffda5` (main) | Vuln research (discovery) | Fork tracking |
| `dependencies/cybergym-e2e` | `sunblaze-ucb/cybergym-e2e` | `https://github.com/nguyenthdat/cybergym-e2e.git` | `d0ae0f02e76ebc084389bf21e755f4b41ac9765a` (main) | Vuln research (full lifecycle) | Fork tracking |
| `dependencies/fuzzingbrain-bench` | `fuzzingbrain/FuzzingBrain-Bench` | `https://github.com/nguyenthdat/FuzzingBrain-Bench.git` | `6010bb4f98524157a13a2a68c3b6921d44c7f830` (main) | Vuln research (open-ended) | Fork tracking |
| `dependencies/crsbench` | `sslab-gatech/CRSBench` | `https://github.com/nguyenthdat/CRSBench.git` | `b4ec940f93ab531d70425cd274696651a84bf5e8` (main) | Vuln research (AIxCC ground truth) | Fork tracking |
| `dependencies/oss-crs` | `ossf/oss-crs` | `https://github.com/nguyenthdat/oss-crs.git` | `69cbcb6981f212fc125c7022eda880b4fdad02ce` (main) | Vuln research (CRS platform) | Fork tracking |
| `dependencies/sec-bench` | `SEC-bench/SEC-bench` | `https://github.com/nguyenthdat/SEC-bench.git` | `31eb43485a3de47da260be0f978528b1f2314415` (main) | Vuln research (reproduction) | Fork tracking |
| `dependencies/sec-bench-pro` | `SEC-bench/SEC-bench-Pro` | `https://github.com/nguyenthdat/SEC-bench-Pro.git` | `da80928ee20dc417ca6a068a1213e1d9d279df20` (main) | Vuln research (V8/SM/kernel) | Fork tracking |
| `dependencies/calif-publications` | `califio/publications` | `https://github.com/nguyenthdat/publications.git` | `0a1c715b06477a32155329bd0c535f30c91bdabf` (main) | Methodology reference | Fork tracking (writeups) |
**Not vendored** (verified absent/incompatible): `wangyu-ovo/CREBench` (empty repo),
`HexHive/magma` + `panda-re/lava` (fuzzer benchmarks needing oracle construction),
`CyberGrandChallenge/samples` (archived DECREE ISA), `google/fuzzbench` (fuzzer
platform), `Evian-Zhang/lava-m-docker` (stale docker wrapper), AnonVul (no public
repo).

**Non-git assets**: WireBench (Android protocol RE) is a HuggingFace dataset
(`wirebench-neurips/wirebench`, CC-BY-4.0), not a git repo — fetch separately if
adopted.

## Recommended benchmark expansions

Research findings (October 2024) for additional security coverage:

### Web application penetration testing

**Priority 1: AutoPenBench** (LOW integration effort)
- **Source**: ETH Zurich, EMNLP 2025
- **Repository**: https://github.com/lucagioacchini/auto-pen-bench
- **Tasks**: 33 (22 in-vitro fundamentals + 11 real-world CVEs: Log4j, SambaCry, Spring4Shell)
- **Scoring**: Milestone-based evaluator (command + stage milestones) + flag capture
- **Runtime**: Docker, Python, SSH
- **License**: MIT
- **Integration effort**: LOW — Clean Python harness, MCP server included, milestone evaluator, structured tool schemas. Best documented for adapter integration.
- **Value**: Fills fundamental pentest workflow coverage (reconnaissance, exploitation phases) missing from current CVE-only benchmarks.

**Priority 2: BountyBench** (MEDIUM integration effort)
- **Source**: Stanford CRFM, NeurIPS 2025
- **Repository**: https://github.com/bountybench/bountybench
- **Tasks**: 40 real bug bounties across 25 codebases (Flask, Django, Express)
- **Scoring**: Binary flag + dollar-impact metrics (Detect/Exploit/Patch phases)
- **Runtime**: Docker, Python 3.11, API keys
- **License**: Apache 2.0
- **Integration effort**: MEDIUM — Multi-phase workflow (Detect → Exploit → Patch), needs three-stage adapter. Well-documented agent interface.
- **Value**: Real-world bug bounty coverage with economic impact metrics (9 OWASP Top 10 categories).

**Priority 3: HPTSA** (MEDIUM integration effort)
- **Source**: UIUC, EACL 2026
- **Repository**: https://github.com/uiuc-kang-lab/HPTSA
- **Tasks**: 14 zero-day web vulnerabilities
- **Scoring**: Binary flag capture (zero-day / one-day mode)
- **Runtime**: Docker, Python ≥3.10, OpenAI SDK
- **License**: Not stated
- **Integration effort**: MEDIUM — Multi-agent orchestration (supervisor + subagents), OpenAI SDK dependency. Needs adapter for task discovery.
- **Value**: Zero-day discovery evaluation (XSS, CSRF, SQLi, SSTI, arbitrary code execution).

**Alternative: NYU CTF Bench** (if CTF coverage desired)
- **Repository**: https://github.com/nyu-llm-ctf/nyu_ctf_bench
- **Tasks**: 200 CSAW CTF challenges (~33 web)
- **License**: GPL v2.0
- **Integration effort**: LOW-MEDIUM — Docker + Python interface, broad coverage but only 1/6 web-focused.

### Mobile application penetration testing (Android)

**Priority 1: MobileCybench** (HIGH integration effort, best-in-class)
- **Source**: Stanford/UC Berkeley (Dan Boneh, Dawn Song, Percy Liang), September 2026
- **Repository**: https://github.com/bountybench/mobilecybench
- **Tasks**: 13 production-grade Android apps (Audiobookshelf, Nextcloud, phpMyAdmin, Termux, Wallabag, Paperless-NGX, Komga, Firefly III, Grocy, Bookstack, Mealie, SearXNG, Flaresolverr)
- **Attack surface**: 495 executable probes across CIAA properties (Confidentiality, Integrity, Availability, Access Control)
- **Scoring**: Property-based executable probes (not simple flag checks); agent exploits replayed against running app
- **Attack settings**: 2 attacker models (malicious app on device, remote attacker with low-privilege account) × 2 access levels (APK-only obfuscated, source code available) = 4 configurations per app
- **Runtime**: Docker + Android emulator + per-app backend services
- **License**: To be determined
- **Integration effort**: HIGH — Requires Docker orchestration, per-app backend setup, probe infrastructure, and emulator automation. Oracle is sophisticated (property-based probes vs. simple flag checks). Adapters would need to wrap Docker + probe runner.
- **Value**: Best-in-class realistic agentic mobile pentest evaluation. Top agent (OpenCode GPT-5.6-Sol) achieved 53.8% probe trigger rate (malicious-app, APK-only), demonstrating genuine difficulty.

**Priority 2: Ghera** (MEDIUM integration effort, training-focused)
- **Source**: JoyMitra et al. (academic research)
- **Repository**: https://github.com/JoyMitra/android-app-vulnerability-benchmarks
- **Tasks**: 60 Android vulnerability benchmarks (ICC, Storage, Web, System APIs, Network, Crypto)
- **Scoring**: Requires per-benchmark oracle scripting (exploit success = pass); each benchmark includes vulnerable app, malicious exploiter app, secure app, and instructions
- **Runtime**: Android emulator (4.4–7.1 target), ADB for APK installation
- **License**: Academic/research (not explicitly stated)
- **Integration effort**: MEDIUM — Needs oracle scripts per-benchmark. Exploitation patterns are well-documented. Reusable as training base.
- **Value**: Lower-hanging fruit for mobile pentest coverage; pairs well with MobileCybench (training + evaluation split).

**Note**: No equivalent agentic iOS pentest benchmark exists as of October 2024. iOS pentest evaluation remains a genuine gap in the ecosystem.

### Current coverage with proposed additions

**Existing security benchmarks** (integrated):
- CVE-Bench: 40 CVE one-day exploits (web apps)
- Cybench: 40 CTF tasks
- WorkBuddy sec: 60 tasks (51 single-step, 9 multi-step)
- **Total**: 140 tasks

**With AutoPenBench + BountyBench**:
- CVE real-world: CVE-Bench (40) + AutoPenBench (11 real CVEs) = 51
- Bug bounty: BountyBench (40)
- Pentest fundamentals: AutoPenBench (22 in-vitro)
- CTF: Cybench (40)
- Security tasks: WorkBuddy (60)
- **Total webapp security**: ~213 tasks

**With MobileCybench** (new domain):
- Android pentest: 13 apps × 4 attack settings = 52 configurations, 495 probes
- **First mobile pentest coverage** in harness2

### Reverse engineering and binary analysis

**Current integrated RE benchmarks**:
- **AgentRE-Bench**: 23 levels, 33 binaries (13 Linux ELF x86-64 + 10 Windows PE32+); malware triage, technique identification (C2, injection, obfuscation); deterministic ground-truth scoring; static-only; MIT license; active (V3 Aug 2026)
- **BinaryAudit**: 33 tasks (lighttpd, dnsmasq, Dropbear, Sozu, Caddy); backdoor detection in real open-source network software; Harbor framework scoring; static (Ghidra/Radare2); Apache 2.0; active (Feb 2026)
- **Total**: 56 tasks

**Priority 1: NYU CTF Bench (RE subset)** (LOW integration effort)
- **Source**: NYU, NeurIPS 2024
- **Repository**: https://github.com/NYU-LLM-CTF/NYU_CTF_Bench
- **Tasks**: Estimated 30–50 reverse engineering tasks (from 200 total CSAW CTF challenges; requires filtering `challenge.json` for `"category": "rev"`)
- **Binary types**: Mixed (ELF, PE, scripts, forensics artifacts)
- **Scoring**: Flag validation via `nyuctf` Python package
- **Runtime**: Docker (docker-compose for server-based challenges), Python
- **License**: GPL v2.0
- **Integration effort**: LOW — Dockerized, programmatic Python API (`CTFDataset`, `CTFChallenge`), public flags. Need to filter RE subset from mixed categories.
- **Value**: Real CTF challenges, diverse difficulty, community-validated, interactive bash environment. Fills educational CTF gap (AgentRE/BinaryAudit are triage-focused).

**Priority 2: InterCode-CTF (RE subset)** (LOW integration effort)
- **Source**: Princeton NLP, 2023
- **Repository**: https://github.com/princeton-nlp/intercode/tree/master/data/ctf
- **Tasks**: 27 reverse engineering tasks (from 100 total picoCTF-derived)
- **Binary types**: picoCTF challenges (ELF, scripts)
- **Scoring**: Exact flag match (gold flag in `ic_ctf.json`)
- **Runtime**: Docker (Ubuntu), InterCode framework
- **License**: Academic use (Princeton NLP)
- **Integration effort**: LOW — Public dataset (`ic_ctf.json`, `task_assets/`), deterministic scoring, explicit RE count.
- **Value**: Smaller than NYU but explicit RE count, picoCTF provenance. **Note**: Contamination risk (picoCTF is public training data).

**Priority 3: CREBench** (LOW integration effort, crypto-specialized)
- **Source**: May 2026
- **Repository**: https://github.com/wangyu-ovo/CREBench
- **Paper**: https://arxiv.org/abs/2604.03750
- **Tasks**: 432 challenges (48 crypto algorithms × 3 key scenarios × 3 difficulty levels)
- **Task structure**: 4 progressive tasks per challenge: L1 algorithm identification, L2 key/IV extraction, L3 wrapper code reimplementation, L4 flag recovery
- **Binary types**: ELF x86-64, stripped executables with decompiled pseudocode provided
- **Scoring**: Automated flag verification (pass@k evaluation)
- **Runtime**: Docker, Python, LiteLLM, Codex CLI (optional)
- **License**: Not specified
- **Integration effort**: LOW — Deterministic scoring, public dataset, reproducible Docker setup. Narrow domain (crypto only).
- **Value**: Cryptographic reverse engineering (AES, RSA, RC4, DES variants, key recovery, algorithm identification). Fills gap not covered by AgentRE-Bench/BinaryAudit (neither test crypto primitives).

**Priority 4: MAGMA** (MEDIUM integration effort, requires oracle construction)
- **Source**: EPFL HexHive, 2020
- **Website**: https://hexhive.epfl.ch/magma/
- **Repository**: https://github.com/HexHive/magma
- **Paper**: https://doi.org/10.1145/3428334
- **Tasks**: 138 real bugs across 7 projects (libpng, libtiff, libxml2, poppler, openssl, sqlite3, php)
- **Binary types**: ELF x86-64 (Linux libraries)
- **Scoring**: MAGMA canaries report bug reach/trigger/detection states — **ground truth exists, agent harness required**
- **Runtime**: Docker (MAGMA build images), fuzzer infrastructure (AFL++, libFuzzer)
- **License**: Apache 2.0
- **Integration effort**: MEDIUM — Strong ground truth (138 CVE-mapped real bugs, canaries), but MAGMA is fuzzer benchmark. Needs agent interface to analyze binaries + generate triggering inputs. **Best ROI for dynamic vulnerability discovery agents.**
- **Value**: Real bug corpus with ground-truth triggering (not synthetic). Tests vulnerability discovery + triggering input generation. Requires dynamic analysis capability (beyond static-only scope of current AgentRE-Bench).

**Priority 5: CrackMeBench** (LOW integration effort, small scale)
- **Paper**: https://arxiv.org/abs/2605.10597 (Jun 2026)
- **Tasks**: 20 tasks in v0 (8 public calibration + 12 generated main-score tasks)
- **Binary types**: ELF x86-64 (C, Rust, Go templates)
- **Scoring**: Private executable oracle (pass@1, pass@3)
- **Runtime**: Docker (no-network sandbox), standard RE tools
- **License**: Educational use (not for DRM/malware/intrusion per paper)
- **Integration effort**: LOW — Deterministic oracle-based scoring, educational CrackMe-style validation.
- **Value**: Keygen generation, password recovery, input validation logic (complementary to malware-focused AgentRE/BinaryAudit). **Small scale** (20 tasks) vs AgentRE (23 levels) and BinaryAudit (33 tasks). Educational RE vs operational malware triage.

**Alternative: SRE-Bench** (requires partnership, contamination-free)
- **Source**: Columbia/Vals AI (arXiv Aug 2026)
- **Paper**: https://arxiv.org/abs/2608.11469
- **Website**: https://daplab.cs.columbia.edu/benchmarks/sre-bench/
- **Tasks**: 1,572 graded tasks across 262 binary instances from 19 programs (~16.9K LoC avg)
- **Binary types**: C, C++, Rust, Go; ELF/PE; x86-64, ARM; network protocols, firmware, games, file parsers, malware
- **Task types**: 6 RE tasks per binary (protocol reverse engineering, vulnerability identification, behavior recovery, format parsing, malware analysis)
- **Scoring**: Deterministic grading server; 44 in-house anti-analysis mechanisms
- **Runtime**: Isolated containers, domain-specific RE toolkits
- **License**: Not specified (binaries are private)
- **Integration effort**: **Requires Columbia/Vals AI partnership** — Binaries are not public to maintain contamination-free status. Cannot self-host.
- **Value**: **Best-in-class** contamination-free, realistic scale (avg 16.9K LoC vs AgentRE's synthetic samples), anti-analysis protections (44 mechanisms), cross-domain tasks (firmware, malware, protocols). Current SOTA: GPT-5.6-Sol 31.5% solve rate (vs AgentRE V3: Kimi K3 68% main score). Fills gap: AgentRE/BinaryAudit use known or synthetic samples; SRE-Bench prevents memorization.

**Not recommended**:
- **DARPA CGC** (250 DECREE binaries): Archived (2016), non-standard ISA (not ELF/PE), requires DECREE emulator. High adaptation cost. **Reference only.**
- **LAVA-M** (thousands synthetic bugs in 4 coreutils): Fuzzing benchmark, requires agent harness construction. **Lower priority** than MAGMA (synthetic vs real bugs).
- **Juliet Test Suite** (64,099 CWE test cases): Source-level static analyzer benchmark; binary adaptation (ROMEO) exists but needs harness + scoring. **High effort**, synthetic patterns. Better for CWE taxonomy coverage testing than realistic binary RE.
- **EMBER/SOREL-20M** (1.1M/20M malware samples): Malware **classification** datasets (ML features), not RE. No tasks for technique discovery, C2 extraction, exploit generation. **Wrong task type.**
- **FuzzBench**: Fuzzer benchmarking platform, not agentic RE. **Not applicable.**

### Current coverage with proposed additions (RE)

**Existing RE benchmarks** (integrated):
- AgentRE-Bench: 23 levels (malware triage, technique identification)
- BinaryAudit: 33 tasks (backdoor detection, real network software)
- **Total**: 56 tasks

**With NYU CTF + InterCode-CTF + CREBench**:
- Malware triage: AgentRE-Bench (23 levels)
- Backdoor detection: BinaryAudit (33 tasks)
- CTF challenges: NYU CTF (~30–50 RE) + InterCode-CTF (27 RE) = ~57–77 tasks
- Cryptographic RE: CREBench (432 challenges)
- **Total RE coverage**: ~578–618 tasks (10× expansion)

**With MAGMA** (dynamic vulnerability discovery):
- Real bug corpus: 138 CVE-mapped vulnerabilities with triggering input generation
- **New capability**: Dynamic analysis, exploit triggering (current benchmarks are static-only)


### Mobile reverse engineering (Android + iOS)

**Distinct from mobile pentest** — RE focuses on static/dynamic binary analysis (APK/DEX/IPA/Mach-O), malware triage, deobfuscation, and vulnerability identification without exploit execution. Pentest executes exploits against running apps.

#### Android RE (mature benchmarks exist)

**Priority 1: MalEval** (BEST, MEDIUM integration effort)
- **Source**: ISSTA 2026
- **Paper**: "Is 'Knowing It's Malicious' Enough? Evaluating LLMs for Fine-Grained Malware Behavior Auditing"
- **Repository**: https://github.com/ZhengXR930/MalEval
- **Dataset**: https://huggingface.co/datasets/Xinzxr/MalEval
- **Tasks**: 255 Android applications (200 archived malware, 30 recent, 25 benign)
- **Binary types**: APK/DEX (Androguard decompilation)
- **Analysis type**: Static analysis with function-level reasoning
- **Agent's job**: Analyze decompiled code → generate function summaries, entry points, call chains → produce behavior reports → map to ground-truth malware behaviors
- **Scoring oracle**: Multi-metric deterministic (Binary F1, Report Quality via LLM-as-judge, False Positive Correction Rate, True Positive Maintenance Rate, Category-level F1)
- **Runtime**: Python 3.10+, Androguard, LangGraph, model API keys (OpenAI/Anthropic/DeepSeek)
- **License**: Other (excludes third-party malware samples)
- **Maintenance**: Active (Aug 2026 ISSTA paper, recent commits)
- **Integration effort**: MEDIUM — Clean Python pipeline, separated static analysis and LLM evaluation stages, model-agnostic (registry in `model_registry.yaml`), deterministic scoring implemented, released dataset with metadata. **Requires isolated environment for APK handling** (malware samples).
- **Value**: Behavior-level malware understanding (not just family classification). Well-structured adapter candidate. **Scale**: 255 tasks vs desktop RE's 33 (AgentRE) and 33 (BinaryAudit).

**Priority 2: CAMA** (function-level RE, MEDIUM effort, dataset access unclear)
- **Source**: ISSTA Companion 2025
- **Paper**: "On Benchmarking Code LLMs for Android Malware Analysis"
- **Repository**: Zenodo dataset 10.5281/zenodo.15155916 (⚠️ 403 forbidden as of Oct 2026 — may not be public yet)
- **Tasks**: 118 Android malware samples → **7.5 million distinct functions** (13 malware families, 6 categories)
- **Binary types**: APK → DEX → decompiled Java (Androguard)
- **Analysis type**: Static analysis, function-level code understanding
- **Agent's job**: Malicious function identification (via maliciousness scores), malware purpose summarization, refined function naming
- **Scoring oracle**: Multi-metric (Maliciousness Consistency Score, Name Consistency Score, Maliciousness-based Fidelity Score via classifier confidence drop, Semantic Relevance vs ground-truth descriptions)
- **Runtime**: Python, Androguard, Code LLM endpoints (CodeLlama, StarChat, CodeT5, PLBART evaluated)
- **License**: CC BY-NC-SA 4.0 (paper)
- **Integration effort**: MEDIUM — Smaller sample count vs MalEval (118 vs 255) but **much larger function corpus** (7.5M functions). Focus on Code LLM understanding rather than end-to-end malware reporting. Well-defined metrics for function-level analysis.
- **Blockers**: Dataset may not be fully public (Zenodo link failed); wait for public release.
- **Value**: Function-level RE specialization (complements MalEval's app-level reports).

**Priority 3: AMD (Android Malware Dataset)** (BEST behavioral ground truth, MEDIUM-HIGH effort, oracle construction needed)
- **Source**: ArgusLab 2017
- **Homepage**: http://amd.arguslab.org
- **Paper**: "Deep Ground Truth Analysis of Current Android Malware" (ArgusLab Tech Report 2017-2)
- **Tasks**: 24,650 total samples → **405 deeply analyzed** (3 per variety × 135 varieties)
- **Structure**: 71 malware families → **135 varieties** (semantically distinct behavior variants)
- **Binary types**: APK
- **Ground truth**: Family labels (71) + **variety labels (135)** + **detailed behavioral descriptions** for each variety (manual expert analysis)
- **Collection period**: 2010–2016
- **Scoring oracle**: **Needs construction** — Variety labels + behavioral descriptions provided; could build variety classification, behavior-matching, malware-family disambiguation tasks
- **Runtime**: Depends on oracle construction
- **License**: Research use
- **Integration effort**: MEDIUM-HIGH — Most detailed behavioral ground truth of any Android dataset (135 varieties with expert-verified descriptions). Requires oracle construction (no existing scoring framework). Samples dated (2010–2016) but more recent than Drebin.
- **Value**: Best candidate for behavior-rich RE tasks (identify variety, match behaviors, explain maliciousness). **Scale**: 135–405 tasks vs desktop's 33.

**Priority 4: AndroTruth** (BEST label reliability, MEDIUM effort, oracle construction needed)
- **Source**: ThreatIntel-Andro (arXiv Oct 2025)
- **Paper**: "AndroTruth: A Reliable Benchmark Android Malware Dataset Derived from Technical Expert Reports"
- **Paper URL**: https://arxiv.org/html/2510.16835
- **Tasks**: 8,172 samples across **187 malware families**
- **Binary types**: APK
- **Ground truth**: **Expert-verified family labels** from 199 security reports (22 vendors) — not AV consensus (addresses label noise problem in datasets like AndroZoo)
- **Collection period**: Reports from Feb 2016 – June 2025
- **Scoring oracle**: **Needs construction** — Family classification oracle (187 families); could add behavior extraction from linked threat reports
- **Runtime**: Depends on oracle construction
- **License**: Not specified in abstract
- **Integration effort**: MEDIUM — Clean family classification; most reliable labels (expert-verified, not AV voting). Could mine threat reports for behavioral tasks. No behavioral descriptions beyond family (vs AMD's variety-level detail).
- **Value**: Most reliable family classification ground truth (187 families). **Scale**: 187+ tasks vs desktop's 33.

**Priority 5: CICMalDroid-2020** (LARGE scale, MEDIUM effort, oracle construction needed)
- **Source**: UNB CIC
- **Homepage**: https://unb.ca/cic/datasets/maldroid-2020.html
- **Kaggle**: https://www.kaggle.com/datasets/hasanccr92/cicmaldroid-2020
- **Tasks**: 17,341 collected → 13,077 analyzed → **11,598 final samples**
- **Categories**: 5 balanced categories (Benign: 1,795, Riskware: 2,546, SMS malware: 3,904, Banking: 2,100, Adware: 1,253)
- **Binary types**: APK
- **Ground truth**: Category labels + dynamic behavior features (CopperDroid analysis)
- **Collection period**: Dec 2017 – Dec 2018
- **Scoring oracle**: **Needs construction** — Category classification oracle (5-way); could add malicious behavior detection tasks
- **Runtime**: Depends on oracle construction
- **License**: Research use
- **Integration effort**: MEDIUM — Modern samples (2017–2018), balanced categories, dynamic features available. Only 5 categories (less granular than AMD's 135 varieties or AndroTruth's 187 families). **Scale**: 11,598 samples >> desktop RE (AgentRE-Bench 33, BinaryAudit 33).
- **Value**: Category-level malware triage (5-way classification), large-scale evaluation.

**Not recommended** (Android):
- **Drebin** (5,560 samples, 179 families): Classic benchmark (2014), dated samples (2010–2012), requires email access request. **Lower priority** than modern alternatives.
- **PRAGuard** (10,479 samples, 7 obfuscation techniques): Only large-scale obfuscation benchmark, but base samples dated (MalGenome/Contagio), narrow focus (obfuscation not broad RE). **Niche use case.**
- **DroidBench** (190 test cases): Well-established taint-analysis benchmark, but narrow focus (information-flow vulnerabilities only). **Partial fit** (not broad malware RE).
- **Ghera** (25 vulnerabilities): Exploit benchmarks, overlaps with mobile pentest. **Wrong task type** (pentest not RE).

**Vapor/inaccessible**:
- **CAMA dataset**: Zenodo link 403 (Oct 2026)
- **Malaika**: Framework in paper, no public repo yet
- **WireBench**: HuggingFace dataset exists but task count unclear
- **AndroZoo**: Requires API key (academic credentials)

#### iOS RE (critical gap — no mature benchmarks)

**Best available: UnCrackable L1–L4** (OWASP MAS Crackmes, LOW effort, insufficient scale)
- **Source**: OWASP MSTG
- **Homepage**: https://mas.owasp.org/crackmes/iOS/
- **Repository**: https://github.com/OWASP/mas-crackmes
- **Tasks**: 4–5 IPA challenges (Level 1, 2, 3, r2pay Level 4, Android License Validator)
- **Binary types**: IPA / Mach-O (ARM64)
- **Analysis type**: Static RE (Hopper/IDA/Ghidra) + dynamic (Frida/lldb)
- **Agent's job**: Extract hidden secret string, bypass anti-tampering, reverse obfuscation/whitebox crypto
- **Scoring oracle**: PARTIAL — Each challenge has known secret (ground truth); binary comparison (correct/incorrect)
- **Runtime**: Hopper/IDA/Ghidra (static), Frida/lldb (dynamic)
- **License**: Open source
- **Integration effort**: LOW — Simple string comparison oracle, well-documented solutions.
- **Blockers**: **Insufficient scale** (4–5 challenges vs Android's 255–24K, desktop's 33). Good for proof-of-concept iOS adapter, **not production benchmark**.

**Alternative: DVIA-v2** (OWASP MSTG, MEDIUM-HIGH effort, single app)
- **Source**: OWASP MSTG (MASTG-APP-0024)
- **Repository**: OWASP MSTG GitHub
- **Tasks**: 15+ known vulnerabilities in **1 app** (insecure storage, improper cryptography, etc.)
- **Binary types**: IPA / Mach-O (Swift-based)
- **Ground truth**: Documented vulnerabilities (no automated scoring framework)
- **Scoring oracle**: **Needs construction** — Define "vulnerability identified" criteria
- **Integration effort**: MEDIUM-HIGH — Single app, oracle construction required.
- **Blockers**: **Only 1 app** with ~15 vulns (vs Android's hundreds/thousands of samples). Insufficient for benchmark (needs 20+ apps minimum).

**iOS gap analysis**:

**What doesn't exist**:
- iOS malware family datasets (like Android's Drebin/AMD/AndroTruth)
- iOS malware behavior benchmarks (like MalEval/CAMA)
- Large-scale iOS RE challenge collections
- iOS obfuscation benchmarks

**Why iOS is underserved**:
1. iOS malware is rare in the wild (App Store review + sandboxing vs Android's open ecosystem)
2. Fewer public iOS binaries (vs APKs easily obtained)
3. iOS analysis requires macOS + Xcode (vs Android's Linux/Windows portability)
4. Research community focuses on Android (larger attack surface)
 **Smallest credible iOS construction**:
- Collect 20–30 iOS IPAs (mix of benign and vulnerable apps)
- Combine UnCrackable (4–5) + DVIA-v2 (1 app, 15+ vulns) + other public IPAs with documented issues
- Build oracle: vulnerability detection (binary per vuln type) or secret extraction
- **Realistic scale**: 20–35 tasks vs desktop RE's 33, Android's 255–24K
- **Effort**: MEDIUM-HIGH (manual vulnerability annotation required)

**Recommendation**: iOS is a **gap** requiring custom construction. Consider skipping iOS initially or wrapping UnCrackable for proof-of-concept.

### Coverage projection (mobile RE)

**With MalEval + AMD + AndroTruth** (Android):
- Malware behavior auditing: MalEval (255 tasks)
- Behavioral ground truth: AMD (135 varieties, 405 deeply analyzed)
- Reliable family classification: AndroTruth (187 families)
- **Total Android RE**: ~577 tasks vs desktop's 56 (10× expansion)

**With UnCrackable** (iOS):
- RE challenges: 4–5 tasks (proof-of-concept only)
- **iOS remains 1–2% of Android scale** (gap)

### Vulnerability research (zero-day discovery)

**Distinct from pentest/RE** — agent **discovers** previously unknown vulnerabilities in source code or binaries (novel bug discovery, CVE assignment, PoC generation for unseen bugs), not just exploiting known CVEs.

**Reference case: calif.io PHP CVEs** (CVE-2026-109618, CVE-2026-109619)
- **What happened**: Real production zero-days — two critical PHP RCE vulnerabilities ("php2shell," CVSSv4.0 9.2), disclosed Oct 21, 2026, patched in PHP 8.5.12/8.4.27/8.3.36/8.2.35. Affected PHP 5.4.0 → 8.5.11, all web SAPIs. Wild exploitation confirmed pre-disclosure.
- **Who**: calif.io is a **security research firm** (offensive security + AI red-teaming consultancy), not a benchmark. Discovery by **human-AI hybrid team** — researcher LCFR/Thai Duong driving Claude as "audit buddy" under OpenAI's "Patch the Planet" initiative.
- **Methodology**: Multi-agent audit pipeline documented in `califio/publications` repo (768★): (1) target discovery, (2) shared-context gathering, (3) parallel agent sweep identifying 12 bug classes, (4) verification agent constructing triggers + tracing lifecycles, (5) synthesis into severity-ranked findings. Built reusable Claude skill `/php-unserialize-audit` from ~20 historical advisories.
- **Value for harness2**: Methodology exemplar + production validation, not an eval. `califio/publications` provides concrete audit-agent pattern to replicate. No scoring oracle, task set, or harness exists.
- **Sources**: [calif.io/php2shell](https://calif.io/php2shell/), [github.com/califio/publications](https://github.com/califio/publications), [MADBugs/php/WRITEUP.md](https://github.com/califio/publications/blob/main/MADBugs/php/WRITEUP.md), [CERT VU#763488](https://www.kb.cert.org/vuls/id/763488)

#### Tier A: Pure discovery benchmarks (agent finds bug with weak/no prior)

**Priority 1: CyberGym Level 0** (HIGH effort, best-in-class)
- **Source**: UC Berkeley, ICLR 2026
- **Repository**: https://github.com/sunblaze-ucb/cybergym (969★)
- **Paper**: https://arxiv.org/abs/2506.02548
- **Tasks**: 1,507 real OSS-Fuzz vulnerabilities across 188 C/C++ projects
- **Task structure (Level 0)**: Agent gets only pre-patch codebase (~1,117 files / ~387K LOC), **no vulnerability description**, must find *any* sanitizer-triggerable bug and produce PoC
- **Scoring oracle**: Execution-based, deterministic (sanitizer crash on pre-patch binary, no crash on post-patch). No LLM judge needed.
- **Difficulty ladder**: L0 (discovery, codebase only) → L1 (+text description) → L2 (+crash stack trace) → L3 (+ground-truth patch, one-day/patch-diffing)
- **Zero-day validation**: Paper's runs found **34 zero-days** + 18 incomplete patches across 431 projects (4 CVEs assigned, 10 patched) — proving discovery setting produces real findings
- **Runtime**: Docker, Python. Data ~240GB benchmark (HuggingFace `sunblaze-ucb/cybergym`); binary-only mode ~130GB; full compile env ~10TB. Self-hosted PoC-submission server.
- **License**: Apache 2.0
- **Maintenance**: Active (updated Oct 2026), adopted in frontier model cards (Claude, Kimi, GLM)
- **Integration effort**: HIGH — Deterministic oracle, well-documented server workflow. Main cost = data download size and per-task Docker builds. **Level 0 is exactly the "find an unknown bug" task requested.**

**Priority 2: CyberGym-E2E** (HIGH effort, full-lifecycle)
- **Source**: ICML 2026
- **Repository**: https://github.com/sunblaze-ucb/cybergym-e2e (88★)
- **Paper**: https://arxiv.org/abs/2606.04460
- **Tasks**: 920 real vulnerabilities across 139 OSS projects (OSS-Fuzz-sourced)
- **Task structure**: **Full lifecycle explicitly scored** — (1) *identify* vulnerabilities in real codebase with no description, (2) *generate* PoC, (3) *patch*. Automated build envs, ground-truth patches, dev-written unit tests.
- **Scoring oracle**: Execution-based for all three stages
- **Runtime**: Docker per-task envs
- **License**: Not specified
- **Maintenance**: Active (Oct 2026)
- **Integration effort**: HIGH — Purpose-built for exact "discover → PoC → patch" pipeline. Newer/less battle-tested than CyberGym but directly on-target.

**Priority 3: FuzzingBrain-Bench (FB-Bench V1)** (HIGH effort, purest discovery oracle)
- **Source**: Texas A&M / o2lab (AIxCC 4th-place FuzzingBrain team)
- **Repository**: https://github.com/fuzzingbrain/FuzzingBrain-Bench (9★)
- **Paper**: https://arxiv.org/abs/2608.25158 (CC-BY)
- **Tasks**: 77 challenges across 43 OSS projects (36 C, 32 C++, 9 Java/JVM)
- **Task structure**: **Open-ended bug discovery** — agent gets project + sanitizer-instrumented harness in self-contained Docker, generates inputs triggering **as many distinct crash signatures as possible** (not PoC for predefined bug)
- **Scoring oracle**: Count of distinct crash signatures (capped, difficulty-weighted). No dependence on ground-truth bug mapping.
- **Runtime**: Docker (self-contained challenges)
- **License**: CC-BY
- **Maintenance**: Active (updated Oct 2026)
- **Integration effort**: HIGH — Pure-discovery scoring, lightweight Docker challenges, actively maintained lineage (FuzzingBrain CRS). Smaller scale than CyberGym but **truest "discovery" oracle** of the set.
- **Results**: Claude Opus 4.8 best — crashed 60/77, score 196/579. 13 challenges uncracked by all three Claude models.

**Priority 4: CRSBench + OSS-CRS** (MEDIUM-HIGH effort, AIxCC ground truth)
- **Source**: Georgia Tech SSLab + OpenSSF (DARPA AIxCC production benchmark)
- **Repository**: https://github.com/sslab-gatech/CRSBench
- **Platform**: https://github.com/ossf/oss-crs (OpenSSF)
- **Tasks**: **124 benchmark tasks** (63 C/C++, 61 JVM) with **315 CPVs** (Challenge Project Vulnerabilities) across **91 CWEs**. Bundles AIxCC Final Challenge Set + Exhibition Round + Team Atlanta's n-day-derived challenges.
- **Agent does**: Run Cyber Reasoning System against challenge project — **find bugs (PoVs), patch them, file SARIF reports, bundle related artifacts**
- **Scoring**: Rewards correct PoVs + patches + SARIF + correct bundling, with accuracy multiplier and time decay (mirrors AIxCC official scoring)
- **Ground truth**: Final round = 54 unique synthetic CPVs injected across 63 challenges on real projects (curl, freerdp, libxml2, wireshark, systemd, OpenSSL, log4j, POI, Tika) **plus 18 real non-synthetic vulnerabilities found by CRSs** (6 C, 12 Java) and ~25 zero-days total
- **Runtime**: Linux + Docker; HuggingFace dataset `sslab-gatech/crsbench-dataset` (134 projects)
- **License**: MIT
- **Maintenance**: Active
- **Integration effort**: MEDIUM-HIGH — Most rigorous ground-truth + scoring of any option, but **heaviest lift** (designed for full multi-component CRS: find+patch+SARIF+bundle, not single agent loop). **Best path**: adopt challenge set + PoV-verification oracle, wrap in simpler agent scaffold rather than full OSS-CRS.
- **Sources**: [CRSBench](https://github.com/sslab-gatech/CRSBench), [oss-crs.openssf.org/crsbench](https://oss-crs.openssf.org/crsbench), [AIxCC challenges](https://archive.aicyberchallenge.com/challenges/), [DARPA results](https://www.darpa.mil/news/2025/aixcc-results)

**Priority 5: AnonVul** (MEDIUM effort, anti-contamination specialized)
- **Source**: arXiv Oct 2026
- **Paper**: https://arxiv.org/abs/2610.17542
- **Tasks**: 132 application-level **business-logic** vulnerabilities across 9 languages, anonymized to defeat memorization
- **Task structure**: Discover + exploit logic vuln in sandboxed app with embedded oracles (black-box and grey-box tracks)
- **Scoring oracle**: Expert-written oracles injected at key exploitation steps + differential PoC verification
- **Anti-contamination**: Anonymization defeats memorization — restoring software identity doubles discovery (21.25%→40.83%), confirming it measures *reasoning* not recall
- **Integration effort**: MEDIUM — **Only benchmark specifically hardened against memorization/contamination for discovery**. Complements memory-safety focus of CyberGym/FB-Bench with logic bugs.
- **Blocker**: Repo availability not confirmed in abstract — **verify artifact release before committing**.
- **Value**: Best agent only 23.11% — very hard. Business-logic vulnerabilities (not covered by memory-safety benchmarks).

**Alternative: SEC-bench Pro** (MEDIUM-HIGH effort, reproduction-under-guidance not pure discovery)
- **Source**: SEC-bench team
- **Repository**: https://github.com/SEC-bench/SEC-bench-Pro
- **Paper**: https://arxiv.org/abs/2605.26548
- **Tasks**: 344 **validated real vulnerabilities** across V8, SpiderMonkey, Linux kernel (memory-safety, sandbox, JIT, race conditions, kernel subsystems)
- **Task**: Given disclosed bug report + trigger instructions, produce working PoC input (framed as "hunting real vulnerabilities" but provides bug report — **closer to CyberGym L1 than L0**)
- **Scoring oracle**: **LLM-based judge** for PoC grading (rule-based judges proved too brittle at this complexity). Staged execution grading.
- **Runtime**: Docker per case; Linux MCP sandbox uses KVM/QEMU
- **License**: Not specified
- **Maintenance**: Active, adopted by OpenAI for model eval
- **Integration effort**: MEDIUM-HIGH — Hardest/most prestigious target set; LLM-judge dependency adds noise vs pure-execution oracles. Strong for measuring deep exploitation ability; **weaker as pure discovery signal** (bug disclosed in prompt).
- **Results**: Codex+GPT-5.5 solved 58%; Claude Code+Opus 4.6 most-completed but times out; GLM-5 only 13/344. Construction surfaced 3 real V8/SM bugs incl. $20K Google VRP sandbox escape.

#### Tier B: Reproduction-from-CVE benchmarks (discovery-adjacent)

| Benchmark | Scale | Task | Oracle | Integration |
|---|---:|---|---|---|
| **CyberGym L1–L3** | 1,507 / 188 proj | PoC from description; L3 = patch-diffing → exploit | Execution (sanitizer) | Best scale; L3 is built-in patch-diffing eval |
| **SEC-bench (base)** | 200 / 29 proj | PoC gen + patch | Execution (sanitizer) | MIT, auto-built ~$0.87/instance; ≤18% PoC, ≤34% patch |
| **ReproBench** | 30 IoT firmware CVEs | Reproduce vuln **from CVE ID only** — full env reconstruction | Per-phase artifact verification | Tests from-scratch pipeline incl. acquiring targets; 45% of runs faked via simulation, only 5.3% real repro |
| **ZeroDayBench** | 22 injected vulns | Find + **patch** unseen zero-day | Patch correctness | **Ports real CVEs into similar code → novel unseen bugs**. Defense-oriented (patch, not exploit); ~12–14% success |

#### Tier C: Patch-diffing / root-cause analysis

- **CyberGym Level 3** — Built-in: provides ground-truth patch diff + post-patch codebase, agent produces exploit PoC. Cleanest patch-diff→exploit oracle.
- **Akamai PatchDiff-AI** — Multi-agent RCA on Patch Tuesday binary diffs. Metrics: correct vulnerable binary 88.6%, vulnerable function 83.9%, correct root cause 71.4%. **System + eval numbers, not released benchmark.**
- **Anthropic N-day exploits** — 18 Firefox + 21 Windows kernel patches → PoC/exploit. Demonstrates threat model but **study, not public dataset**.

#### Tier E: Bug-injection ground-truth corpora (beyond MAGMA/LAVA-M)

- **AIxCC Challenge Set** — 59+ hand-designed synthetic CPVs injected into real OSS (gold standard "injected bug with ground truth"). Via [archive.aicyberchallenge.com](https://archive.aicyberchallenge.com/challenges/) + CRSBench.
- **ZeroDayBench** — Ports real CVEs into analogous code → novel unseen injected bugs.
- **WitnessGym** — 1,300 injected bugs (CodeQL-derived types) into real Java projects on test-reached paths; agent must construct executable witness.
- **SolidiFI-benchmark** — Injected Solidity smart-contract bugs (reentrancy etc.).

### Key gap: "Discovery" is a spectrum

Almost no benchmark gives agent a bare codebase and says "find a zero-day" with **zero prior** — CyberGym L0, FB-Bench, AnonVul, and CRSBench (full-scan mode) come closest. Most "vuln discovery" evals are really reproduction/one-day tasks where a description or report is provided (CyberGym L1, SEC-bench Pro, CVE-Bench).

**Oracle trade-off**: Pure-execution sanitizer oracles (CyberGym, FB-Bench, CRSBench PoV) are deterministic but limited to memory-safety/crashable classes; logic/web bugs need either LLM judges (SEC-bench Pro) or embedded oracles (AnonVul).

**Contamination** is the unresolved threat: real-CVE benchmarks risk the bug being in training data. AnonVul (anonymization) and ZeroDayBench (re-hosted CVEs) are the only two explicitly engineered against it.

### Coverage projection (vuln research)

**Current**: No vuln research benchmarks (all are exploitation/RE focused).

**With CyberGym L0 + FB-Bench + CRSBench**:
- Open-ended discovery: CyberGym L0 (1,507 tasks), FB-Bench (77 challenges)
- Full lifecycle: CyberGym-E2E (920 tasks, discover→PoC→patch)
- Ground-truth injected: CRSBench (124 tasks, 315 CPVs, 91 CWEs)
- **Total vuln research coverage**: ~2,500+ tasks

**Unique capabilities added**:
- Zero-day discovery (CyberGym L0 found 34 real zero-days in paper runs)
- Full vulnerability research lifecycle (CyberGym-E2E: discover → exploit → patch)
- Anti-contamination evaluation (AnonVul anonymization)
- Rigorous AIxCC ground truth (CRSBench: 315 CPVs across real projects)

---

See [pins and patch purposes](PINNED.md).
