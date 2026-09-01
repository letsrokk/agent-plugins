from __future__ import annotations

import hashlib
import json
import os
import random
import socket
import stat
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

from papercuts.models import PapercutsError, filesystem_error as _io_error

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
        records = _serialize_events(events, self.path)
        try:
            descriptor = _open_regular_file(
                self.path,
                os.O_WRONLY | os.O_APPEND,
                create=True,
            )
            with os.fdopen(descriptor, "ab") as journal:
                journal.write(records)
                journal.flush()
                os.fsync(journal.fileno())
        except OSError as error:
            raise _io_error("append journal", self.path, error) from error

    def digest(self) -> str:
        """Return SHA-256 of current journal bytes, with empty bytes for a missing file."""
        return hashlib.sha256(self._read_bytes()).hexdigest()

    def snapshot(self) -> tuple[list[dict[str, Any]], str]:
        """Read events and their journal digest from one byte snapshot."""
        data = self._read_bytes()
        events, _ = self._parse_events(data)
        return events, hashlib.sha256(data).hexdigest()

    def doctor(self, *, repair_tail: bool = False) -> dict[str, Any]:
        """Report health and optionally truncate only an incomplete final record."""
        if not repair_tail:
            data = self._read_bytes()
            events, incomplete_tail = self._parse_events(data)
            _fold_events(events, self.path)
            return _health(
                data=data,
                events=events,
                incomplete_tail=incomplete_tail,
                repaired=False,
            )

        self._reject_symlinks()
        try:
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as error:
            raise _io_error("create journal directory", self.path.parent, error) from error
        token = self._acquire_lock()
        try:
            data = self._read_bytes()
            events, incomplete_tail = self._parse_events(data)
            _fold_events(events, self.path)
            repaired = False
            if incomplete_tail:
                complete_length = data.rfind(b"\n") + 1
                try:
                    descriptor = _open_regular_file(
                        self.path,
                        os.O_WRONLY,
                    )
                    try:
                        os.ftruncate(descriptor, complete_length)
                        os.fsync(descriptor)
                    finally:
                        os.close(descriptor)
                except OSError as error:
                    raise _io_error("repair journal tail", self.path, error) from error
                data = data[:complete_length]
                repaired = True
            return _health(
                data=data,
                events=events,
                incomplete_tail=False,
                repaired=repaired,
            )
        finally:
            self._release_lock(token)

    def replace_locked(
        self,
        surviving_events: Sequence[dict[str, Any]],
        *,
        backup_dir: Path,
        timestamp: datetime,
    ) -> Path:
        """Write backup and fsynced temporary journal, then atomically replace it."""
        if timestamp.tzinfo is None:
            raise PapercutsError(
                "invalid_input",
                "backup timestamp must be timezone-aware",
                exit_status=65,
            )
        self._reject_symlinks()
        _reject_path_symlinks(backup_dir)
        replacement = _serialize_events(surviving_events, self.path)
        original = self._read_bytes()
        try:
            backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as error:
            raise _io_error("create backup directory", backup_dir, error) from error
        _reject_path_symlinks(backup_dir)

        suffix = timestamp.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup_path = backup_dir / f"papercuts-{suffix}.jsonl"
        try:
            descriptor = _open_regular_file(
                backup_path,
                os.O_WRONLY,
                create=True,
                exclusive=True,
            )
            with os.fdopen(descriptor, "wb") as backup:
                backup.write(original)
                backup.flush()
                os.fsync(backup.fileno())
            _fsync_directory(backup_dir)
        except OSError as error:
            raise _io_error("write journal backup", backup_path, error) from error

        temporary_path: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".papercuts-", suffix=".tmp", dir=self.path.parent
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as temporary:
                temporary.write(replacement)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
            _fsync_directory(self.path.parent)
        except OSError as error:
            raise _io_error("replace journal", self.path, error) from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except OSError:
                    pass
        return backup_path

    def _read_events_and_tail(self) -> tuple[list[dict[str, Any]], bool]:
        return self._parse_events(self._read_bytes())

    def _read_bytes(self) -> bytes:
        try:
            descriptor = _open_regular_file(
                self.path,
                os.O_RDONLY,
                missing_ok=True,
            )
            if descriptor is None:
                return b""
            with os.fdopen(descriptor, "rb") as journal:
                return journal.read()
        except FileNotFoundError:
            return b""
        except PapercutsError:
            raise
        except OSError as error:
            raise _io_error("read journal", self.path, error) from error

    def _parse_events(self, data: bytes) -> tuple[list[dict[str, Any]], bool]:
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
            lock_descriptor = self._open_lock_directory()
            if lock_descriptor is None:
                continue
            try:
                descriptor = os.open(
                    "owner.json",
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=lock_descriptor,
                )
                with os.fdopen(descriptor, "w", encoding="utf-8") as metadata_file:
                    metadata_file.write(
                        json.dumps(metadata, separators=(",", ":"), sort_keys=True)
                        + "\n"
                    )
            except OSError as error:
                self._remove_lock_directory(lock_descriptor)
                raise _io_error("write journal lock", self.lock_path, error) from error
            finally:
                os.close(lock_descriptor)
            return token

    def _recover_stale_lock(self) -> None:
        lock_descriptor = self._open_lock_directory()
        if lock_descriptor is None:
            return
        try:
            metadata = self._read_lock_metadata(lock_descriptor)
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
            self._remove_lock_if_owned(token, lock_descriptor)
        finally:
            os.close(lock_descriptor)

    def _release_lock(self, token: str) -> None:
        self._remove_lock_if_owned(token)

    def _remove_lock_if_owned(
        self, token: str, lock_descriptor: int | None = None
    ) -> None:
        opened_here = lock_descriptor is None
        if lock_descriptor is None:
            lock_descriptor = self._open_lock_directory()
        if lock_descriptor is None:
            return
        try:
            metadata = self._read_lock_metadata(lock_descriptor)
            if metadata is None or metadata.get("token") != token:
                return
            try:
                os.unlink("owner.json", dir_fd=lock_descriptor)
            except FileNotFoundError:
                return
            except OSError:
                return
            self._remove_lock_directory(lock_descriptor)
        finally:
            if opened_here:
                os.close(lock_descriptor)

    def _read_lock_metadata(self, lock_descriptor: int) -> dict[str, Any] | None:
        try:
            descriptor = os.open(
                "owner.json",
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=lock_descriptor,
            )
            with os.fdopen(descriptor, encoding="utf-8") as metadata_file:
                if not stat.S_ISREG(os.fstat(metadata_file.fileno()).st_mode):
                    return None
                metadata = json.load(metadata_file)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return metadata if isinstance(metadata, dict) else None

    def _open_lock_directory(self) -> int | None:
        try:
            expected = os.stat(self.lock_path, follow_symlinks=False)
        except FileNotFoundError:
            return None
        except OSError as error:
            raise _io_error("inspect journal lock", self.lock_path, error) from error
        if not stat.S_ISDIR(expected.st_mode):
            raise _unsafe_lock(self.lock_path)

        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self.lock_path, flags)
        except FileNotFoundError:
            return None
        except OSError as error:
            try:
                current = os.stat(self.lock_path, follow_symlinks=False)
            except FileNotFoundError:
                return None
            except OSError as stat_error:
                raise _io_error(
                    "inspect journal lock", self.lock_path, stat_error
                ) from stat_error
            if not stat.S_ISDIR(current.st_mode):
                raise _unsafe_lock(self.lock_path) from error
            raise _io_error("open journal lock", self.lock_path, error) from error

        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino):
            os.close(descriptor)
            return None
        return descriptor

    def _remove_lock_directory(self, lock_descriptor: int) -> None:
        opened = os.fstat(lock_descriptor)
        try:
            current = os.stat(self.lock_path, follow_symlinks=False)
        except OSError:
            return
        if (
            not stat.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            return
        try:
            self.lock_path.rmdir()
        except OSError:
            return

    def _reject_symlinks(self) -> None:
        _reject_path_symlinks(self.path)


def _health(
    *,
    data: bytes,
    events: Sequence[dict[str, Any]],
    incomplete_tail: bool,
    repaired: bool,
) -> dict[str, Any]:
    return {
        "healthy": not incomplete_tail,
        "repaired": repaired,
        "incomplete_tail": incomplete_tail,
        "byte_count": len(data),
        "event_count": len(events),
    }


def _serialize_events(events: Sequence[dict[str, Any]], path: Path) -> bytes:
    serialized: list[bytes] = []
    for index, event in enumerate(events, start=1):
        _validate_event(event, path, index)
        try:
            record = json.dumps(
                event,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        except (TypeError, ValueError) as error:
            raise _malformed(path, index, "event is not JSON serializable") from error
        serialized.append((record + "\n").encode("utf-8"))
    return b"".join(serialized)


def _open_regular_file(
    path: Path,
    flags: int,
    *,
    create: bool = False,
    exclusive: bool = False,
    missing_ok: bool = False,
) -> int | None:
    """Open one regular file without following its final path component."""
    for attempt in range(3):
        _reject_path_symlinks(path)
        try:
            expected = os.stat(path, follow_symlinks=False)
        except FileNotFoundError:
            expected = None
        if expected is not None and not stat.S_ISREG(expected.st_mode):
            raise _unsafe_storage_path(path)
        if expected is None and not create:
            if missing_ok:
                return None
            raise FileNotFoundError(path)

        open_flags = flags | getattr(os, "O_NOFOLLOW", 0)
        if create and (exclusive or expected is None):
            open_flags |= os.O_CREAT | os.O_EXCL
        try:
            descriptor = os.open(path, open_flags, 0o600)
        except FileExistsError:
            if create and not exclusive and expected is None and attempt < 2:
                continue
            raise
        except FileNotFoundError:
            if create and expected is not None and attempt < 2:
                continue
            if missing_ok:
                return None
            raise
        except OSError:
            _reject_path_symlinks(path)
            raise

        try:
            opened = os.fstat(descriptor)
            current = os.stat(path, follow_symlinks=False)
            expected_matches = expected is None or (
                expected.st_dev,
                expected.st_ino,
            ) == (opened.st_dev, opened.st_ino)
            if (
                not stat.S_ISREG(opened.st_mode)
                or not expected_matches
                or (current.st_dev, current.st_ino)
                != (opened.st_dev, opened.st_ino)
            ):
                raise _unsafe_storage_path(path)
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor
    raise _unsafe_storage_path(path)


def _reject_path_symlinks(path: Path) -> None:
    target = path.absolute()
    parts = target.parts
    if not parts:
        return
    current = Path(parts[0])
    for index, component in enumerate(parts[1:], start=1):
        current /= component
        try:
            metadata = os.stat(current, follow_symlinks=False)
        except FileNotFoundError:
            break
        except OSError as error:
            raise _io_error("inspect storage path", current, error) from error
        if not stat.S_ISLNK(metadata.st_mode):
            continue
        # macOS exposes immutable root-owned aliases such as /var and /tmp.
        # Canonicalize only that filesystem anchor, then reject every descendant link.
        if index == 1 and getattr(metadata, "st_uid", -1) == 0:
            current = Path(os.path.realpath(current))
            continue
        raise _unsafe_storage_path(current)


def _unsafe_storage_path(path: Path) -> PapercutsError:
    return PapercutsError(
        "invalid_input",
        f"Storage path traverses a symbolic link or non-regular file: {path}",
        exit_status=64,
    )


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def fold_events(events: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return _fold_events(events, Path("<events>"))


def _fold_events(
    events: Sequence[dict[str, Any]],
    path: Path,
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for index, event in enumerate(events, start=1):
        _validate_event(event, path, index)
        kind = event["kind"]
        if kind == "complaint":
            complaint_id = event["id"]
            if complaint_id in records:
                raise _malformed(path, index, "duplicate complaint ID")
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
            raise _malformed(path, index, "orphan event")
        if event["project"]["id"] != record["project"]["id"]:
            raise _malformed(path, index, "mismatched project ID")

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
        type(event.get("contract")) is not int
        or event["contract"] != 1
        or not isinstance(event.get("kind"), str)
        or event["kind"] not in _KINDS
        or not _non_empty_string(event.get("ts"))
        or not _non_empty_string(event.get("agent"))
        or not isinstance(project, dict)
        or not _non_empty_string(project.get("id"))
        or not _non_empty_string(project.get("name"))
    ):
        raise _malformed(path, line_number)

    kind = event["kind"]
    if kind == "complaint":
        valid = (
            _non_empty_string(event.get("id"))
            and _non_empty_string(event.get("text"))
            and isinstance(event.get("severity"), str)
            and event["severity"] in {"minor", "major", "blocker"}
            and isinstance(event.get("tags"), list)
            and len(event["tags"]) <= 10
            and all(_non_empty_string(tag) for tag in event["tags"])
            and isinstance(event.get("context"), dict)
        )
    elif kind == "encounter":
        valid = (
            _non_empty_string(event.get("complaint_id"))
            and isinstance(event.get("context"), dict)
            and _optional_note_is_valid(event)
        )
    else:
        valid = _non_empty_string(
            event.get("complaint_id")
        ) and _optional_note_is_valid(event)
    if not valid:
        raise _malformed(path, line_number)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _optional_note_is_valid(event: dict[str, Any]) -> bool:
    note = event.get("note")
    return note is None or _non_empty_string(note)


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


def _unsafe_lock(path: Path) -> PapercutsError:
    return PapercutsError(
        "invalid_input",
        f"Journal lock is not a real directory: {path}",
        exit_status=64,
    )
