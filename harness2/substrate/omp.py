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

"""OmpSubstrate: the OMP coding-agent runtime (`omp`) as a solver substrate, called directly.

Carries the c1..c8 surface (OMP_SURFACE), the one install mode (omp_root: AGENTS.md, scripts/
and .omp/ at the workspace root, where `omp --cwd <ws>` discovers them), the direct runtime
call, and the OMP event-stream trajectory renderer. No runner script stands between Harness²
and the agent: `run` spawns one `omp -p --mode json` process per rollout, and the benchmark
launcher only stages the workspace, builds the prompt and collects the deliverables.

Every rollout runs under the dedicated profile `config.OMP_PROFILE`, with the inherited profile
selectors removed and a settings overlay pinned on top, so the operator's own skills, rules,
memories, advisor and model fallbacks never reach a rollout and every agent role runs the
executor model. The session transcript lands beside the event stream, inside the run record.
"""

from __future__ import annotations
import asyncio
import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Mapping

from .. import config
from ..core import runmark as RM
from ..core import tree as HT
from ..core.tree import SurfaceSpec
from .base import Install, Launcher, RunRequest

OMP_SURFACE = SurfaceSpec(
    name="omp",
    always_on=("AGENTS.md",),
    always_on_max=8_000,
    always_on_cap_reason=(
        "AGENTS.md is injected whole into the system prompt of EVERY turn, beside the "
        "runtime's own tool and skill listings"
    ),
    skill_dir=".omp/skills",
    skill_name_rule="overrides_dir",
    trigger_hint=(
        'Fix it by adding a trigger line naming `{name}` to AGENTS.md, e.g. "When '
        '<the situation this skill handles>, read `skill://{name}` and follow it."'
    ),
    autotrigger_file="AGENTS.md",
    trigger_line="- When {desc}, read `skill://{name}` and follow it.\n",
    subagent_requires_mode=False,
    plugin_dir=".omp/extensions",
    hooks_file=None,
    compile_skill_scripts=True,
    reject_empty_always_on=True,
    stubs=(
        (
            "scripts/README.md",
            "<!-- c7: deterministic helpers, run as `python3 scripts/<name>.py`. "
            "Add one by emitting scripts/<name>.py. -->\n",
        ),
        (
            "sub_agents/README.md",
            "<!-- c5: delegated agents, each spawned by the `task` tool in its OWN context. Add "
            "one as sub_agents/<name>/AGENT.md with frontmatter `description:`; the runner "
            "installs it as the task agent `<name>`. -->\n",
        ),
        (
            ".omp/extensions/README.md",
            "<!-- c8: OMP extensions -- the only lever that acts INSIDE the tool loop, so the "
            "model cannot skip it. Add one as .omp/extensions/<name>.ts whose default export is "
            '`function (pi) { pi.on("tool_result", async (event) => { ... }) }`. -->\n',
        ),
        (
            ".omp/skills/README.md",
            "<!-- c6: reusable workflows. Add one as .omp/skills/<name>/SKILL.md with YAML "
            "frontmatter: `description:` is REQUIRED (no description = skill silently skipped); "
            "`name:` is optional and must match the directory. Only name+description are listed "
            "to the agent; it reads the body on demand as skill://<name>. -->\n",
        ),
    ),
)

OMP_INSTALL_MODE = "omp_root"

