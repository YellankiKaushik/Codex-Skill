from __future__ import annotations

import os
import shutil
from pathlib import Path

from .output import ExitCode, GGCPError

SKILL_NAME = "granular-git-commit-push"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_skill_dir() -> Path:
    return project_root() / "skills" / SKILL_NAME


def user_skill_dir() -> Path:
    return Path.home() / ".agents" / "skills" / SKILL_NAME


def install_skill(mode: str = "copy") -> dict[str, str]:
    source = canonical_skill_dir()
    target = user_skill_dir()
    if not source.exists():
        raise GGCPError(f"Canonical skill not found: {source}", ExitCode.VALIDATION_FAILURE)
    if target.exists() or target.is_symlink():
        if not _recognized_install(target, source):
            raise GGCPError(f"Refusing to overwrite unrelated skill installation: {target}", ExitCode.SAFETY_BLOCKER)
        uninstall_skill()
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "link":
        try:
            if os.name == "nt":
                os.symlink(source, target, target_is_directory=True)
            else:
                target.symlink_to(source, target_is_directory=True)
            install_type = "link"
        except OSError:
            shutil.copytree(source, target)
            install_type = "copy"
    else:
        shutil.copytree(source, target)
        install_type = "copy"
    marker = target / ".ggcp-install"
    marker.write_text(f"source={source}\ntype={install_type}\n", encoding="utf-8")
    return {"source": str(source), "target": str(target), "type": install_type}


def uninstall_skill() -> dict[str, str]:
    source = canonical_skill_dir()
    target = user_skill_dir()
    if not target.exists() and not target.is_symlink():
        return {"target": str(target), "status": "not-installed"}
    if not _recognized_install(target, source):
        raise GGCPError(f"Refusing to remove unrecognized skill installation: {target}", ExitCode.SAFETY_BLOCKER)
    if target.is_symlink():
        target.unlink()
    else:
        shutil.rmtree(target)
    return {"target": str(target), "status": "removed"}


def _recognized_install(target: Path, source: Path) -> bool:
    marker = target / ".ggcp-install"
    if marker.exists():
        return True
    if target.is_symlink():
        try:
            return target.resolve() == source.resolve()
        except OSError:
            return False
    return False

