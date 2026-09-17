from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .execution import execute_plan
from .git import optional_git, repository_root, run_git
from .installer import install_skill, uninstall_skill, user_skill_dir
from .inventory import inspect_repository, is_clean
from .output import ExitCode, GGCPError, dump_json, error_payload
from .planning import create_plan, load_plan, plan_for_repository, save_plan, validate_plan
from .recovery import recovery_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ggcp", description="Granular Git Commit Push deterministic CLI")
    parser.add_argument("--version", action="store_true", help="Show ggcp version and exit.")
    sub = parser.add_subparsers(dest="command")
    for name in ["doctor", "inspect", "plan", "status", "recover", "compatibility"]:
        p = sub.add_parser(name)
        p.add_argument("--json", action="store_true")
    plan = sub.choices["plan"]
    plan.add_argument("--output", type=Path)
    validate = sub.add_parser("validate-plan")
    validate.add_argument("file", type=Path)
    execute = sub.add_parser("execute")
    execute.add_argument("--plan", type=Path)
    execute.add_argument("--no-push", action="store_true")
    execute.add_argument("--dry-run", action="store_true")
    execute.add_argument("--json", action="store_true")
    execute.add_argument("--yes", action="store_true", help="Skip interactive confirmation when stdin is a TTY.")
    install = sub.add_parser("install-skill")
    install.add_argument("--copy", action="store_true")
    install.add_argument("--link", action="store_true")
    install.add_argument("--json", action="store_true")
    uninstall = sub.add_parser("uninstall-skill")
    uninstall.add_argument("--json", action="store_true")
    return parser


def command_doctor(as_json: bool) -> int:
    payload: dict[str, Any] = {
        "python": {"version": platform.python_version(), "supported": sys.version_info >= (3, 10)},
        "git": {"available": False, "version": None},
        "skill": {"user_path": str(user_skill_dir()), "found": user_skill_dir().exists()},
    }
    git_version = optional_git(["--version"])
    payload["git"] = {"available": bool(git_version), "version": git_version}
    try:
        inventory = inspect_repository()
        payload["repository"] = inventory.to_dict()
        payload["compatible"] = bool(git_version)
    except GGCPError as exc:
        payload["repository_error"] = exc.message
        payload["compatible"] = False
    if as_json:
        dump_json(payload)
    else:
        print(f"Python: {payload['python']['version']} ({'ok' if payload['python']['supported'] else 'unsupported'})")
        print(f"Git: {payload['git']['version'] or 'not found'}")
        repo = payload.get("repository")
        if repo:
            print(f"Repository: {repo['repository']}")
            print(f"Branch: {repo['branch'] or '(detached)'}")
            print(f"Origin: {repo['origin'] or '(none)'}")
            print(f"Working tree: {'clean' if not repo['changes'] and not repo['staged_changes'] else 'dirty'}")
        print(f"Agent Skill: {'found' if payload['skill']['found'] else 'not installed'} at {payload['skill']['user_path']}")
    return int(ExitCode.SUCCESS if payload["compatible"] else ExitCode.SAFETY_BLOCKER)


def command_inspect(as_json: bool) -> int:
    inventory = inspect_repository()
    if as_json:
        dump_json(inventory.to_dict())
    else:
        print(f"Repository: {inventory.repository}")
        print(f"Branch: {inventory.branch or '(detached)'}")
        print(f"Origin: {inventory.origin or '(none)'}")
        for change in inventory.changes:
            prefix = f"{change.kind:7}"
            if change.old_path:
                print(f"{prefix} {change.old_path} -> {change.path}")
            else:
                print(f"{prefix} {change.path}")
    return int(ExitCode.SUCCESS)


def command_plan(as_json: bool, output: Path | None) -> int:
    plan = plan_for_repository()
    if output:
        save_plan(plan, output)
    if as_json:
        dump_json(plan.to_dict())
    else:
        print(f"Repository: {plan.repository}")
        print(f"Planned commits: {len(plan.entries)}")
        for index, entry in enumerate(plan.entries, 1):
            print(f"{index}. {entry.kind}: {', '.join(entry.paths)}")
            print(f"   {entry.message}")
        if output:
            print(f"Wrote plan: {output}")
    return int(ExitCode.SUCCESS)