# Inherited variables that would select another profile, agent directory, settings overlay or
# role model, and so carry the operator's own OMP setup into a rollout.
_DROPPED_ENV = (
    "OMP_PROFILE",
    "PI_PROFILE",
    "PI_CODING_AGENT_DIR",
    "PI_CODING_AGENT_SESSION_DIR",
    "PI_CONFIG_FILES",
    "PI_SMOL_MODEL",
    "PI_SLOW_MODEL",
    "PI_PLAN_MODEL",
    "PI_BLOCKED_AGENT",
)
_BUILTIN_CHAT_ROLES = (
    "default",
    "smol",
    "slow",
    "plan",
    "task",
    "advisor",
    "tiny",
    "commit",
    "vision",
)
_SPECIALIST_ROLES = (
    "rust",
    "python",
    "architect",
    "implementer",
    "debugger",
    "qa",
    "scout",
    "research",
    "mechanic",
    "devops",
    "designer",
    "codebase-memory",
)
_BUNDLED_AGENTS = (
    "task",
    "sonic",
    "scout",
    "reviewer",
    "security-reviewer",
    "seance",
)
_MODEL_KIND_ROLES = frozenset({"web", "image", "speech", "dictation"})
_CHAT_ROLES = _BUILTIN_CHAT_ROLES
_THINKING_LEVELS = frozenset({"off", "minimal", "low", "medium", "high", "xhigh", "max", "auto"})
_KILL_GRACE = 120
_TIME_LIMIT_EVENT = "harness2_time_limit"
_SUBAGENT = re.compile(r"sub_agents/([a-z0-9][a-z0-9_\-]*)/AGENT\.md")
_FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


def _parse_yaml_subkeys(text: str, section: str) -> list[str]:
    in_sec = False
    keys = []
    sec_indent = None
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^(\s*)" + re.escape(section) + r":", line)
        if m:
            in_sec = True
            sec_indent = len(m.group(1))
            continue
        if in_sec:
            indent = len(line) - len(line.lstrip())
            if indent <= sec_indent:
                break
            key_m = re.match(r"^\s*([a-zA-Z0-9_\-]+)\s*:", line)
            if key_m:
                keys.append(key_m.group(1))
    return keys


def _discover_profile_roles_and_agents(profile: str | None) -> tuple[set[str], set[str]]:
    """Inspect the named profile (and default profile) to discover custom modelRoles and overrides."""
    roles: set[str] = set()
    agents: set[str] = set()
    prof = profile or config.OMP_PROFILE
    paths_to_check: list[Path] = []
    if prof and prof != "default":
        prof_agent = Path.home() / ".omp" / "profiles" / prof / "agent"
        paths_to_check.append(prof_agent / "config.yml")
        paths_to_check.append(prof_agent / "config.yaml")
        agent_dir = prof_agent / "agents"
        if agent_dir.is_dir():
            agents.update(p.stem for p in agent_dir.glob("*.md"))
    default_agent = Path.home() / ".omp" / "agent"
    paths_to_check.append(default_agent / "config.yml")
    paths_to_check.append(default_agent / "config.yaml")
    def_agent_dir = default_agent / "agents"
    if def_agent_dir.is_dir():
        agents.update(p.stem for p in def_agent_dir.glob("*.md"))

    for cfg_path in paths_to_check:
        try:
            if cfg_path.is_file():
                txt = cfg_path.read_text(encoding="utf-8", errors="replace")
                roles.update(_parse_yaml_subkeys(txt, "modelRoles"))
                agents.update(_parse_yaml_subkeys(txt, "agentModelOverrides"))
        except OSError:
            continue
    return roles, agents


def overlay(model: str, agents: Iterable[str] = (), profile: str | None = None) -> dict:
    """The `--config` settings overlay for one rollout; it outranks profile and project settings.

    Off: what adds model calls outside the harness (advisor, recap, autolearn, memory, cache
    warming) or carries operator state in (user-level `~/.agents` skills). Pinned: every chat
    role, specialist role, profile role, bundled agent, and harness agent to the executor model,
    with model fallback off, so a rollout never changes model; blocking subagents, so delegated
    work finishes inside the print-mode run; yolo approvals, since nobody is there to answer a prompt.
    """
    prof_roles, prof_agents = _discover_profile_roles_and_agents(profile)
    all_roles = set(_BUILTIN_CHAT_ROLES) | set(_SPECIALIST_ROLES) | prof_roles
    pinned_roles = {r: model for r in sorted(all_roles) if r not in _MODEL_KIND_ROLES}

    all_agents = set(_BUNDLED_AGENTS) | set(agents) | prof_agents
    pinned_agents = {a: model for a in sorted(all_agents)}

    return {
        "advisor": {"enabled": False},
        "autolearn": {"enabled": False},
        "memory": {"backend": "off"},
        "recap": {"enabled": False},
        "autoResume": False,
        "skills": {"enableAgentsUser": False},
        "providers": {"cacheWarming": "off"},
        "retry": {"modelFallback": False},
        "modelRoles": pinned_roles,
        "task": {"agentModelOverrides": pinned_agents},
        "async": {"enabled": False},
        "tools": {"approvalMode": "yolo"},
    }

