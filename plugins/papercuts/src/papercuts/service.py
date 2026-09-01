from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

from papercuts.models import (
    PapercutsError,
    PrunePolicy,
    Severity,
    Status,
    StorageContext,
    filesystem_error,
    sanitize_context,
    sanitize_user_string,
)
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
                        context=sanitize_context(context),
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
                        context=sanitize_context(context),
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
        sanitized_note = _sanitize_note(note)
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
                    note=sanitized_note,
                    context=sanitize_context(context),
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

    def doctor(self, *, repair_tail: bool = False) -> dict[str, Any]:
        return self.store.doctor(repair_tail=repair_tail)

    def preview_prune(self, policy: PrunePolicy) -> dict[str, Any]:
        """Select whole complaint histories and hash journal bytes, policy, and IDs."""
        normalized_policy = _validate_prune_policy(policy)
        moment = _normalized_moment(self.now())
        events, journal_digest = self.store.snapshot()
        return self._prune_preview(
            events,
            journal_digest=journal_digest,
            policy=normalized_policy,
            moment=moment,
        )

    def apply_prune(self, policy: PrunePolicy, plan_id: str) -> dict[str, Any]:
        """Recompute preview under lock, reject stale plans, back up, and replace."""
        normalized_policy = _validate_prune_policy(policy)
        if not isinstance(plan_id, str) or not plan_id:
            raise _invalid("plan_id must not be empty")
        moment = _normalized_moment(self.now())
        with self.store.mutation() as events:
            preview = self._prune_preview(
                events,
                journal_digest=self.store.digest(),
                policy=normalized_policy,
                moment=moment,
            )
            if preview["plan_id"] != plan_id:
                raise PapercutsError(
                    "stale_prune_plan",
                    "The prune plan no longer matches the journal and policy.",
                    exit_status=75,
                    retryable=True,
                    suggested_fix="Preview pruning again before applying it.",
                )

            candidate_ids = {item["id"] for item in preview["candidates"]}
            if not candidate_ids:
                return {
                    "changed": False,
                    "plan_id": plan_id,
                    "policy": normalized_policy,
                    "backup": None,
                    "removed_complaints": 0,
                    "removed_events": 0,
                    "reclaimed_bytes": 0,
                }

            surviving_events = [
                event
                for event in events
                if _event_complaint_id(event) not in candidate_ids
            ]
            try:
                before_bytes = self.storage.journal_path.stat().st_size
            except OSError as error:
                raise filesystem_error(
                    "inspect journal",
                    self.storage.journal_path,
                    error,
                ) from error
            backup_path = self.store.replace_locked(
                surviving_events,
                backup_dir=self._backup_dir(),
                timestamp=moment,
            )
            try:
                after_bytes = self.storage.journal_path.stat().st_size
            except OSError as error:
                raise filesystem_error(
                    "inspect journal",
                    self.storage.journal_path,
                    error,
                ) from error
            return {
                "changed": True,
                "plan_id": plan_id,
                "policy": normalized_policy,
                "backup": str(backup_path),
                "removed_complaints": len(candidate_ids),
                "removed_events": len(events) - len(surviving_events),
                "reclaimed_bytes": before_bytes - after_bytes,
            }

    def inspect_storage(self) -> dict[str, Any]:
        """Return scope, path, project, byte count, event count, and health."""
        health = self.store.doctor()
        return {
            "scope": self.storage.scope,
            "path": str(self.storage.journal_path),
            "project": self.storage.project.to_dict(),
            "byte_count": health["byte_count"],
            "event_count": health["event_count"],
            "healthy": health["healthy"],
        }

    def _prune_preview(
        self,
        events: Sequence[dict[str, Any]],
        *,
        journal_digest: str,
        policy: dict[str, int | str],
        moment: datetime,
    ) -> dict[str, Any]:
        records = fold_events(events)
        selected: list[dict[str, Any]] = []
        for record in records.values():
            if (
                policy["projects"] == "current"
                and record["project"]["id"] != self.storage.project.id
            ):
                continue
            reason = _prune_reason(record, policy=policy, moment=moment)
            if reason is None:
                continue
            history = [
                event
                for event in events
                if _event_complaint_id(event) == record["id"]
            ]
            selected.append(
                {
                    "id": record["id"],
                    "project": record["project"],
                    "status": record["status"],
                    "reason": reason,
                    "event_count": len(history),
                    "estimated_bytes": sum(_event_size(event) for event in history),
                }
            )
        selected.sort(key=lambda item: item["id"])
        candidate_ids = [item["id"] for item in selected]
        plan_id = _prune_plan_id(
            journal_digest=journal_digest,
            policy=policy,
            candidate_ids=candidate_ids,
        )
        return {
            "plan_id": plan_id,
            "policy": policy,
            "candidates": selected,
            "estimated": {
                "complaints": len(selected),
                "events": sum(item["event_count"] for item in selected),
                "bytes": sum(item["estimated_bytes"] for item in selected),
            },
        }

    def _backup_dir(self) -> Path:
        if self.storage.scope == "project":
            return self.storage.project_root / ".codex/papercuts.backups"
        return self.storage.journal_path.parent / "papercuts.backups"

    def _change_status(
        self, complaint_id: str, kind: Literal["resolved", "reopened"], note: str | None
    ) -> dict[str, Any]:
        sanitized_note = _sanitize_note(note)
        with self.store.mutation() as events:
            records = list(fold_events(events).values())
            record = self._resolve_id(records, complaint_id, all_projects=False)
            target_status = "resolved" if kind == "resolved" else "open"
            if record["status"] == target_status:
                return {"changed": False, "record": record}
            event = self._event(kind, complaint_id=record["id"], note=sanitized_note)
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
    if not isinstance(text, str):
        raise _invalid("complaint text must be a string")
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise _invalid("complaint text must not be empty")
    return sanitize_user_string(normalized, field="complaint text")


