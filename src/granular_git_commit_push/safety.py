from __future__ import annotations

import fnmatch
from pathlib import PurePosixPath


SENSITIVE_PATTERNS = (
    ".env",
    ".env.*",
    "credentials.json",
    "service-account.json",
    "*.pem",
    "*.key",
    "id_rsa",
    "id_ed25519",
    "secrets.*",
    "private-key.*",
    "firebase-adminsdk*.json",
)


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def is_sensitive_path(path: str) -> bool:
    normalized = normalize_path(path)
    name = PurePosixPath(normalized).name
    return any(fnmatch.fnmatchcase(name.lower(), pattern.lower()) for pattern in SENSITIVE_PATTERNS)


def sensitive_paths(paths: list[str]) -> list[str]:
    return sorted({path for path in paths if is_sensitive_path(path)})