def agent_file(name: str, body: str) -> str:
    """`sub_agents/<name>/AGENT.md` as OMP's flat task-agent file `.omp/agents/<name>.md`.

    OMP registers a task agent under its frontmatter `name:` and skips one without it, so the
    directory name is written there, replacing any `name:` the proposal carried.
    """
    m = _FRONTMATTER.match(body)
    if m:
        fields = [ln for ln in m.group(1).splitlines() if not re.match(r"name\s*:", ln)]
        rest = body[m.end() :]
    else:
        desc = re.search(r"^description:\s*(.+)$", body[:600], re.M)
        fields = [f"description: {json.dumps(desc.group(1).strip())}"] if desc else []
        rest = body
    return "\n".join(["---", f"name: {name}", *fields, "---", ""]) + rest


def sidecars(stream: Path) -> tuple[Path, Path, Path]:
    """(stderr log, settings overlay, session directory) of the rollout whose events are
    `stream`; they sit beside it, so whatever clears a run record clears them too."""
    stream = Path(stream)
    return (
        stream.with_suffix(".stderr.log"),
        stream.with_suffix(".config.yml"),
        stream.with_suffix(".session"),
    )


@dataclass(frozen=True)
class OmpRun:
    """How one `omp` process ended. `timed_out` is True when the run reached its time limit,
    whether OMP stopped the turn itself or the process was killed; `exit_code` is None only
    when it was killed."""

    exit_code: int | None
    timed_out: bool
    wall_s: float
    stream: Path
    stderr: Path

    def stderr_tail(self, n: int = 600) -> str:
        try:
            return self.stderr.read_text(encoding="utf-8", errors="replace").strip()[-n:]
        except OSError:
            return ""


@cache
def _version(binary: str) -> str:
    """The first line of `omp --version` (e.g. 'omp/18.12.3'); never starts a session."""
    try:
        r = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"`{binary} --version` failed: {exc}") from exc
    line = next((ln.strip() for ln in r.stdout.splitlines() if ln.strip()), "")
    if r.returncode != 0 or not line:
        raise RuntimeError(
            f"`{binary} --version` exited {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}"
        )
    return line


def _kill_group(proc: subprocess.Popen, grace_s: float = 5.0) -> None:
    """SIGTERM the rollout's process group so OMP can close its stream, then SIGKILL the rest."""
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGTERM)
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=grace_s)
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGKILL)
    if proc.poll() is None:
        proc.kill()
    proc.wait()


async def _kill_group_async(proc: asyncio.subprocess.Process, grace_s: float = 5.0) -> None:
    """Async SIGTERM process group, wait for OMP to exit, then SIGKILL remaining children."""
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGTERM)
    with contextlib.suppress(asyncio.TimeoutError, Exception):
        await asyncio.wait_for(proc.wait(), timeout=grace_s)
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGKILL)
    if proc.returncode is None:
        with contextlib.suppress(Exception):
            proc.kill()
    with contextlib.suppress(Exception):
        await proc.wait()


