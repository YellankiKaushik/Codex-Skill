from __future__ import annotations

import json
import sys
from enum import IntEnum
from typing import Any


class ExitCode(IntEnum):
    SUCCESS = 0
    USAGE = 2
    SAFETY_BLOCKER = 3
    VALIDATION_FAILURE = 4
    GIT_FAILURE = 5
    SYNC_CONFLICT = 6


class GGCPError(Exception):
    def __init__(self, message: str, code: ExitCode = ExitCode.VALIDATION_FAILURE, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.payload = payload or {}


def dump_json(data: Any) -> None:
    sys.stdout.write(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True))
    sys.stdout.write("\n")


def error_payload(error: GGCPError) -> dict[str, Any]:
    return {"ok": False, "error": {"message": error.message, "code": error.code.name, **error.payload}}