def command_validate(path: Path) -> int:
    plan = load_plan(path)
    validate_plan(plan, inspect_repository())
    print("Plan is valid.")
    return int(ExitCode.SUCCESS)


def command_execute(args: argparse.Namespace) -> int:
    plan = load_plan(args.plan) if args.plan else plan_for_repository()
    if sys.stdin.isatty() and not args.dry_run and not args.yes:
        response = input(f"Execute {len(plan.entries)} planned commit(s)? Type 'yes' to continue: ")
        if response.strip().lower() != "yes":
            raise GGCPError("Execution cancelled.", ExitCode.USAGE)
    result = execute_plan(plan, dry_run=args.dry_run, no_push=args.no_push)
    if args.json:
        dump_json(result)
    else:
        print(f"Commits created: {result['commits_created']}")
        if result.get("dry_run"):
            print("Dry run only; no changes were made.")
        elif result.get("sync", {}).get("pushed"):
            print("Push completed.")
        elif result.get("sync", {}).get("skipped"):
            print("Push skipped.")
    return int(ExitCode.SUCCESS)


def command_status(as_json: bool) -> int:
    inventory = inspect_repository()
    payload = {"clean": is_clean(inventory), "inventory": inventory.to_dict()}
    if as_json:
        dump_json(payload)
    else:
        print("clean" if payload["clean"] else "dirty")
    return int(ExitCode.SUCCESS)


def command_recover(as_json: bool) -> int:
    payload = recovery_state()
    if as_json:
        dump_json(payload)
    else:
        print(f"State: {payload.get('state', 'unknown')}")
        for item in payload.get("recommendations", []):
            print(f"- {item}")
    return int(ExitCode.SUCCESS)


def command_compatibility(as_json: bool) -> int:
    payload = {
        "format": "Agent Skills SKILL.md with YAML frontmatter name and description",
        "canonical_skill": "skills/granular-git-commit-push",
        "install_target": str(user_skill_dir()),
        "agents": [
            {"name": "OpenAI Codex", "support": "plugin and Agent Skills", "detected": False},
            {"name": "GitHub Copilot", "support": "Agent Skills", "detected": False},
            {"name": "Cursor", "support": "Agent Skills", "detected": False},
            {"name": "Gemini CLI", "support": "Agent Skills", "detected": False},
            {"name": "OpenCode", "support": "Agent Skills / local skill directories", "detected": False},
            {"name": "Claude", "support": "Agent Skills", "detected": False},
        ],
    }
    if as_json:
        dump_json(payload)
    else:
        print(f"Supported format: {payload['format']}")
        print(f"Canonical skill: {payload['canonical_skill']}")
        print(f"User install target: {payload['install_target']}")
        for agent in payload["agents"]:
            print(f"- {agent['name']}: {agent['support']} (detected locally: {agent['detected']})")
    return int(ExitCode.SUCCESS)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.version:
            print(__version__)
            return int(ExitCode.SUCCESS)
        if args.command == "doctor":
            return command_doctor(args.json)
        if args.command == "inspect":
            return command_inspect(args.json)
        if args.command == "plan":
            return command_plan(args.json, args.output)
        if args.command == "validate-plan":
            return command_validate(args.file)
        if args.command == "execute":
            return command_execute(args)
        if args.command == "status":
            return command_status(args.json)
        if args.command == "recover":
            return command_recover(args.json)
        if args.command == "install-skill":
            result = install_skill("link" if args.link and not args.copy else "copy")
            dump_json(result) if args.json else print(f"Installed skill to {result['target']} ({result['type']})")
            return int(ExitCode.SUCCESS)
        if args.command == "uninstall-skill":
            result = uninstall_skill()
            dump_json(result) if args.json else print(f"Skill uninstall status: {result['status']}")
            return int(ExitCode.SUCCESS)
        if args.command == "compatibility":
            return command_compatibility(args.json)
        parser.print_help()
        return int(ExitCode.USAGE)
    except GGCPError as exc:
        if getattr(args, "json", False):
            dump_json(error_payload(exc))
        else:
            print(f"ggcp: {exc.message}", file=sys.stderr)
        return int(exc.code)


if __name__ == "__main__":
    raise SystemExit(main())
