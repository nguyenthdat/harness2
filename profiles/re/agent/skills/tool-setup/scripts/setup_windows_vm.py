#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Windows VM Ansible Provisioning & Tool Catalog Manager.

CLI tool to inspect and manipulate the Windows reverse engineering tool catalog,
generate WinRM setup scripts, create Ansible inventory configurations,
and trigger Ansible playbook execution for Windows guest VMs.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ANSIBLE_DIR = SKILL_DIR / "ansible"
CATALOG_PATH = ANSIBLE_DIR / "windows_tools.json"
PLAYBOOK_PATH = ANSIBLE_DIR / "playbook_windows.yml"
WINRM_SCRIPT_PATH = ANSIBLE_DIR / "setup_winrm.ps1"
DEFENDER_SCRIPT_PATH = ANSIBLE_DIR / "toggle_defender.ps1"
DEFENDER_PLAYBOOK_PATH = ANSIBLE_DIR / "playbook_defender.yml"
DEFAULT_INVENTORY_PATH = ANSIBLE_DIR / "inventory.ini"

VALID_CATEGORIES: set[str] = {
    "telemetry_monitoring",
    "network_analysis",
    "forensics_triage",
    "debugging_disassembly",
    "pe_analysis",
    "system_utilities",
    "automation_agent",
}


@dataclass(slots=True)
class ToolEntry:
    id: str
    name: str
    category: str
    description: str
    choco_package: str | None
    winget_id: str | None
    npm_package: str | None
    binary_path: str
    service_name: str | None
    enabled: bool
    tags: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolEntry:
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            category=str(data["category"]),
            description=str(data.get("description", "")),
            choco_package=data.get("choco_package"),
            winget_id=data.get("winget_id"),
            npm_package=data.get("npm_package"),
            binary_path=str(data.get("binary_path", "")),
            service_name=data.get("service_name"),
            enabled=bool(data.get("enabled", True)),
            tags=list(data.get("tags", [])),
        )
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_catalog(path: Path = CATALOG_PATH) -> tuple[dict[str, Any], list[ToolEntry]]:
    if not path.is_file():
        raise FileNotFoundError(f"Catalog file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw_tools = raw.get("tools", [])
    tools = [ToolEntry.from_dict(t) for t in raw_tools]
    return raw, tools


def save_catalog(raw: dict[str, Any], tools: list[ToolEntry], path: Path = CATALOG_PATH) -> None:
    raw["tools"] = [t.to_dict() for t in tools]
    content = json.dumps(raw, indent=2) + "\n"
    path.write_text(content, encoding="utf-8")


def cmd_list(args: argparse.Namespace) -> int:
    try:
        _, tools = load_catalog()
    except Exception as exc:
        print(f"Error loading catalog: {exc}", file=sys.stderr)
        return 1

    filtered = tools
    if args.category:
        filtered = [t for t in filtered if t.category == args.category]
    if args.tag:
        filtered = [t for t in filtered if args.tag.lower() in [tag.lower() for tag in t.tags]]
    if args.enabled_only:
        filtered = [t for t in filtered if t.enabled]

    if args.json:
        print(json.dumps([t.to_dict() for t in filtered], indent=2))
        return 0

    print(f"Windows Tools Catalog ({len(filtered)} items):")
    print("-" * 88)
    print(f"{'STATUS':<8} {'ID':<16} {'CATEGORY':<24} {'NAME'}")
    print("-" * 88)
    for tool in filtered:
        status = "[ON] " if tool.enabled else "[OFF]"
        print(f"{status:<8} {tool.id:<16} {tool.category:<24} {tool.name}")
    print("-" * 88)
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    try:
        _, tools = load_catalog()
    except Exception as exc:
        print(f"Error loading catalog: {exc}", file=sys.stderr)
        return 1

    total = len(tools)
    enabled_count = sum(1 for t in tools if t.enabled)
    disabled_count = total - enabled_count

    categories: dict[str, dict[str, int]] = {}
    for t in tools:
        if t.category not in categories:
            categories[t.category] = {"total": 0, "enabled": 0, "disabled": 0}
        categories[t.category]["total"] += 1
        if t.enabled:
            categories[t.category]["enabled"] += 1
        else:
            categories[t.category]["disabled"] += 1

    summary_data = {
        "total_tools": total,
        "enabled_tools": enabled_count,
        "disabled_tools": disabled_count,
        "categories": categories,
    }

    if args.json:
        print(json.dumps(summary_data, indent=2))
        return 0

    print("Windows Tools Catalog Summary:")
    print(f"  Total tools:    {total}")
    print(f"  Enabled tools:  {enabled_count}")
    print(f"  Disabled tools: {disabled_count}")
    print("\nBreakdown by Category:")
    print(f"{'CATEGORY':<26} {'TOTAL':<8} {'ENABLED':<8} {'DISABLED'}")
    print("-" * 52)
    for cat, stats in sorted(categories.items()):
        print(f"{cat:<26} {stats['total']:<8} {stats['enabled']:<8} {stats['disabled']}")
    return 0


def cmd_toggle(args: argparse.Namespace, enable: bool) -> int:
    try:
        raw, tools = load_catalog()
    except Exception as exc:
        print(f"Error loading catalog: {exc}", file=sys.stderr)
        return 1

    target_id = args.tool_id.strip()
    found = False
    for t in tools:
        if t.id == target_id:
            t.enabled = enable
            found = True
            break

    if not found:
        print(f"Tool with id '{target_id}' not found in catalog.", file=sys.stderr)
        return 1

    save_catalog(raw, tools)
    action = "enabled" if enable else "disabled"
    print(f"Tool '{target_id}' successfully {action}.")
    return 0


def cmd_add_tool(args: argparse.Namespace) -> int:
    try:
        raw, tools = load_catalog()
    except Exception as exc:
        print(f"Error loading catalog: {exc}", file=sys.stderr)
        return 1

    tool_id = args.id.strip().lower()
    if any(t.id == tool_id for t in tools):
        print(f"Error: Tool with id '{tool_id}' already exists.", file=sys.stderr)
        return 1

    category = args.category.strip()
    if category not in VALID_CATEGORIES:
        valid_list = ", ".join(sorted(VALID_CATEGORIES))
        print(f"Error: Invalid category '{category}'. Must be one of: {valid_list}", file=sys.stderr)
        return 1

    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()] if args.tags else []

    new_tool = ToolEntry(
        id=tool_id,
        name=args.name.strip(),
        category=category,
        description=args.description.strip(),
        choco_package=args.choco.strip() if args.choco else None,
        winget_id=args.winget.strip() if args.winget else None,
        npm_package=args.npm.strip() if args.npm else None,
        binary_path=args.binary_path.strip(),
        service_name=args.service.strip() if args.service else None,
        enabled=not args.disabled,
        tags=tags,
    )

    tools.append(new_tool)
    save_catalog(raw, tools)
    print(f"Successfully added tool '{new_tool.id}' ({new_tool.name}) to category '{new_tool.category}'.")
    return 0


