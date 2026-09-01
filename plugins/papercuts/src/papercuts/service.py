from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Literal, Mapping, Sequence

from papercuts.models import PapercutsError, Severity, Status, StorageContext
from papercuts.store import JournalStore, fold_events

_SEVERITIES = {"minor", "major", "blocker"}
_SEVERITY_ORDER = {"blocker": 0, "major": 1, "minor": 2}


class PapercutsService:
    def __init__(
        self,
        storage: StorageContext,
        *,
        agent: str = "codex",
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.storage = storage
        self.store = JournalStore(storage.journal_path)
        self.agent = agent
        self.now = now or (lambda: datetime.now(timezone.utc))

    def lodge(
        self,
        text: str,
        *,
        severity: Severity = "minor",
        tags: Sequence[str] = (),
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a complaint or append an encounter for an exact duplicate."""
        normalized_text = _normalize_text(text)
        normalized_tags = _normalize_tags(tags)
        _validate_severity(severity)
        complaint_id = _complaint_id(
            self.storage.project.id, normalized_text, normalized_tags
        )

        with self.store.mutation() as events:
            records = fold_events(events)
            existing = records.get(complaint_id)
            new_events: list[dict[str, Any]] = []
            if existing is None:
                new_events.append(
                    self._event(
                        "complaint",
                        id=complaint_id,
                        text=normalized_text,
                        severity=severity,
                        tags=normalized_tags,
                        context=dict(context or {}),
                    )
                )
            else:
                self._verify_identity(
                    existing, normalized_text=normalized_text, tags=normalized_tags
                )
                if existing["status"] == "resolved":
                    new_events.append(self._event("reopened", complaint_id=complaint_id))
                new_events.append(
                    self._event(
                        "encounter",
                        complaint_id=complaint_id,
                        note=None,
                        context=dict(context or {}),
                    )
                )
            self.store.append_events_locked(new_events)
            record = fold_events([*events, *new_events])[complaint_id]
        return {"changed": True, "record": record}

    def list(
        self,
        *,
        status: Status | Literal["all"] = "open",
        query: str | None = None,
        tags: Sequence[str] = (),
        severity: Severity | None = None,
        min_encounters: int | None = None,
        recent_days: int | None = None,
        all_projects: bool = False,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Return folded complaints using the fixed v1 ordering."""
        if status not in {"open", "resolved", "all"}:
            raise _invalid("status must be open, resolved, or all")
        if severity is not None:
            _validate_severity(severity)
        if min_encounters is not None and min_encounters < 0:
            raise _invalid("min_encounters must be non-negative")
        if recent_days is not None and recent_days < 0:
            raise _invalid("recent_days must be non-negative")
        if limit < 0:
            raise _invalid("limit must be non-negative")

        records = list(fold_events(self.store.read_events()).values())
        records = self._visible(records, all_projects=all_projects)
        normalized_tags = set(_normalize_tags(tags))
        normalized_query = _normalize_text(query).casefold() if query else None
        recent_cutoff = (
            self.now() - timedelta(days=recent_days)
            if recent_days is not None
            else None
        )
        filtered = [
            record
            for record in records
            if (status == "all" or record["status"] == status)
            and (severity is None or record["severity"] == severity)
            and (
                min_encounters is None
                or record["encounter_count"] >= min_encounters
            )
            and (not normalized_tags or normalized_tags.issubset(record["tags"]))
            and (
                normalized_query is None
                or normalized_query in record["text"].casefold()
            )
            and (
                recent_cutoff is None
                or _parse_timestamp(record["last_encounter_at"]) >= recent_cutoff
            )
        ]
        filtered.sort(
            key=lambda record: (
                _SEVERITY_ORDER[record["severity"]],
                -record["encounter_count"],
                -_parse_timestamp(record["last_encounter_at"]).timestamp(),
                record["id"],
            )
        )
        return filtered[:limit]

    def get(
        self, complaint_id: str, *, all_projects: bool = False
    ) -> dict[str, Any]:
        """Resolve a full or unique prefix ID and return one folded complaint."""
        records = list(fold_events(self.store.read_events()).values())
        return self._resolve_id(records, complaint_id, all_projects=all_projects)

    def vote(
        self,
        complaint_id: str,
        *,
        note: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append one encounter, reopening first when required."""
        with self.store.mutation() as events:
            records = list(fold_events(events).values())
            record = self._resolve_id(records, complaint_id, all_projects=False)
            new_events: list[dict[str, Any]] = []
            if record["status"] == "resolved":
                new_events.append(
                    self._event("reopened", complaint_id=record["id"], note=None)
                )
            new_events.append(
                self._event(
                    "encounter",
                    complaint_id=record["id"],
                    note=note,
                    context=dict(context or {}),
                )
            )
            self.store.append_events_locked(new_events)
            updated = fold_events([*events, *new_events])[record["id"]]
        return {"changed": True, "record": updated}

    def resolve(
        self, complaint_id: str, *, note: str | None = None
    ) -> dict[str, Any]:
        """Append resolved unless already resolved."""
        return self._change_status(complaint_id, "resolved", note)

    def reopen(
        self, complaint_id: str, *, note: str | None = None
    ) -> dict[str, Any]:
        """Append reopened unless already open."""
        return self._change_status(complaint_id, "reopened", note)

    def inspect_storage(self) -> dict[str, Any]:
        """Return scope, path, project, byte count, event count, and health."""
        events = self.store.read_events()
        try:
            journal_bytes = self.storage.journal_path.read_bytes()
        except FileNotFoundError:
            journal_bytes = b""
        except OSError as error:
            raise PapercutsError(
                "io_failure",
                f"Could not inspect journal at {self.storage.journal_path}: {error}",
                exit_status=74,
                retryable=True,
            ) from error
        return {
            "scope": self.storage.scope,
            "path": str(self.storage.journal_path),
            "project": self.storage.project.to_dict(),
            "byte_count": len(journal_bytes),
            "event_count": len(events),
            "healthy": not journal_bytes or journal_bytes.endswith(b"\n"),
        }

    def _change_status(
        self, complaint_id: str, kind: Literal["resolved", "reopened"], note: str | None
    ) -> dict[str, Any]:
        with self.store.mutation() as events:
            records = list(fold_events(events).values())
            record = self._resolve_id(records, complaint_id, all_projects=False)
            target_status = "resolved" if kind == "resolved" else "open"
            if record["status"] == target_status:
                return {"changed": False, "record": record}
            event = self._event(kind, complaint_id=record["id"], note=note)
            self.store.append_events_locked([event])
            updated = fold_events([*events, event])[record["id"]]
        return {"changed": True, "record": updated}

    def _event(self, kind: str, **fields: Any) -> dict[str, Any]:
        return {
            "contract": 1,
            "kind": kind,
            **fields,
            "ts": _format_timestamp(self.now()),
            "agent": self.agent,
            "project": self.storage.project.to_dict(),
        }

    def _visible(
        self, records: Sequence[dict[str, Any]], *, all_projects: bool
    ) -> list[dict[str, Any]]:
        if self.storage.scope != "user" or all_projects:
            return list(records)
        return [
            record
            for record in records
            if record["project"]["id"] == self.storage.project.id
        ]

    def _resolve_id(
        self,
        records: Sequence[dict[str, Any]],
        complaint_id: str,
        *,
        all_projects: bool,
    ) -> dict[str, Any]:
        visible = self._visible(records, all_projects=all_projects)
        matches = [record for record in visible if record["id"].startswith(complaint_id)]
        if not matches:
            raise PapercutsError(
                "not_found",
                f"Complaint not found: {complaint_id}",
                exit_status=66,
            )
        if len(matches) > 1:
            raise PapercutsError(
                "ambiguous_id",
                f"Complaint ID prefix is ambiguous: {complaint_id}",
                exit_status=66,
            )
        return matches[0]

    def _verify_identity(
        self,
        record: Mapping[str, Any],
        *,
        normalized_text: str,
        tags: Sequence[str],
    ) -> None:
        if (
            record["project"]["id"] != self.storage.project.id
            or record["text"] != normalized_text
            or record["tags"] != list(tags)
        ):
            raise PapercutsError(
                "internal_failure",
                "Complaint ID collision detected; no event was appended.",
                exit_status=70,
            )


def _normalize_text(text: str | None) -> str:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        raise _invalid("complaint text must not be empty")
    return normalized


def _normalize_tags(tags: Sequence[str]) -> list[str]:
    normalized = sorted({tag.strip().lower() for tag in tags if tag.strip()})
    if len(normalized) > 10:
        raise _invalid("at most ten tags are allowed")
    return normalized


def _complaint_id(project_id: str, text: str, tags: Sequence[str]) -> str:
    identity = json.dumps(
        {"contract": 1, "project_id": project_id, "text": text, "tags": list(tags)},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"pc_{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16]}"


def _validate_severity(severity: str) -> None:
    if severity not in _SEVERITIES:
        raise _invalid("severity must be minor, major, or blocker")


def _format_timestamp(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise _invalid("clock must return a timezone-aware datetime")
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PapercutsError(
            "malformed_journal",
            f"Invalid journal timestamp: {value}",
            exit_status=65,
        ) from error
    if parsed.tzinfo is None:
        raise PapercutsError(
            "malformed_journal",
            f"Journal timestamp lacks a timezone: {value}",
            exit_status=65,
        )
    return parsed.astimezone(timezone.utc)


def _invalid(message: str) -> PapercutsError:
    return PapercutsError("invalid_input", message, exit_status=64)
