from __future__ import annotations

from pathlib import Path

from .git import current_branch, remote_url, run_git, upstream_ref
from .inventory import inspect_repository
from .output import ExitCode, GGCPError
from .planning import Plan, validate_plan


def _staged_paths(root: Path) -> list[str]:
    output = run_git(["diff", "--cached", "--name-only"], cwd=root).stdout
    return sorted(line for line in output.splitlines() if line)


def _stage_entry(root: Path, paths: list[str]) -> None:
    for path in paths:
        run_git(["add", "-A", "--", path], cwd=root)


def _commit(root: Path, message: str) -> None:
    run_git(["commit", "-m", message], cwd=root)


def execute_plan(plan: Plan, dry_run: bool = False, no_push: bool = False) -> dict[str, object]:
    root = Path(plan.repository)
    inventory = inspect_repository(root)
    validate_plan(plan, inventory)
    if dry_run:
        return {"ok": True, "dry_run": True, "commits_created": 0, "entries": [entry.to_dict() for entry in plan.entries]}
    created: list[str] = []
    for entry in plan.entries:
        _stage_entry(root, entry.paths)
        staged = _staged_paths(root)
        if staged != sorted(entry.paths):
            raise GGCPError(
                "Staging area does not match the intended plan entry.",
                ExitCode.SAFETY_BLOCKER,
                {"blocker": "STAGING_MISMATCH", "expected": sorted(entry.paths), "actual": staged},
            )
        _commit(root, entry.message)
        sha = run_git(["rev-parse", "--short", "HEAD"], cwd=root).stdout.strip()
        created.append(sha)
        if _staged_paths(root):
            raise GGCPError("Unexpected staged files remain after commit.", ExitCode.SAFETY_BLOCKER)
    remaining = inspect_repository(root)
    if remaining.changes or remaining.staged_changes:
        raise GGCPError(
            "Unexpected changes remain after executing the plan.",
            ExitCode.SAFETY_BLOCKER,
            {"blocker": "UNEXPECTED_REMAINING", "inventory": remaining.to_dict()},
        )
    sync = {"pushed": False, "skipped": bool(no_push)}
    if not no_push:
        sync = synchronize_and_push(root)
    return {"ok": True, "dry_run": False, "commits_created": len(created), "commits": created, "sync": sync}


def synchronize_and_push(root: Path) -> dict[str, object]:
    branch = current_branch(root)
    if not branch:
        raise GGCPError("Cannot push from detached HEAD.", ExitCode.SAFETY_BLOCKER, {"blocker": "DETACHED_HEAD"})
    origin = remote_url(root)
    if not origin:
        raise GGCPError("No origin remote is configured.", ExitCode.SAFETY_BLOCKER, {"blocker": "NO_REMOTE"})
    run_git(["fetch", "origin"], cwd=root)
    remote_ref = f"origin/{branch}"
    remote_exists = run_git(["rev-parse", "--verify", remote_ref], cwd=root, check=False).returncode == 0
    if remote_exists:
        behind = int(run_git(["rev-list", "--count", f"HEAD..{remote_ref}"], cwd=root).stdout.strip())
        if behind > 0:
            result = run_git(["rebase", remote_ref], cwd=root, check=False)
            if result.returncode != 0:
                raise GGCPError("Rebase failed; resolve conflicts before pushing.", ExitCode.SYNC_CONFLICT, {"blocker": "REBASE_CONFLICT"})
    final_inventory = inspect_repository(root)
    if final_inventory.changes or final_inventory.staged_changes:
        raise GGCPError("Working tree must be clean before push.", ExitCode.SAFETY_BLOCKER, {"blocker": "DIRTY_BEFORE_PUSH"})
    run_git(["push", "-u", "origin", branch], cwd=root)
    return {"pushed": True, "branch": branch, "origin": origin, "upstream": upstream_ref(root)}