def _sanitize_note(note: str | None) -> str | None:
    if note is None:
        return None
    return str(sanitize_context({"note": note})["note"])


def _normalize_tags(tags: Sequence[str]) -> list[str]:
    if isinstance(tags, (str, bytes)):
        raise _invalid("tags must be a sequence of strings")
    normalized_tags: set[str] = set()
    for tag in tags:
        sanitized = sanitize_user_string(tag, field="tag").strip().lower()
        if sanitized:
            normalized_tags.add(sanitized)
    normalized = sorted(normalized_tags)
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


def _validate_prune_policy(policy: PrunePolicy) -> dict[str, int | str]:
    if not isinstance(policy, PrunePolicy):
        raise _invalid("policy must be a PrunePolicy")
    thresholds = {
        "resolved_older_than_days": policy.resolved_older_than_days,
        "open_max_encounters": policy.open_max_encounters,
        "open_inactive_for_days": policy.open_inactive_for_days,
    }
    if any(type(value) is not int or value < 0 for value in thresholds.values()):
        raise _invalid("prune thresholds and encounter counts must be non-negative")
    if policy.projects not in {"current", "all"}:
        raise _invalid("projects must be current or all")
    return policy.to_dict()


def _prune_reason(
    record: Mapping[str, Any],
    *,
    policy: Mapping[str, int | str],
    moment: datetime,
) -> str | None:
    if record["status"] == "resolved":
        resolved_event = next(
            (
                event
                for event in reversed(record["status_history"])
                if event["kind"] == "resolved"
            ),
            None,
        )
        if resolved_event is None:
            raise PapercutsError(
                "malformed_journal",
                f"Resolved complaint lacks a resolution event: {record['id']}",
                exit_status=65,
            )
        cutoff = moment - timedelta(
            days=int(policy["resolved_older_than_days"])
        )
        if _parse_timestamp(resolved_event["ts"]) < cutoff:
            return f"resolved before {_format_timestamp(cutoff)}"
        return None

    cutoff = moment - timedelta(days=int(policy["open_inactive_for_days"]))
    if (
        record["encounter_count"] <= int(policy["open_max_encounters"])
        and _parse_timestamp(record["last_encounter_at"]) < cutoff
    ):
        return (
            f"open with at most {policy['open_max_encounters']} encounters and inactive "
            f"since before {_format_timestamp(cutoff)}"
        )
    return None


def _prune_plan_id(
    *,
    journal_digest: str,
    policy: Mapping[str, int | str],
    candidate_ids: Sequence[str],
) -> str:
    material = json.dumps(
        {
            "journal_digest": journal_digest,
            "policy": dict(policy),
            "candidate_ids": list(candidate_ids),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"pp_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _event_complaint_id(event: Mapping[str, Any]) -> str:
    if event["kind"] == "complaint":
        return str(event["id"])
    return str(event["complaint_id"])


def _event_size(event: Mapping[str, Any]) -> int:
    return len(
        (
            json.dumps(
                event,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    )


def _normalized_moment(moment: datetime) -> datetime:
    if not isinstance(moment, datetime) or moment.tzinfo is None:
        raise _invalid("clock must return a timezone-aware datetime")
    return moment.astimezone(timezone.utc)


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
