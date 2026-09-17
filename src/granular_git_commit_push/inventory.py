from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .git import current_branch, git_dir, head_sha, list_remotes, optional_git, remote_url, repository_root, run_git, upstream_ref


@dataclass(frozen=True)
class Change:
    kind: str
    path: str
    old_path: str | None = None
    staged: bool = False
    unstaged: bool = True
    status_code: str = ""

    def paths(self) -> list[str]:
        return [p for p in [self.old_path, self.path] if p]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "old_path": self.old_path,
            "staged": self.staged,
            "unstaged": self.unstaged,
            "status_code": self.status_code,
        }


@dataclass(frozen=True)
class Inventory:
    repository: str
    branch: str | None
    head: str | None
    upstream: str | None
    origin: str | None
    remotes: list[dict[str, str]]
    operation: dict[str, bool]
    staged_changes: list[Change] = field(default_factory=list)
    changes: list[Change] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "branch": self.branch,
            "head": self.head,
            "upstream": self.upstream,
            "origin": self.origin,
            "remotes": self.remotes,
            "operation": self.operation,
            "staged_changes": [change.to_dict() for change in self.staged_changes],
            "changes": [change.to_dict() for change in self.changes],
        }


def _parse_name_status_parts(parts: list[str]) -> Change:
    code = parts[0]
    if code.startswith("R") or code.startswith("C"):
        return Change(kind="rename", old_path=parts[1], path=parts[2], status_code=code)
    mapping = {"M": "modify", "A": "add", "D": "delete"}
    return Change(kind=mapping.get(code[:1], "modify"), path=parts[1], status_code=code)


def _parse_porcelain(line: str) -> Change:
    code = line[:2]
    raw = line[3:]
    staged = code[0] not in (" ", "?")
    unstaged = code[1] not in (" ", "?")
    if " -> " in raw:
        old, new = raw.split(" -> ", 1)
        return Change(kind="rename", old_path=old, path=new, staged=staged, unstaged=unstaged, status_code=code)
    if code == "??":
        kind = "add"
    elif "D" in code:
        kind = "delete"
    elif "A" in code:
        kind = "add"
    else:
        kind = "modify"
    return Change(kind=kind, path=raw, staged=staged, unstaged=unstaged, status_code=code)


def _operation_state(root: Path) -> dict[str, bool]:
    gd = git_dir(root)
    return {
        "merge": (gd / "MERGE_HEAD").exists(),
        "rebase": (gd / "rebase-merge").exists() or (gd / "rebase-apply").exists(),
        "cherry_pick": (gd / "CHERRY_PICK_HEAD").exists(),
        "revert": (gd / "REVERT_HEAD").exists(),
    }


def _porcelain_changes(root: Path) -> list[Change]:
    output = run_git(["status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=root).stdout
    records = [record for record in output.split("\0") if record]
    changes: list[Change] = []
    index = 0
    while index < len(records):
        record = records[index]
        code = record[:2]
        path = record[3:]
        staged = code[0] not in (" ", "?")
        unstaged = code[1] not in (" ", "?")
        if code[0] in ("R", "C"):
            old_path = records[index + 1]
            changes.append(Change(kind="rename", old_path=old_path, path=path, staged=staged, unstaged=unstaged, status_code=code))
            index += 2
            continue
        if code == "??":
            kind = "add"
        elif "D" in code:
            kind = "delete"
        elif "A" in code:
            kind = "add"
        else:
            kind = "modify"
        changes.append(Change(kind=kind, path=path, staged=staged, unstaged=unstaged, status_code=code))
        index += 1
    return changes


def _staged_changes(root: Path) -> list[Change]:
    output = run_git(["diff", "--cached", "--name-status", "-z"], cwd=root).stdout
    return _parse_name_status_z(output)


def _parse_name_status_z(output: str) -> list[Change]:
    records = [record for record in output.split("\0") if record]
    changes: list[Change] = []
    index = 0
    while index < len(records):
        code = records[index]
        if code.startswith("R") or code.startswith("C"):
            changes.append(_parse_name_status_parts([code, records[index + 1], records[index + 2]]))
            index += 3
        else:
            changes.append(_parse_name_status_parts([code, records[index + 1]]))
            index += 2
    return changes


def _rename_detected_changes(root: Path, porcelain: list[Change]) -> list[Change]:
    if not porcelain or head_sha(root) is None:
        return porcelain
    paths: list[str] = []
    for change in porcelain:
        paths.extend(change.paths())
    with tempfile.NamedTemporaryFile(prefix="ggcp-index-", delete=False) as handle:
        index_path = handle.name
    try:
        env = {"GIT_INDEX_FILE": index_path}
        run_git(["read-tree", "HEAD"], cwd=root, env=env)
        run_git(["add", "-A", "--", *paths], cwd=root, env=env)
        diff = run_git(["diff", "--cached", "--name-status", "-z", "--find-renames=50%"], cwd=root, env=env).stdout
        changes = _parse_name_status_z(diff)
        return changes or porcelain
    finally:
        try:
            os.unlink(index_path)
        except FileNotFoundError:
            pass


def inspect_repository(path: Path | None = None) -> Inventory:
    root = repository_root(path)
    porcelain = _porcelain_changes(root)
    staged = _staged_changes(root)
    changes = _rename_detected_changes(root, porcelain)
    return Inventory(
        repository=str(root),
        branch=current_branch(root),
        head=head_sha(root),
        upstream=upstream_ref(root),
        origin=remote_url(root),
        remotes=list_remotes(root),
        operation=_operation_state(root),
        staged_changes=staged,
        changes=changes,
    )


def is_clean(inventory: Inventory) -> bool:
    return not inventory.changes and not inventory.staged_changes
