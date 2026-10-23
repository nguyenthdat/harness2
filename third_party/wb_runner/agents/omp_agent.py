"""OmpAgent -- an OMP BaseInstalledAgent for WorkBuddy-Bench.

Runs the host OMP runtime directly against the container workspace by downloading
/workspace to a host tempdir, executing `omp -p --mode json`, uploading the modified
workspace back to the container, and mapping the event stream to ATIF.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

from harbor.agents.installed.base import BaseInstalledAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trajectories.agent import Agent
from harbor.models.trajectories.final_metrics import FinalMetrics
from harbor.models.trajectories.metrics import Metrics
from harbor.models.trajectories.step import Step
from harbor.models.trajectories.tool_call import ToolCall
from harbor.models.trajectories.trajectory import Trajectory

from workbuddy_bench.agents._agent_user import ensure_agent_user

_OUTPUT_FILENAME = "omp-output.jsonl"
_STDERR_FILENAME = "omp-stderr.log"


class OmpAgent(BaseInstalledAgent):
    """OMP CLI agent running on host against container workspace for harbor."""

    SUPPORTS_ATIF: bool = True

    def __init__(self, logs_dir: Path, *args, **kwargs):
        self._omp_version: str | None = kwargs.pop("OMP_VERSION", "1.0.0")
        self._omp_bin: str = (
            kwargs.pop("OMP_BIN", None)
            or os.environ.get("HARNESS2_OMP_BIN")
            or shutil.which("omp")
            or "omp"
        )
        self._omp_profile: str = (
            kwargs.pop("OMP_PROFILE", None)
            or os.environ.get("HARNESS2_OMP_PROFILE")
            or "harness2"
        )
        self._omp_model: str | None = (
            kwargs.pop("OMP_MODEL", None)
            or os.environ.get("HARNESS2_OMP_MODEL")
            or None
        )
        self._agent_timeout_sec: int | None = (
            kwargs.pop("OMP_TIMEOUT_SEC", None)
            or kwargs.pop("agent_timeout_sec", None)
        )
        super().__init__(logs_dir, *args, version=self._omp_version, **kwargs)

    @staticmethod
    def name() -> str:
        return "omp"

    def get_version_command(self) -> str | None:
        return None

    def parse_version(self, stdout: str) -> str:
        out = (stdout or "").strip()
        return out.split()[-1] if out else out

    async def install(self, environment: BaseEnvironment) -> None:
        await ensure_agent_user(self, environment)

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        instruction = self.render_instruction(instruction)
        local_ws = Path(tempfile.mkdtemp(prefix="wb-omp-ws-"))
        try:
            await environment.download_dir("/workspace", local_ws)
            await self._run_omp(instruction, local_ws)
            await environment.upload_dir(local_ws, "/workspace")
            run_user = getattr(environment, "default_user", None)
            if run_user not in (None, "", "root", 0, "0"):
                import shlex
                u = shlex.quote(str(run_user))
                await self.exec_as_root(
                    environment,
                    command=(
                        f"chown -R {u} /workspace && "
                        f"mkdir -p /logs/verifier && chmod -R a+rwx /logs/verifier && "
                        f"(chmod -R a+rX /tests 2>/dev/null || true)"
                    ),
                )
        finally:
            shutil.rmtree(local_ws, ignore_errors=True)
        self.populate_context_post_run(context)

    async def _run_omp(self, instruction: str, local_ws: Path) -> None:
        from harness2 import config
        from harness2.substrate.omp import OmpSubstrate

        output_file = self.logs_dir / _OUTPUT_FILENAME
        output_file.parent.mkdir(parents=True, exist_ok=True)

        substrate = OmpSubstrate()
        model = (
            self._omp_model
            or config.SOLVER_MODEL_OMP
            or os.environ.get("HARNESS2_OMP_MODEL")
            or os.environ.get("HARNESS2_SOLVER_MODEL")
        )
        if not model:
            raise RuntimeError("OmpAgent needs an explicit OMP model or HARNESS2_OMP_MODEL")

        timeout = int(self._agent_timeout_sec or 3600)

        run = await substrate.run_async(
            instruction,
            local_ws,
            model=model,
            timeout=timeout,
            stream=output_file,
            profile=self._omp_profile,
            binary=self._omp_bin,
        )

        legacy_stderr = self.logs_dir / _STDERR_FILENAME
        if run.stderr.is_file() and run.stderr != legacy_stderr:
            try:
                shutil.copy2(run.stderr, legacy_stderr)
            except OSError:
                pass

        if run.exit_code not in (0, None):
            tail = run.stderr_tail(1000)
            raise RuntimeError(
                f"OMP process exited with code {run.exit_code}: {tail}"
            )
    def populate_context_post_run(self, context: AgentContext) -> None:
        events = self._read_events()
        if not events:
            return
        traj = self._build_trajectory(events)
        if traj is not None:
            traj_path = self.logs_dir / "trajectory.json"
            traj_path.write_text(traj.model_dump_json(indent=2), encoding="utf-8")
            fm = traj.final_metrics
            if fm is not None:
                context.n_input_tokens = fm.total_prompt_tokens
                context.n_output_tokens = fm.total_completion_tokens
                if fm.total_cost_usd is not None:
                    context.cost_usd = fm.total_cost_usd

    def _read_events(self) -> list[dict] | None:
        out = self.logs_dir / _OUTPUT_FILENAME
        if not out.is_file():
            return None
        events: list[dict] = []
        with out.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    ev = json.loads(line)
                    if isinstance(ev, dict):
                        events.append(ev)
                except json.JSONDecodeError:
                    continue
        return events or None

    def _build_trajectory(self, events: list[dict]) -> Trajectory | None:
        steps: list[Step] = []
        session_id: str | None = None
        total_prompt = 0
        total_completion = 0
        total_cached = 0
        total_cost = 0.0
        step_id = 1
        errors: list = []

        for ev in events:
            etype = ev.get("type")
            session_id = session_id or ev.get("sessionId") or ev.get("session_id")
            if etype == "message_end":
                msg = ev.get("message")
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") != "assistant":
                    continue

                content = msg.get("content")
                text_parts: list[str] = []
                reasoning_parts: list[str] = []
                tool_calls: list[ToolCall] = []

                blocks = content if isinstance(content, list) else ()
                for b in blocks:
                    if not isinstance(b, dict):
                        continue
                    btype = b.get("type")
                    if btype == "text":
                        txt = b.get("text")
                        if isinstance(txt, str) and txt.strip():
                            text_parts.append(txt)
                    elif btype == "thinking":
                        th = b.get("thinking")
                        if isinstance(th, str) and th.strip():
                            reasoning_parts.append(th)
                    elif btype == "toolCall":
                        t_id = str(b.get("id") or f"call_{len(tool_calls) + 1}")
                        t_name = str(b.get("name") or "tool")
                        t_args = b.get("arguments") if isinstance(b.get("arguments"), dict) else {}
                        tool_calls.append(
                            ToolCall(
                                tool_call_id=t_id,
                                function_name=t_name,
                                arguments=t_args,
                            )
                        )

                usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
                t_in = int(usage.get("input") or 0)
                t_out = int(usage.get("output") or 0)
                t_cache = int(usage.get("cacheRead") or 0) + int(usage.get("cacheWrite") or 0)
                cost_val: float | None = None
                cost_dict = usage.get("cost")
                if isinstance(cost_dict, dict) and isinstance(cost_dict.get("total"), (int, float)):
                    cost_val = float(cost_dict["total"])

                total_prompt += t_in + t_cache
                total_completion += t_out
                total_cached += t_cache
                if cost_val is not None:
                    total_cost += cost_val

                stop = msg.get("stopReason")
                if stop == "error":
                    errors.append({"message": msg.get("errorMessage") or "assistant error"})

                steps.append(
                    Step(
                        step_id=step_id,
                        source="agent",
                        model_name=self._omp_model or "omp",
                        message="\n".join(text_parts),
                        reasoning_content="\n".join(reasoning_parts) or None,
                        tool_calls=tool_calls or None,
                        metrics=Metrics(
                            prompt_tokens=t_in,
                            completion_tokens=t_out,
                            cached_tokens=t_cache,
                            cost_usd=cost_val,
                        ),
                        llm_call_count=1,
                    )
                )
                step_id += 1
            elif etype in ("error", "notice") and ev.get("level") == "error":
                errors.append(ev)

        if not steps and not errors:
            return None
        if not steps:
            steps.append(
                Step(
                    step_id=1,
                    source="agent",
                    model_name=self._omp_model or "omp",
                    message="run produced no steps",
                    llm_call_count=0,
                )
            )

        final_metrics = FinalMetrics(
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_completion,
            total_cached_tokens=total_cached,
            total_cost_usd=round(total_cost, 6) if total_cost > 0 else None,
            total_steps=len(steps),
            extra={
                "model_route": self._omp_model or "omp",
                "profile": self._omp_profile,
                "errors": errors if errors else None,
            },
        )

        return Trajectory(
            session_id=session_id,
            agent=Agent(
                name="omp",
                version=self._version or "1.0.0",
                model_name=self._omp_model or "omp",
            ),
            steps=steps,
            final_metrics=final_metrics,
            notes="omp --mode json stream mapped to ATIF",
        )
