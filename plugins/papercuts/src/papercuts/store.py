from __future__ import annotations

import hashlib
import json
import os
import random
import socket
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

from papercuts.models import PapercutsError

_KINDS = {"complaint", "encounter", "resolved", "reopened"}
_LOCK_TIMEOUT_SECONDS = 5.0
_STALE_LOCK_SECONDS = 300.0


class JournalStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock_path = Path(f"{path}.lock")

    def read_events(self) -> list[dict[str, Any]]:
        """Parse complete UTF-8 JSON object lines and reject malformed interiors."""
        events, _ = self._read_events_and_tail()
        return events

    @contextmanager
    def mutation(self) -> Iterator[list[dict[str, Any]]]:
        """Acquire the adjacent lock directory, read current events, and release safely."""
        self._reject_symlinks()
        try:
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as error:
            raise _io_error("create journal directory", self.path.parent, error) from error

        token = self._acquire_lock()
        try:
            events, incomplete_tail = self._read_events_and_tail()
            if incomplete_tail:
                raise PapercutsError(
                    "malformed_journal",
                    f"Journal has an incomplete final record: {self.path}",
                    exit_status=65,
                    suggested_fix="Run doctor --repair-tail before mutating the journal.",
                )
            yield events
        finally:
            self._release_lock(token)

    def append_events_locked(self, events: Sequence[dict[str, Any]]) -> None:
        """Append complete compact JSON records, flush, and fsync before return."""
        if not events:
            return
        records = b"".join(
            (
                json.dumps(
                    event,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
            for event in events
        )
        try:
            descriptor = os.open(
                self.path,
                os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                0o600,
            )
            with os.fdopen(descriptor, "ab") as journal:
                journal.write(records)
                journal.flush()
                os.fsync(journal.fileno())
        except (OSError, TypeError, ValueError) as error:
            raise _io_error("append journal", self.path, error) from error

    def digest(self) -> str:
        """Return SHA-256 of current journal bytes, with empty bytes for a missing file."""
        try:
            data = self.path.read_bytes() if self.path.exists() else b""
        except OSError as error:
            raise _io_error("read journal", self.path, error) from error
        return hashlib.sha256(data).hexdigest()

    def _read_events_and_tail(self) -> tuple[list[dict[str, Any]], bool]:
        try:
            data = self.path.read_bytes()
        except FileNotFoundError:
            return [], False
        except OSError as error:
            raise _io_error("read journal", self.path, error) from error

        lines = data.splitlines(keepends=True)
        incomplete_tail = bool(lines and not lines[-1].endswith(b"\n"))
        complete_lines = lines[:-1] if incomplete_tail else lines
        events: list[dict[str, Any]] = []
        for line_number, raw_line in enumerate(complete_lines, start=1):
            try:
                line = raw_line.removesuffix(b"\n").removesuffix(b"\r").decode(
                    "utf-8"
                )
                event = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise _malformed(self.path, line_number) from error
            _validate_event(event, self.path, line_number)
            events.append(event)
        return events, incomplete_tail

    def _acquire_lock(self) -> str:
        token = uuid.uuid4().hex
        deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
        while True:
            try:
                self.lock_path.mkdir()
            except FileExistsError:
                self._recover_stale_lock()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise PapercutsError(
                        "lock_timeout",
                        f"Timed out waiting for journal lock: {self.lock_path}",
                        exit_status=75,
                        retryable=True,
                    )
                time.sleep(min(remaining, random.uniform(0.025, 0.1)))
                continue
            except OSError as error:
                raise _io_error("create journal lock", self.lock_path, error) from error

            metadata = {
                "token": token,
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "created_at": _utc_now(),
            }
            try:
                descriptor = os.open(
                    self._metadata_path(),
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                )
                with os.fdopen(descriptor, "w", encoding="utf-8") as metadata_file:
                    metadata_file.write(
                        json.dumps(metadata, separators=(",", ":"), sort_keys=True)
                        + "\n"
                    )
            except OSError as error:
                try:
                    self.lock_path.rmdir()
                except OSError:
                    pass
                raise _io_error("write journal lock", self.lock_path, error) from error
            return token

    def _recover_stale_lock(self) -> None:
        metadata = self._read_lock_metadata()
        if metadata is None or metadata.get("host") != socket.gethostname():
            return
        try:
            created_at = datetime.fromisoformat(
                str(metadata["created_at"]).replace("Z", "+00:00")
            )
            age = datetime.now(timezone.utc) - created_at.astimezone(timezone.utc)
            pid = int(metadata["pid"])
            token = str(metadata["token"])
        except (KeyError, TypeError, ValueError):
            return
        if age.total_seconds() <= _STALE_LOCK_SECONDS or not _process_absent(pid):
            return
        self._remove_lock_if_owned(token)

    def _release_lock(self, token: str) -> None:
        self._remove_lock_if_owned(token)

    def _remove_lock_if_owned(self, token: str) -> None:
        metadata = self._read_lock_metadata()
        if metadata is None or metadata.get("token") != token:
            return
        try:
            self._metadata_path().unlink()
            self.lock_path.rmdir()
        except FileNotFoundError:
            return
        except OSError:
            return

    def _read_lock_metadata(self) -> dict[str, Any] | None:
        try:
            metadata = json.loads(self._metadata_path().read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return metadata if isinstance(metadata, dict) else None

    def _metadata_path(self) -> Path:
        return self.lock_path / "owner.json"

    def _reject_symlinks(self) -> None:
        target = self.path.absolute()
        candidates = [target]
        if target.parent != target:
            candidates.append(target.parent)
        while not os.path.lexists(candidates[-1]):
            parent = candidates[-1].parent
            if parent == candidates[-1]:
                break
            candidates.append(parent)
        for current in reversed(candidates):
            try:
                if current.is_symlink():
                    raise PapercutsError(
                        "invalid_input",
                        f"Journal path traverses a symbolic link: {current}",
                        exit_status=64,
                    )
            except OSError as error:
                raise _io_error("inspect journal path", current, error) from error


def fold_events(events: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for index, event in enumerate(events, start=1):
        _validate_event(event, Path("<events>"), index)
        kind = event["kind"]
        if kind == "complaint":
            complaint_id = event["id"]
            if complaint_id in records:
                raise _malformed(Path("<events>"), index, "duplicate complaint ID")
            records[complaint_id] = {
                **event,
                "status": "open",
                "encounter_count": 1,
                "vote_count": 0,
                "last_encounter_at": event["ts"],
                "resolution_note": None,
                "recent_encounters": [],
                "status_history": [],
            }
            continue

        complaint_id = event["complaint_id"]
        record = records.get(complaint_id)
        if record is None:
            raise _malformed(Path("<events>"), index, "orphan event")
        if event["project"]["id"] != record["project"]["id"]:
            raise _malformed(Path("<events>"), index, "mismatched project ID")

        if kind == "encounter":
            record["encounter_count"] += 1
            record["vote_count"] += 1
            record["last_encounter_at"] = event["ts"]
            record["recent_encounters"] = [
                *record["recent_encounters"],
                event,
            ][-10:]
        else:
            record["status"] = "resolved" if kind == "resolved" else "open"
            if kind == "resolved":
                record["resolution_note"] = event.get("note")
            record["status_history"].append(event)
    return records


def _validate_event(event: Any, path: Path, line_number: int) -> None:
    if not isinstance(event, dict):
        raise _malformed(path, line_number)
    project = event.get("project")
    if (
        event.get("contract") != 1
        or event.get("kind") not in _KINDS
        or not isinstance(event.get("ts"), str)
        or not event["ts"]
        or not isinstance(event.get("agent"), str)
        or not event["agent"]
        or not isinstance(project, dict)
        or not isinstance(project.get("id"), str)
        or not project["id"]
        or not isinstance(project.get("name"), str)
        or not project["name"]
    ):
        raise _malformed(path, line_number)

    kind = event["kind"]
    if kind == "complaint":
        valid = (
            isinstance(event.get("id"), str)
            and isinstance(event.get("text"), str)
            and event.get("severity") in {"minor", "major", "blocker"}
            and isinstance(event.get("tags"), list)
            and all(isinstance(tag, str) for tag in event["tags"])
            and isinstance(event.get("context"), dict)
        )
    else:
        valid = isinstance(event.get("complaint_id"), str)
    if not valid:
        raise _malformed(path, line_number)


def _process_absent(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except (PermissionError, OSError):
        return False
    return False


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _malformed(path: Path, line_number: int, detail: str | None = None) -> PapercutsError:
    suffix = f" ({detail})" if detail else ""
    return PapercutsError(
        "malformed_journal",
        f"Malformed journal event at {path}:{line_number}{suffix}",
        exit_status=65,
    )


def _io_error(action: str, path: Path, error: BaseException) -> PapercutsError:
    return PapercutsError(
        "io_failure",
        f"Could not {action} at {path}: {error}",
        exit_status=74,
        retryable=True,
    )