class OmpSubstrate:
    """The OMP runtime behind the one Substrate interface, invoked by `run` with no runner."""

    name = "omp"

    def __init__(self, launcher: Launcher | None = None):
        self._launcher = launcher

    def surface(self) -> SurfaceSpec:
        return OMP_SURFACE

    def materialise(self, tree_dir: Path, spec, ctx: Mapping[str, str]) -> Install:
        """Stage the surface files in the layout OMP discovers from the workspace root.

        Everything stays at its own path except sub_agents/<name>/AGENT.md, which becomes the
        task agent `.omp/agents/<name>.md`. README stubs and off-surface files are not staged.
        """
        if spec.install_mode != OMP_INSTALL_MODE:
            raise ValueError(
                f"install_mode {spec.install_mode!r} is not the omp mode; this substrate has "
                f"exactly one: {OMP_INSTALL_MODE!r}"
            )
        tree_dir = Path(tree_dir)
        if not HT.is_tree(OMP_SURFACE, tree_dir):
            raise ValueError(f"{tree_dir} is not an omp harness tree (no AGENTS.md)")
        staged = Path(tempfile.mkdtemp(prefix="adapt-omp-root-"))
        try:
            files = {}
            for rel, body in HT.read_tree(OMP_SURFACE, tree_dir).items():
                m = _SUBAGENT.fullmatch(rel)
                if m:
                    files[f".omp/agents/{m.group(1)}.md"] = agent_file(m.group(1), body)
                else:
                    files[rel] = body
            for key, body in ctx.items():
                if key.startswith("file:"):
                    files[HT.normalize_rel(key[len("file:") :])] = body
            for rel, body in files.items():
                p = staged / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(body, encoding="utf-8")
        except BaseException:
            shutil.rmtree(staged, ignore_errors=True)
            raise
        return Install(
            staging_dir=staged,
            fingerprint=RM.fingerprint(tree_dir),
            extras={
                "install_mode": OMP_INSTALL_MODE,
                **{k: v for k, v in ctx.items() if not k.startswith("file:")},
            },
        )

    def install(self, install: Install, workspace: Path) -> list[str]:
        """Copy a staged harness onto the workspace root; return the installed relative paths."""
        src, workspace = Path(install.staging_dir), Path(workspace)
        installed = []
        for f in sorted(src.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            rel = f.relative_to(src)
            dest = workspace / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
            installed.append(rel.as_posix())
        return installed

    def binary(self) -> str:
        found = shutil.which(config.OMP_BIN)
        if not found:
            raise RuntimeError(
                f"OMP runtime not found: {config.OMP_BIN!r} is not an executable on PATH; "
                f"install omp or set HARNESS2_OMP_BIN to its path"
            )
        return found

    def runtime(self) -> str:
        """The runtime identity a run records: version and profile, e.g. 'omp/18.12.3 @harness2'."""
        return f"{_version(self.binary())} @{config.OMP_PROFILE}"

    def env(self, base: Mapping[str, str], profile: str | None = None) -> dict[str, str]:
        """The rollout environment: `base` minus `_DROPPED_ENV`, with the rollout profile
        selected, so an `omp` the agent itself starts resolves the same profile."""
        env = {k: v for k, v in base.items() if k not in _DROPPED_ENV}
        env["OMP_PROFILE"] = profile or config.OMP_PROFILE
        return env

    def argv(
        self,
        workspace: Path,
        *,
        model: str,
        timeout: int,
        thinking: str,
        session_dir: Path,
        overlay_file: Path,
        profile: str | None = None,
        binary: str | None = None,
    ) -> list[str]:
        """One headless turn: the prompt arrives on stdin, events leave on stdout as NDJSON."""
        bin_path = binary or self.binary()
        prof = profile or config.OMP_PROFILE
        return [
            bin_path,
            "--profile",
            prof,
            "-p",
            "--mode",
            "json",
            "--cwd",
            str(workspace),
            "--model",
            model,
            "--thinking",
            thinking,
            "--max-time",
            str(int(timeout)),
            "--session-dir",
            str(session_dir),
            "--config",
            str(overlay_file),
            "--no-title",
            "--no-lsp",
            "--no-prewalk",
        ]

    def run(
        self,
        prompt: str,
        workspace: Path,
        *,
        model: str,
        timeout: int,
        stream: Path,
        thinking: str = "high",
        env: Mapping[str, str] | None = None,
        profile: str | None = None,
        binary: str | None = None,
    ) -> OmpRun:
        """Run one rollout: the OMP runtime itself, in `workspace`, under the rollout profile.

        The caller supplies everything task-specific -- prompt, workspace, executor model --
        explicitly. The prompt goes in on stdin, because a positional prompt starting with `@`
        would be read as a file attachment. `--max-time` lets OMP abort its own turn at
        `timeout`; the process group is killed `_KILL_GRACE` seconds later, and on every exit,
        so nothing the agent started outlives the rollout. A run that reached the limit gets a
        closing `harness2_time_limit` event in its stream, because OMP ends such a turn with
        the same `agent_end` and exit status as a finished one.
        """
        if not model.strip():
            raise ValueError("OmpSubstrate.run needs an explicit provider/model selector")
        workspace = Path(workspace).absolute()
        stream = Path(stream)
        stderr_path, overlay_path, session_dir = sidecars(stream)
        stream.parent.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(session_dir, ignore_errors=True)  # the stream is rewritten; so is the session
        agents = sorted(p.stem for p in (workspace / ".omp" / "agents").glob("*.md"))
        prof = profile or config.OMP_PROFILE
        overlay_path.write_text(
            json.dumps(overlay(model, agents, profile=prof), indent=2) + "\n", encoding="utf-8"
        )
        argv = self.argv(
            workspace,
            model=model,
            timeout=timeout,
            thinking=thinking,
            session_dir=session_dir,
            overlay_file=overlay_path,
            profile=prof,
            binary=binary,
        )
        child_env = self.env(os.environ if env is None else env, profile=prof)
        killed = False
        t0 = time.monotonic()
        with stream.open("wb") as out, stderr_path.open("wb") as err:
            proc = subprocess.Popen(
                argv,
                cwd=workspace,
                env=child_env,
                stdin=subprocess.PIPE,
                stdout=out,
                stderr=err,
                start_new_session=True,
            )
            try:
                proc.communicate(
                    prompt.encode("utf-8"),
                    timeout=(int(timeout) + _KILL_GRACE) if timeout is not None else None,
                )
            except subprocess.TimeoutExpired:
                killed = True
            finally:
                _kill_group(proc)
        wall = time.monotonic() - t0
        # A turn that OMP itself stops at --max-time ends like a finished one (agent_end, exit
        # 0), so only the clock tells them apart; the stream records which it was.
        timed_out = killed or wall >= int(timeout)
        if timed_out:
            with stream.open("a", encoding="utf-8") as fh:
                event = {"type": _TIME_LIMIT_EVENT, "limit_s": int(timeout), "killed": killed}
                fh.write(json.dumps(event) + "\n")
        return OmpRun(
            exit_code=None if killed else proc.returncode,
            timed_out=timed_out,
            wall_s=round(wall, 1),
            stream=stream,
            stderr=stderr_path,
        )

    async def run_async(
        self,
        prompt: str,
        workspace: Path,
        *,
        model: str,
        timeout: int,
        stream: Path,
        thinking: str = "high",
        env: Mapping[str, str] | None = None,
        profile: str | None = None,
        binary: str | None = None,
    ) -> OmpRun:
        """Asynchronously run one rollout with clean process-group termination and cancellation safety."""
        if not model.strip():
            raise ValueError("OmpSubstrate.run_async needs an explicit provider/model selector")
        workspace = Path(workspace).absolute()
        stream = Path(stream)
        stderr_path, overlay_path, session_dir = sidecars(stream)
        stream.parent.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(session_dir, ignore_errors=True)
        agents = sorted(p.stem for p in (workspace / ".omp" / "agents").glob("*.md"))
        prof = profile or config.OMP_PROFILE
        overlay_path.write_text(
            json.dumps(overlay(model, agents, profile=prof), indent=2) + "\n", encoding="utf-8"
        )
        argv = self.argv(
            workspace,
            model=model,
            timeout=timeout,
            thinking=thinking,
            session_dir=session_dir,
            overlay_file=overlay_path,
            profile=prof,
            binary=binary,
        )
        child_env = self.env(os.environ if env is None else env, profile=prof)
        killed = False
        t0 = time.monotonic()
        with stream.open("wb") as out, stderr_path.open("wb") as err:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                cwd=str(workspace),
                env=child_env,
                stdin=asyncio.subprocess.PIPE,
                stdout=out,
                stderr=err,
                start_new_session=True,
            )
            try:
                effective_timeout = (int(timeout) + _KILL_GRACE) if timeout is not None else None
                if effective_timeout is not None:
                    await asyncio.wait_for(
                        proc.communicate(input=prompt.encode("utf-8")),
                        timeout=effective_timeout,
                    )
                else:
                    await proc.communicate(input=prompt.encode("utf-8"))
            except (asyncio.TimeoutError, asyncio.CancelledError):
                killed = True
            finally:
                await _kill_group_async(proc)
        wall = time.monotonic() - t0
        timed_out = killed or wall >= int(timeout)
        if timed_out:
            with stream.open("a", encoding="utf-8") as fh:
                event = {"type": _TIME_LIMIT_EVENT, "limit_s": int(timeout), "killed": killed}
                fh.write(json.dumps(event) + "\n")
        return OmpRun(
            exit_code=None if killed else proc.returncode,
            timed_out=timed_out,
            wall_s=round(wall, 1),
            stream=stream,
            stderr=stderr_path,
        )

    def execute(
        self, task_ref: str, install: Install, run_ids: list[str], timeout: int
    ) -> list[Path]:
        if self._launcher is None:
            raise RuntimeError(
                "OmpSubstrate was constructed without a launcher body; the benchmark adapter "
                "must supply one (it owns the workspace layout, the prompt, the executor model "
                "and read-back locations, and calls `run` for the rollout itself)"
            )
        return self._launcher(
            RunRequest(task_ref=task_ref, run_ids=tuple(run_ids), timeout=int(timeout)), install
        )

    def read_trajectory(
        self, stream_path: Path, *, obs_trunc: int, max_chars: int, args_trunc: int = 2000
    ) -> str:
        return render_events(
            Path(stream_path), obs_trunc=obs_trunc, max_chars=max_chars, args_trunc=args_trunc
        )

    def preflight(self) -> None:
        """Check the runtime, and that the executor model resolves under the rollout profile.

        `omp models --json` reads the profile's model registry, credentials included, without
        calling a model, so a missing login or API key fails here and not on the first rollout.
        """
        binary = self.binary()
        model = config.SOLVER_MODEL_OMP
        if not model:
            raise config.ConfigError(
                "Set HARNESS2_OMP_MODEL (or HARNESS2_SOLVER_MODEL) to an OMP provider/model "
                "selector for omp executor rollouts"
            )
        head, _, level = model.rpartition(":")
        selector = head if head and level in _THINKING_LEVELS else model
        profile = config.OMP_PROFILE
        try:
            r = subprocess.run(
                [binary, "--profile", profile, "models", selector, "--json"],
                env=self.env(os.environ),
                capture_output=True,
                text=True,
                timeout=120,
                stdin=subprocess.DEVNULL,
            )
            found = {m.get("selector") for m in json.loads(r.stdout).get("models", [])}
        except (OSError, subprocess.TimeoutExpired, ValueError, AttributeError) as exc:
            raise RuntimeError(f"`omp --profile {profile} models` failed: {exc}") from exc
        if selector not in found:
            raise RuntimeError(
                f"{selector} is not available to OMP profile {profile!r}: log in with "
                f"`omp --profile {profile} login`, export the provider's API key, or define the "
                f"provider in models.yml under `omp --profile {profile} config path`"
            )


