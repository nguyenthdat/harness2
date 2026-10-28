# OMP profile guide

English | [Tiếng Việt](OMP.vi.md)

This guide runs Harness² with the [OMP executor](SETUP.md#omp-executor) on
[JobBench](BENCHMARKS.md#jobbench) (OMP also supports [WorkBuddy-Bench](BENCHMARKS.md#workbuddy-bench) and LAB),
with DeepSeek models in every role, and then moves what it learns into your own OMP profile. Commands run from the repository
root. Recursion budgets and resume rules are in the
[experiment guide](EXPERIMENTS.md).

## How Harness² uses OMP

For each task, Harness² runs reference rollouts under the current harness, asks
the improver for candidate edits, probes each candidate with its own rollout,
composes a refined harness from the evidence, and selects a final harness
without seeing the grading rubric. Reflection then stores the adopted harness
and an evidence-backed lesson in a per-domain library that later tasks in the
same domain read.

Candidates come in two dimensions:

| Dimension | Covers |
|---|---|
| INV (invariant) | How the agent works: procedure, tool use, verification, completion |
| DOM (domain) | What a practitioner in the task's field knows |

A task costs `4k` executor rollouts and `3k` improver sessions, so `--k 1`
means 4 rollouts and 3 improver sessions.

Each rollout is one `omp --profile harness2 -p --mode json` process in a fresh
task workspace. A per-run settings overlay turns off the advisor, memory, recap,
and autolearn, pins every model role and subagent to the executor model, and
approves every tool call. Harness² never reads or writes your own profile;
moving results into it is the manual step in
[Move results into your profile](#7-move-results-into-your-profile).

The harness is the set of files Harness² may edit. They sit at the workspace
root, where OMP discovers them:

| Path | Role | When it is in context |
|---|---|---|
| `AGENTS.md` | Role, procedure, standing rules | Every turn; capped at 8,000 characters |
| `.omp/skills/<name>/SKILL.md` | Reusable workflow; `description:` frontmatter required | Name and description up front, body on demand as `skill://<name>`; opened only when `AGENTS.md` names it in a trigger line |
| `sub_agents/<name>/AGENT.md` | Delegated agent | Installed as the task agent `.omp/agents/<name>.md`; runs in its own context |
| `scripts/<name>.py` | Deterministic helper | When the agent runs `python3 scripts/<name>.py` |
| `.omp/extensions/<name>.ts` | Handler inside the tool loop (`tool_call`, `tool_result`, `session_stop`) | Always loaded |

JobBench starts every task from a two-line `AGENTS.md`
(`third_party/jb_runner/codex_base_harness/AGENTS.md`).

## Requirements

- macOS or Linux with `git`, `npm`, Node.js 20 or newer, and
  [uv](https://docs.astral.sh/uv/getting-started/installation/). LAB also needs
  Pandoc and Poppler (`brew install pandoc poppler` on macOS); JobBench does not. WorkBuddy needs Docker.
- `omp` on `PATH`, or `HARNESS2_OMP_BIN` set to its path. Setup does not install
  or pin OMP.
- A DeepSeek API key.
- About 3.5 GB of disk for the JobBench dependencies under `dependencies/`.

Steps 1 to 4 were verified on macOS (arm64) with omp 18.12.5.

## 1. Install Harness²

```bash
uv venv --python 3.12 .venv    # --clear replaces an existing .venv
source .venv/bin/activate
uv pip install -e '.[render]'
harness2-demo --output runs/demo --k 2
```

The demo needs no credentials and ends with `2 tasks completed; 0 failed`.

## 2. Install JobBench for OMP

```bash
harness2-setup jb --substrate omp --dry-run    # review the plan
harness2-setup jb --substrate omp
```

Setup clones the pinned OpenCode checkout that the improver runs on, installs
Bun 1.3.11 under `dependencies/tools`, clones and patches `job-bench-eval` with
its own Python 3.12 environment, downloads the dataset (65 tasks across 35
occupations), and prints the `harness2` profile directory.

## 3. Configure DeepSeek

OMP and the pinned OpenCode both include a `deepseek` provider that reads
`DEEPSEEK_API_KEY`, so the profile needs no `models.yml`. List the model IDs
your key can use:

```bash
curl -s https://api.deepseek.com/models -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

Create `.env` in the repository root with model IDs from that list, and make it
private with `chmod 600 .env`:

```bash
DEEPSEEK_API_KEY=sk-...
HARNESS2_OMP_MODEL=deepseek/deepseek-v4-pro
HARNESS2_OMP_PROFILE=harness2
HARNESS2_SOLVER_MODEL=deepseek/deepseek-v4-pro
HARNESS2_IMPROVER_MODEL=deepseek/deepseek-v4-pro
HARNESS2_JUDGE_MODEL=deepseek-v4-pro
HARNESS2_JUDGE_BASE_URL=https://api.deepseek.com
HARNESS2_JUDGE_API_KEY=sk-...
```

| Setting | Used by |
|---|---|
| `HARNESS2_OMP_MODEL` | Executor rollouts |
| `HARNESS2_OMP_PROFILE` | The profile rollouts run under; `harness2` is the default |
| `HARNESS2_SOLVER_MODEL` | Required by every command, in OpenCode's `provider/model` form; the default for the executor and improver models |
| `HARNESS2_IMPROVER_MODEL` | Improver sessions: proposals, compositions, selection, reflection |
| `HARNESS2_JUDGE_MODEL`, `HARNESS2_JUDGE_BASE_URL`, `HARNESS2_JUDGE_API_KEY` | `harness2-judge`, through JobBench's OpenAI-compatible judge client |
| `HARNESS2_IMPROVER_CHANNEL` | Improver channel: `opencode` (default), `claude_cli`, or `omp` |
| `HARNESS2_IMPROVER_OMP_PROFILE` | Profile used when `HARNESS2_IMPROVER_CHANNEL=omp`; defaults to `HARNESS2_OMP_PROFILE` or `default` |

- Harness² loads `.env` itself, and shell variables take precedence. It does not
  expand `$VAR`, so the judge key appears a second time; change both lines when
  you rotate the key.
- `deepseek-flash` can replace `deepseek-v4-pro` in any role. The models are
  recorded with the run, so choose them before the first run.
- By default, the improver runs via OpenCode with an isolated data directory and without
  `ANTHROPIC_*` variables, so OpenCode logins and Anthropic API keys never reach
  it. Setting `HARNESS2_IMPROVER_CHANNEL=omp` runs recursive adaptation improver sessions
  (proposals, compositions, selection) directly through `omp` using `HARNESS2_IMPROVER_OMP_PROFILE`.
  Any provider that OMP and OpenCode both read from an API-key variable can
  replace DeepSeek the same way, with an OpenAI-compatible endpoint for the
  judge; the Vertex AI route is in
  [Models and credentials](SETUP.md#models-and-credentials).

## 4. Check before spending

```bash
harness2-check --bench jb --substrate omp
```

A ready installation prints `Ready: jb/omp; 65 tasks`. The check confirms that
the executor model resolves under the `harness2` profile, without calling it.
To inspect the same things by hand, load `.env` first, because `omp` does not
read it:

```bash
set -a; . ./.env; set +a
omp --profile harness2 models deepseek/deepseek-v4-pro --json
curl -s https://api.deepseek.com/user/balance -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

`omp models` lists a provider as soon as its credentials are configured, without
testing them: stale `~/.aws` credentials, for example, make Bedrock models
appear. The balance call proves that the key works and costs nothing.

## 5. Run

Use one output root per experiment. Its run directory records the executor,
improver and judge models, the judge endpoint, the `omp` version and profile,
and the task selection (`--only-domains`, `--max-tasks`, `--seed`); a later
command with different values is refused. Keep the variable exported for the
judge and report commands.

```bash
export HARNESS2_RUNS_DIR=runs/jb-omp-deepseek

# Preview the task stream; no model calls
harness2 --bench jb --substrate omp --k 1 --mode parallel \
  --only-domains computer_and_information_research_scientists --max-tasks 1 --dry-run

# Refine; one rollout can take up to 60 minutes, so use tmux or a spare terminal
harness2 --bench jb --substrate omp --k 1 --mode parallel \
  --only-domains computer_and_information_research_scientists --max-tasks 1

# Grade the adopted harness, then the base harness, then report
harness2-judge  --bench jb --substrate omp --k 1 --mode parallel
harness2-judge  --bench jb --substrate omp --k 1 --mode parallel --bases
harness2-report --bench jb --substrate omp --k 1 --mode parallel
```

`SUBSTRATE=omp bash scripts/run_jobbench.sh --only-domains ... --max-tasks 1`
runs the check, refinement, judging and report in one go, without `--bases`.
Repeat a command to resume it.

`--max-tasks` caps tasks per domain and `--workers N` runs `N` domains at once.
Tasks within a domain always run in order, each reading the library entries of
the tasks before it, so running a whole domain lets later tasks build on earlier
lessons. These domains are closest to software work: their tasks combine CSV,
XLSX, SQLite and Markdown inputs through scripted analysis and deliver documents
and tables.

| Domain | Tasks |
|---|---|
| `computer_and_information_research_scientists` | 2 |
| `statisticians` | 3 |
| `web_administrators` | 1 |

`--dry-run` without `--only-domains` lists every domain.

## 6. Read the results

Paths below are under `$HARNESS2_RUNS_DIR/jb/`, for `--k 1 --mode parallel`
(namespace `jb-omp-agg1`; sequential runs use `seq` in place of `agg`).

| Path | Contents |
|---|---|
| `adapt/jb-omp-agg1/<domain>__<task>/summary.json` | `selections.agg.chosen_label` names the adopted harness; `chosen_tree_is_base: true` means no edit survived |
| `adapt/jb-omp-agg1/<domain>__<task>/harnesses/` | `base`, the candidates `inv1` and `dom1`, and the composition `agg1` |
| `adapt/jb-omp-agg1/judged.json`, `base_judged.json` | Scores of the adopted and base harnesses |
| `library/jb/k1-omp/agg/<domain>/INDEX.md` | The domain library's index |
| `library/jb/k1-omp/agg/<domain>/harnesses/<domain>__<task>/` | `harness/`, the adopted tree, and `EXPERIENCE.md`: why it was chosen, what each edit did, and the lesson with its cue, evidence and confidence |
| `dataset/<domain>/<task>/model_output/`, `model_traj/` | Each rollout's deliverables, and its event stream, stderr, settings overlay and OMP session |

To see what a task changed:

```bash
T=$HARNESS2_RUNS_DIR/jb/adapt/jb-omp-agg1/computer_and_information_research_scientists__task1
grep chosen_label "$T/summary.json"
diff -ru "$T/harnesses/base" "$T/harnesses/agg1"    # use the chosen label
```

## 7. Move results into your profile

A profile keeps its user-level components in `~/.omp/profiles/<profile>/agent/`,
for example `~/.omp/profiles/coder/agent/`. Move components by hand:

| Adopted harness | Profile location | Note |
|---|---|---|
| A rule in `AGENTS.md` | `AGENTS.md` | Merge the rule; never replace the file |
| `.omp/skills/<name>/` | `skills/<name>/` | Also carry the skill's trigger line into `AGENTS.md` |
| `sub_agents/<name>/AGENT.md` | `agents/<name>.md` | Frontmatter must include `name: <name>`; OMP skips an agent without it |
| `scripts/<name>.py` | `skills/<skill>/scripts/<name>.py` | A profile has no workspace `scripts/`; update the path in the rule or skill that runs it |
| `.omp/extensions/<name>.ts` | `extensions/<name>.ts` | Loaded in every session; read it before copying |

The repository's RE profile keeps three skills in `profiles/re/agent/skills/`:
[malware-analysis](../profiles/re/agent/skills/malware-analysis/SKILL.md),
[reverse-engineering](../profiles/re/agent/skills/reverse-engineering/SKILL.md),
and
[static-artifact-analysis](../profiles/re/agent/skills/static-artifact-analysis/SKILL.md).
It is a leaf analyst: it does not define subagents. Standing constraints are in
`profiles/re/agent/RULES.md`; on-demand rules are in `profiles/re/agent/rules/`.
Each directory matches its YAML `name`; load it with `skill://<name>`.

```bash
E=$HARNESS2_RUNS_DIR/jb/library/jb/k1-omp/agg/statisticians/harnesses/statisticians__task1
P=~/.omp/profiles/coder/agent
cat "$E/EXPERIENCE.md"
cp -R "$E/harness/.omp/skills/<name>" "$P/skills/"
```

What to move:

- INV edits (procedure, tool use, verification) that `EXPERIENCE.md` backs with
  evidence. Leave DOM edits behind: they encode one occupation's knowledge.
- Not an extension that refuses to finish until a file exists, such as a
  deliverable in `output/`: in an interactive profile it blocks every session
  that does not write that file.
- Lessons were learned with the executor model on a two-line `AGENTS.md`. A
  profile that runs another model or carries a long `AGENTS.md` may already
  cover a lesson or contradict it; check before merging, and use the profile for
  a few real sessions afterwards.
- To trial a harness without touching your profile, install it in a scratch copy
  of a project the way Harness² rolled it out: `AGENTS.md`, `scripts/` and
  `.omp/` at the root, with each `sub_agents/<name>/AGENT.md` moved to
  `.omp/agents/<name>.md`.

## 8. Native IDA and the official IDA MCP in the RE profile

`profiles/re/agent/config.yml` enables OMP's native `ida` tool and executable
`read` views. `profiles/re/agent/mcp.json` also connects the
[first-party Hex-Rays IDA MCP](https://docs.hex-rays.com/add-ons/mcp/overview)
from [HexRaysSA/ida-mcp](https://github.com/HexRaysSA/ida-mcp), not the community
`ida-pro-mcp` server. The existing REA/Ghidra server remains unchanged.

Native IDA keeps the requested `~/opswat/.idapro/.venv/bin/python`; MCP
launches the `ida-mcp` executable installed separately by `uv tool install`.
The tested stack is OMP 18.13.1, IDA Pro 9.4.260713, Python 3.13.16 arm64,
`ida-domain` 0.5.1, and official `ida-mcp` 20261023.0.2. The MCP requires IDA
9.4+ with idalib, Python 3.11+, Git, and uv. A working IDA license and any
required first-run license acceptance are prerequisites; these commands do
not install a license, accept terms, or start the GUI.

Keep the following **literal absolute paths** in the private, ignored
`profiles/re/agent/.env`, adjusting them for the machine:

```dotenv
OMP_IDA_PYTHON=/absolute/home/opswat/.idapro/.venv/bin/python
IDADIR="/path/to/IDA Professional 9.4.app/Contents/MacOS"
IDAPYTHON_VENV_EXECUTABLE=/absolute/home/opswat/.idapro/.venv/bin/python
```

On Linux, `IDADIR` is the directory containing `libidalib.so`; on macOS it is
the app's `Contents/MacOS`, containing `libidalib.dylib`. Do not use the old
`IDA_INSTALLDIR` name. Do not put `$HOME` or references to another variable
inside the profile dotenv file: OMP's parser leaves those references literal.
Keep IDA-specific variables in this profile, not a globally exported shell
startup file.

Keep the existing native venv; install the MCP CLI separately and ensure
`ida-mcp` is on OMP's `PATH`. These are the tested versions:

```bash
export OMP_IDA_PYTHON="$HOME/opswat/.idapro/.venv/bin/python"
uv pip install --python "$OMP_IDA_PYTHON" ida-domain==0.5.1 idapro==0.0.10
uv tool install ida-mcp==20261023.0.2
```

`idapyswitch` selects the **base interpreter's shared library**, not the venv
directory or `bin/python`. For the selected venv, with `IDADIR` exported in
the current setup shell:

```bash
LIBPYTHON=$("$OMP_IDA_PYTHON" -c 'import pathlib, sysconfig; print(pathlib.Path(sysconfig.get_config_var("LIBDIR")) / sysconfig.get_config_var("LDLIBRARY"))')
"$IDADIR/idapyswitch" --force-path "$LIBPYTHON"
export IDAPYTHON_VENV_EXECUTABLE="$OMP_IDA_PYTHON"
# Read the selection back without switching again:
"$OMP_IDA_PYTHON" -c 'import idapro, ida_registry; print(ida_registry.reg_read_string("Python3TargetDLL"))'
```

The library and venv must have the same Python major/minor and CPU
architecture. `IDAPYTHON_VENV_EXECUTABLE` activates the venv's packages for
IDAPython; `idapyswitch` alone does not. Finder/Dock launches do not inherit
these shell/profile variables; no machine-wide `launchctl` setting or GUI
plugin is installed by this setup.

OMP 18.13.1 does **not** interpolate `${VAR}` in native `ida.python` or
`ida.installDir`. The native interpreter setting therefore uses the supported
`~` path; update it as well if moving the venv. `installDir` is intentionally
unset so native IDA reads `IDADIR`. MCP `${VAR}` expansion only sees Bun's
process environment, which can miss profile dotenv values outside this repo.
The IDA MCP entry uses OMP's documented bare-variable `env` lookup and runs
`ida-mcp stdio --agent=omp-re --idle-timeout=900` directly, without a shell or
Python module shim. `IDAPYTHON_VENV_EXECUTABLE` still resolves the profile's
`OMP_IDA_PYTHON` value; no separate MCP `OMP_IDA_PYTHON` mapping is needed.

The MCP uses stdio, not an unauthenticated HTTP listener.
`IDA_NEXUS_IDALIB_ONLY=1` keeps workers headless. The CLI is launched from uv's
tool environment; with the retained `IDAPYTHON_VENV_EXECUTABLE`, the tested
worker reports the native venv as `sys.executable`/`sys.prefix`, while
`idapro` and `ida_nexus` are loaded from uv's tool environment.
`--idle-timeout=900` releases idle MCP database leases independently of native
`ida.idleCloseSec`. Native IDA and IDA Nexus have separate database managers:
close a database before opening that same IDB with the other integration.

For this checkout's home-relative config root:

```bash
PI_CONFIG_DIR=opswat/Projects/harness2 omp --profile re config path
PI_CONFIG_DIR=opswat/Projects/harness2 omp --profile re read /usr/bin/true
```

The first command must resolve to this checkout's `profiles/re/agent`, not the
default profile. In a new RE session, use native `ida` open/exec/close on a
harmless fixture, or `/mcp reload` then `/mcp test ida`; MCP `list_databases`
and `reference` are harmless read checks. For an analysis smoke, MCP
`open_database` with `gui: false`, inspect metadata/functions with
`execute_python`, then `close_database` for only the returned instance.
Do not execute the analyzed binary. The direct-executable MCP smoke ran outside
the repo with IDA variables unset in the launching shell: profile discovery,
initialize, all six tools, `list_databases`, and `reference` passed. A temporary
compiled fixture reported ARM/64-bit and `twice`/`main`; its database closed
successfully with `final_lease: true`. Native configuration was unchanged.

## Caveats

- Keep `HARNESS2_OMP_PROFILE` on a dedicated profile. The overlay does not stop
  a profile's MCP servers or extensions from loading, and rollouts approve every
  tool call with nobody watching; on a daily profile with desktop-control or
  note-taking MCP servers, a rollout can use them.
- JobBench publishes each task's `RUBRICS.json`, and a rollout can fetch it.
  Block the hosts listed under [Web access](EXPERIMENTS.md#web-access) at the
  network level during runs.
- With DeepSeek as both executor and judge, the judge grades its own model's
  work. DeepSeek accepts image inputs but replies that it cannot see them, so
  rubrics that need a chart are graded without it.
- `omp update` changes the recorded runtime. Finish a run before updating, and
  use a new `HARNESS2_RUNS_DIR` afterwards.
