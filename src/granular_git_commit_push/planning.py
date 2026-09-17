from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .inventory import Change, Inventory, inspect_repository
from .output import ExitCode, GGCPError
from .safety import sensitive_paths

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PlanEntry:
    kind: str
    paths: list[str]
    message: str
    old_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {"kind": self.kind, "paths": self.paths, "message": self.message}
        if self.old_path:
            data["old_path"] = self.old_path
        return data


@dataclass(frozen=True)
class Plan:
    schema_version: int
    repository: str
    base_head: str | None
    branch: str | None
    entries: list[PlanEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository": self.repository,
            "base_head": self.base_head,
            "branch": self.branch,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Plan":
        try:
            entries = [
                PlanEntry(kind=item["kind"], paths=list(item["paths"]), message=item["message"], old_path=item.get("old_path"))
                for item in data["entries"]
            ]
            return Plan(
                schema_version=int(data["schema_version"]),
                repository=str(data["repository"]),
                base_head=data.get("base_head"),
                branch=data.get("branch"),
                entries=entries,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GGCPError("Plan file is malformed.", ExitCode.VALIDATION_FAILURE) from exc


def message_for(change: Change) -> str:
    path = change.path
    leaf = Path(path).stem.lower().replace("_", "-")
    scope = "".join(ch for ch in leaf if ch.isalnum() or ch == "-").strip("-") or "files"
    normalized = path.replace("\\", "/")
    if change.kind == "delete":
        return f"chore({scope}): remove {Path(path).name}"
    if change.kind == "rename":
        return f"refactor({scope}): move {Path(path).name}"
    if normalized.startswith("docs/") or normalized.endswith(".md"):
        return f"docs({scope}): update {Path(path).name}"
    if normalized.startswith("tests/") or ".test." in normalized or ".spec." in normalized:
        return f"test({scope}): update {Path(path).name}"
    if Path(path).name in {"package.json", "pyproject.toml"} or normalized.startswith(".github/"):
        return f"build({scope}): update {Path(path).name}"
    if change.kind == "add":
        return f"feat({scope}): add {Path(path).name}"
    return f"chore({scope}): update {Path(path).name}"


def create_plan(inventory: Inventory) -> Plan:
    if inventory.staged_changes:
        raise GGCPError(
            "Existing staged changes are protected. Unstage or commit them before running ggcp.",
            ExitCode.SAFETY_BLOCKER,
            {"blocker": "STAGED_WORK", "staged_changes": [change.to_dict() for change in inventory.staged_changes]},
        )
    sensitive = sensitive_paths([path for change in inventory.changes for path in change.paths()])
    if sensitive:
        raise GGCPError(
            "Sensitive-looking paths are present. ggcp will not plan them automatically.",
            ExitCode.SAFETY_BLOCKER,
            {"blocker": "SENSITIVE_PATH", "paths": sensitive},
        )
    entries: list[PlanEntry] = []
    for change in sorted(inventory.changes, key=lambda item: (item.path, item.old_path or "")):
        paths = change.paths()
        entries.append(PlanEntry(kind=change.kind, old_path=change.old_path, paths=paths, message=message_for(change)))
    return Plan(SCHEMA_VERSION, inventory.repository, inventory.head, inventory.branch, entries)


def save_plan(plan: Plan, path: Path) -> None:
    text = json.dumps(plan.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def load_plan(path: Path) -> Plan:
    return Plan.from_dict(json.loads(path.read_text(encoding="utf-8")))


def validate_plan(plan: Plan, inventory: Inventory) -> None:
    if plan.schema_version != SCHEMA_VERSION:
        raise GGCPError("Unsupported plan schema version.", ExitCode.VALIDATION_FAILURE)
    if str(Path(plan.repository).resolve()) != str(Path(inventory.repository).resolve()):
        raise GGCPError("Plan repository does not match the current repository.", ExitCode.VALIDATION_FAILURE, {"blocker": "REPOSITORY_MISMATCH"})
    if plan.base_head and inventory.head and plan.base_head != inventory.head:
        raise GGCPError("Plan is stale because HEAD changed.", ExitCode.VALIDATION_FAILURE, {"blocker": "STALE_PLAN"})
    if inventory.staged_changes:
        raise GGCPError("Existing staged changes are protected.", ExitCode.SAFETY_BLOCKER, {"blocker": "STAGED_WORK"})
    current_paths = sorted(path for change in inventory.changes for path in change.paths())
    planned_paths = sorted(path for entry in plan.entries for path in entry.paths)
    if current_paths != planned_paths:
        raise GGCPError(
            "Plan paths do not match the current Git inventory.",
            ExitCode.VALIDATION_FAILURE,
            {"blocker": "PLAN_PATH_MISMATCH", "current_paths": current_paths, "planned_paths": planned_paths},
        )


def plan_for_repository(path: Path | None = None) -> Plan:
    return create_plan(inspect_repository(path))