_TRUNC_FMT = "…(+{n} chars — render truncation)"


def _clip(s, n: int) -> str:
    s = "" if s is None else str(s)
    s = s.replace("\x00", "")
    if n <= 0 or len(s) <= n:
        return s
    return s[:n] + _TRUNC_FMT.format(n=len(s) - n)


def _events(path: Path) -> Iterator[dict]:
    """The JSON objects of an `omp --mode json` stream, in order; junk lines are skipped."""
    with Path(path).open(encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln.startswith("{"):
                continue
            try:
                ev = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if isinstance(ev, dict):
                yield ev


def _text(content) -> str:
    """The text blocks of a message's content, joined; an image becomes a placeholder."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content if isinstance(content, list) else ():
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif block.get("type") == "image":
            parts.append("(image)")
    return "\n".join(p for p in parts if p.strip())


def _assistant(ev: dict) -> dict | None:
    """The assistant message a `message_end` event completes, else None."""
    msg = ev.get("message") if ev.get("type") == "message_end" else None
    return msg if isinstance(msg, dict) and msg.get("role") == "assistant" else None


_USAGE_KEYS = ("input", "cacheRead", "cacheWrite", "output", "reasoningTokens")


def _add_usage(acc: dict, usage) -> None:
    if not isinstance(usage, dict):
        return
    for k in _USAGE_KEYS:
        v = usage.get(k)
        if isinstance(v, (int, float)):
            acc[k] = acc.get(k, 0) + int(v)
    cost = usage.get("cost")
    total = cost.get("total") if isinstance(cost, dict) else None
    if isinstance(total, (int, float)):
        acc["cost"] = acc.get("cost", 0.0) + float(total)


def _render_message(
    msg: dict, lines: list[str], pending: dict[str, str], obs_trunc: int, args_trunc: int
) -> None:
    role = msg.get("role")
    content = msg.get("content")
    if role == "assistant":
        for block in content if isinstance(content, list) else ():
            if not isinstance(block, dict):
                continue
            kind = block.get("type")
            if kind == "text" and str(block.get("text") or "").strip():
                lines.append(f"[ASSISTANT] {_clip(block['text'], obs_trunc)}")
            elif kind == "thinking" and str(block.get("thinking") or "").strip():
                lines.append(f"[THINKING] {_clip(block['thinking'], obs_trunc)}")
            elif kind == "toolCall":
                name = block.get("name") or "tool"
                args = json.dumps(block.get("arguments"), default=str, ensure_ascii=False)
                lines.append(f"[ACTION] {name}({_clip(args, args_trunc)})")
                if block.get("id") is not None:
                    pending[str(block["id"])] = name
        stop = msg.get("stopReason")
        if stop in ("error", "aborted"):
            lines.append(
                f"[ERROR] {stop}: {_clip(msg.get('errorMessage') or '(no message)', 1000)}"
            )
        elif stop == "length":
            lines.append("[HARNESS] the model hit its output-token limit mid-message")
    elif role == "toolResult":
        name = pending.pop(str(msg.get("toolCallId")), None) or msg.get("toolName") or "tool"
        tag = "OBSERVATION ERROR" if msg.get("isError") else "OBSERVATION"
        lines.append(f"[{tag}] {name}: {_clip(_text(content), obs_trunc)}")
    else:
        txt = _text(content)
        if txt.strip():
            tag = "USER" if role == "user" else f"HARNESS {role or 'message'}"
            lines.append(f"[{tag}] {_clip(txt, obs_trunc)}")


def render_events(path: Path, *, obs_trunc: int, max_chars: int, args_trunc: int = 2000) -> str:
    """Render an `omp --mode json` event stream into the shared grammar.

    Completed messages (`message_end`) carry, in order, everything the grammar needs: the
    prompt, each assistant message's thinking, text and tool calls, and each tool result.
    Streaming deltas and the `turn_end`/`agent_end` repeats are skipped. A tool call whose
    result never arrived, a run that reached its time limit, and a stream without `agent_end`
    are all stated, because each means the work was cut short. `args_trunc` is this
    substrate's default, as for codex.
    """
    lines: list[str] = []
    pending: dict[str, str] = {}
    usage: dict = {}
    ended = False
    limit = ""
    try:
        for ev in _events(path):
            et = ev.get("type")
            msg = ev.get("message")
            if et == "message_end" and isinstance(msg, dict):
                _render_message(msg, lines, pending, obs_trunc, args_trunc)
                if msg.get("role") == "assistant":
                    _add_usage(usage, msg.get("usage"))
            elif et == "auto_retry_start":
                lines.append(
                    f"[HARNESS] provider retry {ev.get('attempt')}/{ev.get('maxAttempts')}: "
                    f"{_clip(ev.get('errorMessage'), 500)}"
                )
            elif et == "auto_compaction_end" and not ev.get("skipped"):
                failed = ev.get("errorMessage") or ("aborted" if ev.get("aborted") else "")
                lines.append(
                    f"[HARNESS] context compaction failed: {_clip(failed, 300)}"
                    if failed
                    else "[HARNESS] context compacted"
                )
            elif et == "notice" and ev.get("level") in ("warning", "error"):
                lines.append(f"[HARNESS] {ev['level']}: {_clip(ev.get('message'), 500)}")
            elif et == "agent_end":
                ended = True
            elif et == _TIME_LIMIT_EVENT:
                how = "KILLED" if ev.get("killed") else "stopped by OMP"
                limit = f"run {how} at its {ev.get('limit_s')}s time limit"
    except OSError as e:
        return f"(failed to read trajectory: {e})"
    for name in pending.values():
        lines.append(f"[OBSERVATION ERROR] {name}: (no result -- the run ended before it returned)")
    if lines or limit:
        head = limit or (
            "run ended" if ended else "stream ended WITHOUT agent_end (process killed or crashed)"
        )
        lines.append(
            f"[HARNESS] {head} | tokens in={usage.get('input', 0)} "
            f"cache_read={usage.get('cacheRead', 0)} out={usage.get('output', 0)} "
            f"reasoning={usage.get('reasoningTokens', 0)} cost=${usage.get('cost', 0.0):.4f}"
        )
    rendered = "\n".join(lines).strip()
    if not rendered:
        return "(no parseable events in trajectory)"
    if len(rendered) > max_chars:
        dropped = len(rendered) - max_chars
        rendered = rendered[:max_chars] + "\n" + _TRUNC_FMT.format(n=dropped)
    return rendered


def summarize(path: Path) -> dict:
    """Counts for a run record: events, assistant turns, tool calls, provider errors, token
    usage (input counts every prompt token, cached ones included), cost, the last assistant
    text, how the last assistant message stopped, and whether the agent loop ended."""
    usage: dict = {}
    out = {
        "n_events": 0,
        "turns": 0,
        "tool_calls": 0,
        "errors": 0,
        "final_text": "",
        "stop_reason": "",
        "ended": False,
    }
    try:
        for ev in _events(path):
            if ev.get("type") == _TIME_LIMIT_EVENT:
                continue
            out["n_events"] += 1
            out["ended"] = out["ended"] or ev.get("type") == "agent_end"
            msg = _assistant(ev)
            if msg is None:
                continue
            out["turns"] += 1
            content = msg.get("content") if isinstance(msg.get("content"), list) else []
            out["tool_calls"] += sum(
                1 for b in content if isinstance(b, dict) and b.get("type") == "toolCall"
            )
            out["stop_reason"] = str(msg.get("stopReason") or "")
            out["errors"] += out["stop_reason"] == "error"
            out["final_text"] = _text(content) or out["final_text"]
            _add_usage(usage, msg.get("usage"))
    except OSError:
        pass
    out["input_tokens"] = sum(usage.get(k, 0) for k in ("input", "cacheRead", "cacheWrite"))
    out["cached_input_tokens"] = usage.get("cacheRead", 0)
    out["output_tokens"] = usage.get("output", 0)
    out["reasoning_tokens"] = usage.get("reasoningTokens", 0)
    out["cost_usd"] = round(usage.get("cost", 0.0), 6)
    return out


__all__ = [
    "OMP_SURFACE",
    "OMP_INSTALL_MODE",
    "OmpRun",
    "OmpSubstrate",
    "agent_file",
    "overlay",
    "render_events",
    "sidecars",
    "summarize",
]
