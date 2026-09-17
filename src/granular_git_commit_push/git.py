from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .output import ExitCode, GGCPError


@dataclass(frozen=True)
class GitResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def run_git(args: list[str], cwd: Path | None = None, env: dict[str, str] | None = None, check: bool = True) -> GitResult:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            env=merged_env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise GGCPError("Git executable was not found on PATH.", ExitCode.GIT_FAILURE) from exc
    result = GitResult(tuple(args), completed.returncode, completed.stdout, completed.stderr)
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise GGCPError(f"git {' '.join(args)} failed: {detail}", ExitCode.GIT_FAILURE, {"git_args": args})
    return result


def repository_root(path: Path | None = None) -> Path:
    result = run_git(["rev-parse", "--show-toplevel"], cwd=path, check=True)
    return Path(result.stdout.strip()).resolve()


def optional_git(args: list[str], cwd: Path | None = None) -> str | None:
    result = run_git(args, cwd=cwd, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def current_branch(root: Path) -> str | None:
    return optional_git(["branch", "--show-current"], cwd=root)


def head_sha(root: Path) -> str | None:
    return optional_git(["rev-parse", "--verify", "HEAD"], cwd=root)


def remote_url(root: Path, name: str = "origin") -> str | None:
    return optional_git(["remote", "get-url", name], cwd=root)


def upstream_ref(root: Path) -> str | None:
    return optional_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=root)


def list_remotes(root: Path) -> list[dict[str, str]]:
    result = run_git(["remote", "-v"], cwd=root)
    remotes: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            remotes.append({"name": parts[0], "url": parts[1], "direction": parts[2].strip("()")})
    return remotes


def git_dir(root: Path) -> Path:
    result = run_git(["rev-parse", "--git-dir"], cwd=root)
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = root / path
    return path

