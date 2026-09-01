from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

Scope = Literal["project", "user"]
Severity = Literal["minor", "major", "blocker"]
Status = Literal["open", "resolved"]

_CONTEXT_KEYS = {"command", "exit_status", "stderr", "stderr_file", "note"}
_EVIDENCE_FILE_LIMIT = 1024 * 1024
_ASSIGNMENT_SECRET = re.compile(
    r"(?i)((?<![A-Za-z0-9_.-])[\"']?(?=[A-Za-z_])[A-Za-z0-9_.-]*"
    r"(?:TOKEN|SECRET|PASSWORD|API_KEY)[A-Za-z0-9_.-]*[\"']?\s*[:=]\s*)"
    r"(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;]+)"
)
_BEARER_SECRET = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_URL_CREDENTIALS = re.compile(
    r"(?i)\b([a-z][a-z0-9+.-]*://)[^/\s:@]+(?::[^/\s@]*)?@"
)
_GITHUB_SECRET = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"
)
_OPENAI_SECRET = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")
_URL = re.compile(r"(?i)\b(?:https?|ssh|git|ftp|file)://[^\s\"']+")
_SCP_REMOTE = re.compile(
    r"(?i)(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9_.-]+@)?"
    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}:[^\s\"']+"
)
_WINDOWS_ABSOLUTE_PATH = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)[^\s\"']+"
)
_POSIX_ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9:/])/(?!/)[^\s\"']*")
_ENVIRONMENT_LINE = re.compile(r"^(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*=.*$")
_ENVIRONMENT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ENVIRONMENT_OBJECT = re.compile(
    r"(?is)^(?:os\.)?(?:env|environ|environment)\s*(?:\(|=|:)\s*\{"
)
_COMMON_ENVIRONMENT_NAMES = {
    "home",
    "path",
    "pwd",
    "shell",
    "temp",
    "tmp",
    "user",
    "userprofile",
}


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


def sanitize_context(
    context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate, redact, and bound evidence before it reaches the journal."""
    if context is None:
        return {}
    if not isinstance(context, Mapping):
        raise _invalid_evidence("context must be an object")

    keys = set(context)
    if not all(isinstance(key, str) for key in keys):
        raise _invalid_evidence("context keys must be strings")
    environment_keys = {
        key for key in keys if key.casefold() in {"env", "environment", "environ"}
    }
    if environment_keys:
        raise _invalid_evidence("raw environment evidence is not allowed")
    unknown = keys - _CONTEXT_KEYS
    if unknown:
        raise _invalid_evidence("context contains unsupported evidence fields")
    if "stderr" in context and "stderr_file" in context:
        raise _invalid_evidence("provide stderr or stderr_file, not both")

    sanitized: dict[str, Any] = {}
    for key in ("command", "note"):
        if key not in context:
            continue
        value = context[key]
        if not isinstance(value, str):
            raise _invalid_evidence(f"{key} must be a string")
        _reject_environment_dump(value)
        redacted = _redact(value)
        limit = 1024 if key == "command" else 2048
        if len(redacted) > limit:
            raise _invalid_evidence(f"{key} exceeds {limit} characters")
        sanitized[key] = redacted

    if "exit_status" in context:
        exit_status = context["exit_status"]
        if type(exit_status) is not int:
            raise _invalid_evidence("exit_status must be an integer")
        sanitized["exit_status"] = exit_status

    stderr: str | None = None
    if "stderr" in context:
        value = context["stderr"]
        if not isinstance(value, str):
            raise _invalid_evidence("stderr must be a string")
        stderr = value
    elif "stderr_file" in context:
        stderr = _read_evidence_file(context["stderr_file"])
    if stderr is not None:
        _reject_environment_dump(stderr)
        redacted_stderr = _redact(stderr)
        if len(redacted_stderr.encode("utf-8")) > 4096:
            raise _invalid_evidence("stderr exceeds 4096 UTF-8 bytes")
        sanitized["stderr"] = redacted_stderr
    return sanitized


def _read_evidence_file(value: Any) -> str:
    if not isinstance(value, (str, os.PathLike)):
        raise _invalid_evidence("stderr_file must be a path")
    try:
        path = Path(value)
        expected = os.stat(path, follow_symlinks=False)
        if (
            not stat.S_ISREG(expected.st_mode)
            or expected.st_size > _EVIDENCE_FILE_LIMIT
        ):
            raise _invalid_evidence(
                "stderr_file must be a regular file no larger than 1 MiB"
            )
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
        with os.fdopen(descriptor, "rb") as evidence_file:
            metadata = os.fstat(evidence_file.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_size > _EVIDENCE_FILE_LIMIT
                or (metadata.st_dev, metadata.st_ino)
                != (expected.st_dev, expected.st_ino)
            ):
                raise _invalid_evidence(
                    "stderr_file must be a regular file no larger than 1 MiB"
                )
            data = evidence_file.read(_EVIDENCE_FILE_LIMIT + 1)
    except PapercutsError:
        raise
    except (OSError, TypeError) as error:
        raise _invalid_evidence("stderr_file could not be read safely") from error
    if len(data) > _EVIDENCE_FILE_LIMIT:
        raise _invalid_evidence(
            "stderr_file must be a regular file no larger than 1 MiB"
        )
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _invalid_evidence("stderr_file must contain UTF-8 text") from error


def _redact(value: str) -> str:
    redacted = _ASSIGNMENT_SECRET.sub(r"\1[REDACTED]", value)
    redacted = _BEARER_SECRET.sub("Bearer [REDACTED]", redacted)
    redacted = _URL_CREDENTIALS.sub(r"\1[REDACTED]@", redacted)
    redacted = _GITHUB_SECRET.sub("[REDACTED]", redacted)
    redacted = _OPENAI_SECRET.sub("[REDACTED]", redacted)
    redacted = _URL.sub("[REDACTED_URL]", redacted)
    redacted = _SCP_REMOTE.sub("[REDACTED_URL]", redacted)
    redacted = _WINDOWS_ABSOLUTE_PATH.sub("[REDACTED_PATH]", redacted)
    return _POSIX_ABSOLUTE_PATH.sub("[REDACTED_PATH]", redacted)


def _reject_environment_dump(value: str) -> None:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if len(lines) >= 2 and all(_ENVIRONMENT_LINE.fullmatch(line) for line in lines):
        raise _invalid_evidence("raw environment evidence is not allowed")

    if _ENVIRONMENT_OBJECT.match(value.lstrip()):
        raise _invalid_evidence("raw environment evidence is not allowed")

    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return
    if not isinstance(parsed, dict) or len(parsed) < 2:
        return
    keys = [key for key in parsed if isinstance(key, str)]
    if len(keys) != len(parsed) or not all(
        _ENVIRONMENT_NAME.fullmatch(key) for key in keys
    ):
        return
    common_names = sum(
        key.casefold() in _COMMON_ENVIRONMENT_NAMES for key in keys
    )
    uppercase_names = sum(key.upper() == key for key in keys)
    if common_names >= 2 or uppercase_names >= 3:
        raise _invalid_evidence("raw environment evidence is not allowed")


def _invalid_evidence(message: str) -> PapercutsError:
    return PapercutsError("invalid_input", message, exit_status=65)


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
