---
name: preferred-package-managers
description: Prefer Bun for JavaScript and TypeScript workflows and uv for Python dependency and environment management.
---

# Preferred Package Managers

Apply these rules when installing dependencies, running project commands, or creating JavaScript, TypeScript, or Python projects.

## Respect The Repository Contract

- Treat the repository's committed lockfile, `packageManager` field, build scripts, CI configuration, and contributor documentation as authoritative.
- Do not introduce a second package manager or generate a competing lockfile in an established project.
- Do not migrate an established project solely to apply these preferences. When the repository does not mandate another tool, use Bun for JavaScript and TypeScript and uv for Python.

## Prefer Bun For JavaScript And TypeScript

- Use Bun as the default runtime, package manager, script runner, and package executor for new JavaScript and TypeScript work.
- Use `bun install` to install project dependencies and `bun install --frozen-lockfile` when reproducibility requires the lockfile to remain unchanged.
- Use `bun add <package>`, `bun add --dev <package>`, `bun remove <package>`, and `bun update` instead of the npm, Yarn, or pnpm equivalents.
- Use `bun run <script>` for `package.json` scripts, `bun <file>` for JavaScript or TypeScript entry points, and `bunx <package>` for one-off package executables.
- Commit `bun.lock` for Bun-managed projects. Do not create or retain `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml` unless the repository explicitly uses that package manager.
- Fall back to Node.js or another package manager only for a demonstrated compatibility requirement or an explicit repository contract; state the reason when doing so.

## Prefer uv For Python

- Use uv as the default Python project, dependency, virtual-environment, command, and tool manager.
- Use `uv init` for new projects, `uv add <package>` and `uv remove <package>` for dependency changes, `uv lock` for lockfile updates, and `uv sync` to materialize the environment.
- Use `uv run <command>` for project commands and `uvx <tool>` or `uv tool run <tool>` for one-off tools.
- Commit `uv.lock` for uv-managed applications and other projects that require reproducible environments.
- Prefer uv's project interface over direct `pip`, `pip-tools`, `pipx`, Poetry, Pipenv, or manual `venv` workflows. Use `uv pip` only when maintaining a pip-compatible legacy workflow that cannot use uv's project interface.
- Fall back to another Python package manager only when the repository explicitly requires it or uv cannot satisfy a verified compatibility constraint; state the reason when doing so.