def cmd_winrm_script(args: argparse.Namespace) -> int:
    if not WINRM_SCRIPT_PATH.is_file():
        print(f"Error: WinRM script not found at {WINRM_SCRIPT_PATH}", file=sys.stderr)
        return 1

    script_content = WINRM_SCRIPT_PATH.read_text(encoding="utf-8")
    if args.output:
        out_path = Path(args.output).resolve()
        out_path.write_text(script_content, encoding="utf-8")
        print(f"WinRM setup script written to {out_path}")
    else:
        print(script_content)
    return 0


def cmd_generate_inventory(args: argparse.Namespace) -> int:
    host = args.host.strip()
    user = args.user.strip()
    password = args.password
    port = args.port
    transport = args.transport
    scheme = "https" if port == 5986 or transport == "credssp" else "http"

    inventory_text = f"""# Generated Ansible WinRM Inventory for Windows RE VM
[windows_vms]
win-re-vm ansible_host={host} ansible_port={port} ansible_user={user} ansible_password={password}

[windows_vms:vars]
ansible_connection=winrm
ansible_winrm_transport={transport}
ansible_winrm_scheme={scheme}
ansible_winrm_server_cert_validation=ignore
ansible_winrm_operation_timeout_sec=120
ansible_winrm_read_timeout_sec=180
"""

    out_path = Path(args.output).resolve() if args.output else DEFAULT_INVENTORY_PATH
    out_path.write_text(inventory_text, encoding="utf-8")
    print(f"Inventory generated successfully at {out_path}")
    return 0


