"""Centralized harness runtime adapter mapping, including the local OMP overlay."""

from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HarnessRuntimeAdapter:
    harness_name: str
    canonical_display_name: str
    harness_protocol: str
    backend_base_env: str
    backend_key_env: str
    proxy_url_env: str
    uses_anthropic_env: bool

    def emit_shell_vars(self) -> str:
        lines = [
            f"HARNESS_NAME={self.harness_name!r}",
            f"HARNESS_DISPLAY_NAME={self.canonical_display_name!r}",
            f"HARNESS_PROTOCOL={self.harness_protocol!r}",
            f"HARNESS_BACKEND_BASE_ENV={self.backend_base_env!r}",
            f"HARNESS_BACKEND_KEY_ENV={self.backend_key_env!r}",
            f"HARNESS_PROXY_URL_ENV={self.proxy_url_env!r}",
            f"HARNESS_USES_ANTHROPIC_ENV={'1' if self.uses_anthropic_env else ''}",
        ]
        return "\n".join(lines)


HARNESS_ADAPTERS: dict[str, HarnessRuntimeAdapter] = {
    "claude-code": HarnessRuntimeAdapter(
        harness_name="claude-code",
        canonical_display_name="Claude Code",
        harness_protocol="anthropic",
        backend_base_env="ANTHROPIC_BASE_URL",
        backend_key_env="ANTHROPIC_API_KEY",
        proxy_url_env="",
        uses_anthropic_env=True,
    ),
    "cbc-agent": HarnessRuntimeAdapter(
        harness_name="cbc-agent",
        canonical_display_name="CodeBuddy Code CLI",
        harness_protocol="openai",
        backend_base_env="CBC_BASE_URL",
        backend_key_env="CBC_API_KEY",
        proxy_url_env="CBC_PROXY_URL",
        uses_anthropic_env=False,
    ),
    "omp-harness": HarnessRuntimeAdapter(
        harness_name="omp-harness",
        canonical_display_name="OMP",
        harness_protocol="openai",
        backend_base_env="CBC_BASE_URL",
        backend_key_env="CBC_API_KEY",
        proxy_url_env="CBC_PROXY_URL",
        uses_anthropic_env=False,
    ),
}


def resolve_adapter(harness_name: str) -> HarnessRuntimeAdapter:
    adapter = HARNESS_ADAPTERS.get(harness_name)
    if adapter is None:
        valid = ", ".join(sorted(HARNESS_ADAPTERS))
        raise ValueError(
            f"Unknown harness name: {harness_name!r}. Valid harness names: [{valid}]. "
            "Register the harness in runner/harness_adapters.py::HARNESS_ADAPTERS."
        )
    return adapter


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: python3 -m workbuddy_bench.runner.harness_adapters <harness-name>",
            file=sys.stderr,
        )
        return 1
    try:
        print(resolve_adapter(sys.argv[1]).emit_shell_vars())
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
