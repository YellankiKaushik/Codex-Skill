from __future__ import annotations

from pathlib import Path
from typing import Any

from .git import run_git
from .inventory import inspect_repository


def recovery_state(path: Path | None = None) -> dict[str, Any]:
    inventory = inspect_repository(path)
    root = Path(inventory.repository)
    branch = inventory.branch
    state: dict[str, Any] = {"inventory": inventory.to_dict(), "recommendations": []}
    if inventory.operation["rebase"]:
        state["state"] = "rebase_in_progress"
        state["recommendations"].append("Resolve conflicts, then run git rebase --continue or abort according to user intent.")
        return state
    if inventory.operation["merge"]:
        state["state"] = "merge_in_progress"
        state["recommendations"].append("Resolve or abort the merge before ggcp execution.")
        return state
    if inventory.changes:
        state["state"] = "uncommitted_changes"
        state["recommendations"].append("Run ggcp inspect, ggcp plan, then ggcp execute when ready.")
    elif branch:
        upstream = inventory.upstream
        if upstream:
            ahead = int(run_git(["rev-list", "--count", f"{upstream}..HEAD"], cwd=root).stdout.strip())
            behind = int(run_git(["rev-list", "--count", f"HEAD..{upstream}"], cwd=root).stdout.strip())
            state["ahead"] = ahead
            state["behind"] = behind
            if ahead and behind:
                state["state"] = "diverged"
                state["recommendations"].append("Fetch and rebase safely; do not force-push.")
            elif ahead:
                state["state"] = "local_ahead"
                state["recommendations"].append("Verify clean tree, then push.")
            elif behind:
                state["state"] = "remote_ahead"
                state["recommendations"].append("Fetch and rebase before creating new commits.")
            else:
                state["state"] = "clean_synced"
        else:
            state["state"] = "no_upstream"
            state["recommendations"].append("Configure an upstream before push operations.")
    return state