def cmd_run_playbook(args: argparse.Namespace) -> int:
    ansible_bin = shutil.which("ansible-playbook")
    if not ansible_bin:
        print("Error: 'ansible-playbook' executable not found in PATH.", file=sys.stderr)
        print("Install ansible with your host package manager (e.g. brew install ansible or pip install ansible).", file=sys.stderr)
        return 1

    inv_path = Path(args.inventory).resolve() if args.inventory else DEFAULT_INVENTORY_PATH
    if not inv_path.is_file():
        print(f"Error: Inventory file '{inv_path}' not found.", file=sys.stderr)
        print(f"Run '{Path(__file__).name} generate-inventory --host <IP> --user <User> --password <Pass>' first.", file=sys.stderr)
        return 1

    if not PLAYBOOK_PATH.is_file():
        print(f"Error: Playbook '{PLAYBOOK_PATH}' not found.", file=sys.stderr)
        return 1

    cmd: list[str] = [ansible_bin, "-i", str(inv_path), str(PLAYBOOK_PATH)]

    if args.check:
        cmd.append("--check")
    if args.tags:
        cmd.extend(["--tags", args.tags])
    if args.extra_vars:
        cmd.extend(["--extra-vars", args.extra_vars])
    if args.verbose:
        cmd.append("-" + "v" * min(args.verbose, 4))

    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def cmd_defender(args: argparse.Namespace) -> int:
    action = args.action.strip().lower()
    if action not in ["status", "disable", "enable"]:
        print(f"Error: Invalid defender action '{action}'. Must be status, disable, or enable.", file=sys.stderr)
        return 1

    if args.script_only:
        if not DEFENDER_SCRIPT_PATH.is_file():
            print(f"Error: Defender script not found at {DEFENDER_SCRIPT_PATH}", file=sys.stderr)
            return 1
        script_content = DEFENDER_SCRIPT_PATH.read_text(encoding="utf-8")
        if args.output:
            out_path = Path(args.output).resolve()
            out_path.write_text(script_content, encoding="utf-8")
            print(f"Windows Defender toggle script written to {out_path}")
        else:
            print(script_content)
        return 0

    # Remote execution via Ansible
    ansible_bin = shutil.which("ansible-playbook")
    if not ansible_bin:
        print("Error: 'ansible-playbook' executable not found in PATH.", file=sys.stderr)
        print("To run remotely, install ansible. To get the PowerShell script for direct VM execution, pass --script-only.", file=sys.stderr)
        return 1

    inv_path = Path(args.inventory).resolve() if args.inventory else DEFAULT_INVENTORY_PATH
    if not inv_path.is_file():
        print(f"Error: Inventory file '{inv_path}' not found.", file=sys.stderr)
        print(f"Run '{Path(__file__).name} generate-inventory --host <IP> --user <User> --password <Pass>' first or provide --inventory.", file=sys.stderr)
        return 1

    if not DEFENDER_PLAYBOOK_PATH.is_file():
        print(f"Error: Defender playbook '{DEFENDER_PLAYBOOK_PATH}' not found.", file=sys.stderr)
        return 1

    exclusions_list: list[str] = [p.strip() for p in args.exclusions.split(",") if p.strip()]
    exclusions_json = json.dumps(exclusions_list)
    clear_excl_str = "true" if args.clear_exclusions else "false"

    cmd: list[str] = [
        ansible_bin,
        "-i",
        str(inv_path),
        str(DEFENDER_PLAYBOOK_PATH),
        "-e",
        f"defender_action={action}",
        "-e",
        f"defender_clear_exclusions={clear_excl_str}",
        "-e",
        f"defender_exclusions={exclusions_json}",
    ]
    if args.verbose:
        cmd.append("-" + "v" * min(args.verbose, 4))
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setup_windows_vm.py",
        description="Windows VM Ansible Provisioning & Tool Catalog Manager for Reverse Engineering Labs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="List tools in catalog")
    p_list.add_argument("--category", choices=sorted(VALID_CATEGORIES), help="Filter by category")
    p_list.add_argument("--tag", help="Filter by tag")
    p_list.add_argument("--enabled-only", action="store_true", help="Show only enabled tools")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")

    # summary
    p_summary = subparsers.add_parser("summary", help="Show tool counts and category breakdown")
    p_summary.add_argument("--json", action="store_true", help="Output as JSON")

    # enable-tool
    p_enable = subparsers.add_parser("enable-tool", help="Enable a tool in the catalog")
    p_enable.add_argument("tool_id", help="Tool ID to enable")

    # disable-tool
    p_disable = subparsers.add_parser("disable-tool", help="Disable a tool in the catalog")
    p_disable.add_argument("tool_id", help="Tool ID to disable")

    # add-tool
    p_add = subparsers.add_parser("add-tool", help="Add a new tool entry to the catalog")
    p_add.add_argument("--id", required=True, help="Unique tool ID")
    p_add.add_argument("--name", required=True, help="Display name")
    p_add.add_argument("--category", required=True, choices=sorted(VALID_CATEGORIES), help="Tool category")
    p_add.add_argument("--description", default="", help="Tool description")
    p_add.add_argument("--choco", default=None, help="Chocolatey package name")
    p_add.add_argument("--winget", default=None, help="Winget package ID")
    p_add.add_argument("--npm", default=None, help="NPM package name (e.g. @zavora-ai/computer-use-mcp)")
    p_add.add_argument("--binary-path", required=True, help="Expected path to installed binary")
    p_add.add_argument("--service", default=None, help="Windows Service name (if applicable)")
    p_add.add_argument("--tags", default="", help="Comma-separated tags")
    p_add.add_argument("--disabled", action="store_true", help="Add in disabled state")

    # winrm-script
    p_winrm = subparsers.add_parser("winrm-script", help="Print or export PowerShell WinRM setup script")
    p_winrm.add_argument("-o", "--output", help="Write script to output file path")

    # generate-inventory
    p_inv = subparsers.add_parser("generate-inventory", help="Generate Ansible WinRM inventory file")
    p_inv.add_argument("--host", required=True, help="VM Hostname or IP address")
    p_inv.add_argument("--user", required=True, help="Admin username")
    p_inv.add_argument("--password", required=True, help="Admin password")
    p_inv.add_argument("--port", type=int, default=5985, help="WinRM port (default: 5985)")
    p_inv.add_argument("--transport", default="ntlm", choices=["ntlm", "basic", "credssp"], help="WinRM transport auth")
    p_inv.add_argument("-o", "--output", help="Output file path (default: ansible/inventory.ini)")

    # run-playbook
    p_play = subparsers.add_parser("run-playbook", help="Run Ansible provisioning playbook")
    p_play.add_argument("-i", "--inventory", help="Path to inventory file")
    p_play.add_argument("--check", action="store_true", help="Run Ansible in dry-run/check mode")
    p_play.add_argument("--tags", help="Only run plays/tasks tagged with these values")
    p_play.add_argument("--extra-vars", help="Extra variables string for Ansible")
    p_play.add_argument("-v", "--verbose", action="count", default=0, help="Verbose output (-v, -vv, -vvv)")
    # defender
    p_def = subparsers.add_parser("defender", help="Manage Windows Defender state (toggle, status, disable, enable)")
    p_def.add_argument("--action", default="status", choices=["status", "disable", "enable"], help="Action to perform (default: status)")
    p_def.add_argument("--clear-exclusions", action="store_true", default=False, help="Clear specified exclusion paths when enabling/managing Defender")
    p_def.add_argument("--exclusions", default="C:\\Tools,C:\\Workspace", help="Comma-separated exclusion paths (default: C:\\Tools,C:\\Workspace)")
    p_def.add_argument("--script-only", action="store_true", help="Print or export PowerShell toggle script instead of running Ansible")
    p_def.add_argument("-o", "--output", help="Output file path when using --script-only")
    p_def.add_argument("-i", "--inventory", help="Path to Ansible inventory file for remote execution")
    p_def.add_argument("-v", "--verbose", action="count", default=0, help="Verbose output (-v, -vv, -vvv)")

    return parser

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        return cmd_list(args)
    elif args.command == "summary":
        return cmd_summary(args)
    elif args.command == "enable-tool":
        return cmd_toggle(args, enable=True)
    elif args.command == "disable-tool":
        return cmd_toggle(args, enable=False)
    elif args.command == "add-tool":
        return cmd_add_tool(args)
    elif args.command == "winrm-script":
        return cmd_winrm_script(args)
    elif args.command == "generate-inventory":
        return cmd_generate_inventory(args)
    elif args.command == "run-playbook":
        return cmd_run_playbook(args)
    elif args.command == "defender":
        return cmd_defender(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
