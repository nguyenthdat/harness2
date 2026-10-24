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

---
See [pins and patch purposes](PINNED.md).
