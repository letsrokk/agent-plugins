from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

Scope = Literal["project", "user"]
Severity = Literal["minor", "major", "blocker"]
Status = Literal["open", "resolved"]


@dataclass(frozen=True)
class ProjectRef:
    id: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class StorageContext:
    project: ProjectRef
    project_root: Path
    journal_path: Path
    scope: Scope
    config_source: Path | None


@dataclass(frozen=True)
class PrunePolicy:
    resolved_older_than_days: int = 30
    open_max_encounters: int = 1
    open_inactive_for_days: int = 90
    projects: Literal["current", "all"] = "current"

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


class PapercutsError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_status: int,
        retryable: bool = False,
        suggested_fix: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_status = exit_status
        self.retryable = retryable
        self.suggested_fix = suggested_fix


def success_envelope(data: Any, *, journal_path: Path) -> dict[str, Any]:
    return {"ok": True, "data": data, "meta": {"contract": 1, "file": str(journal_path)}}


def error_envelope(error: PapercutsError) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": error.code,
            "message": error.message,
            "retryable": error.retryable,
            "suggested_fix": error.suggested_fix,
        },
        "meta": {"contract": 1},
    }
