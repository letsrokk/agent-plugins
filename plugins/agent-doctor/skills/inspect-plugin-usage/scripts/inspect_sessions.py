#!/usr/bin/env python3
"""Summarize skill invocations recorded in local Codex and Claude sessions."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


SKILL_PATH_PATTERN = re.compile(r"([A-Za-z0-9_./~:-]+/SKILL\.md)")
COMMAND_NAME_PATTERN = re.compile(r"<command-name>/?([^<]+)</command-name>")
FRONTMATTER_NAME_PATTERN = r"(?m)^name:\s*{name}\s*$"
ERROR_PATTERN = re.compile(
    r"permission denied|no such file|not found|access denied|\berror\b|\bfailed\b",
    re.IGNORECASE,
)
KNOWN_RECORD_TYPES = {
    "codex": {
        "compacted",
        "event_msg",
        "inter_agent_communication_metadata",
        "response_item",
        "session_meta",
        "token_usage_record",
        "turn_context",
        "world_state",
    },
    "claude": {
        "agent-name",
        "assistant",
        "attachment",
        "custom-title",
        "file-history-snapshot",
        "last-prompt",
        "permission-mode",
        "pr-link",
        "queue-operation",
        "system",
        "user",
    },
}


def analyze(
    *,
    target_kind: str,
    target_name: str,
    project: Path | None,
    days: int,
    now: datetime | None = None,
    codex_home: Path | None = None,
    claude_home: Path | None = None,
) -> dict[str, Any]:
    """Return aggregate invocation counts for an exact plugin or skill."""
    if target_kind not in {"plugin", "skill"}:
        raise ValueError("target_kind must be 'plugin' or 'skill'")
    if not target_name:
        raise ValueError("target_name must not be empty")
    if days <= 0:
        raise ValueError("days must be positive")

    end = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    start = end - timedelta(days=days)
    resolved_project = project.expanduser().resolve(strict=False) if project else None
    codex_root = codex_home or Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    claude_root = claude_home or Path("~/.claude").expanduser()

    warnings: Counter[tuple[str, str]] = Counter()
    sessions = []
    sessions.extend(
        _scan_codex(codex_root / "sessions", target_kind, target_name, start, end, warnings)
    )
    sessions.extend(
        _scan_claude(
            claude_root / "projects", target_kind, target_name, start, end, warnings
        )
    )

    scopes = {"all": _summarize(sessions)}
    if resolved_project is not None:
        project_sessions = [
            session
            for session in sessions
            if session["cwd"] is not None
            and _belongs_to_project(session["cwd"], resolved_project)
        ]
        scopes["project"] = _summarize(project_sessions)

    return {
        "target": {"kind": target_kind, "name": target_name},
        "window": {
            "days": days,
            "start": _format_timestamp(start),
            "end": _format_timestamp(end),
        },
        "project": str(resolved_project) if resolved_project else None,
        "scopes": scopes,
        "warnings": [
            {"client": client, "category": category, "count": count}
            for (client, category), count in sorted(warnings.items())
        ],
    }


def _scan_codex(
    root: Path,
    target_kind: str,
    target_name: str,
    start: datetime,
    end: datetime,
    warnings: Counter[tuple[str, str]],
) -> list[dict[str, Any]]:
    if not root.is_dir():
        warnings[("codex", "missing-session-root")] += 1
        return []

    sessions = []
    for path in sorted(root.rglob("*.jsonl")):
        records = _read_records(path, "codex", warnings)
        timed_records = [
            (record, _parse_timestamp(record.get("timestamp"))) for record in records
        ]
        in_window = any(
            timestamp is not None and start <= timestamp <= end
            for _, timestamp in timed_records
        )
        if not in_window:
            continue

        cwd = None
        outputs: dict[str, Any] = {}
        for record, _ in timed_records:
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue
            if record.get("type") == "session_meta" and cwd is None:
                cwd = _resolve_cwd(payload.get("cwd"))
            if (
                record.get("type") == "response_item"
                and payload.get("type")
                in {"custom_tool_call_output", "function_call_output"}
                and payload.get("call_id")
            ):
                outputs[str(payload["call_id"])] = payload.get("output")
        if cwd is None:
            warnings[("codex", "missing-session-cwd")] += 1

        invocations = []
        for record, timestamp in timed_records:
            if timestamp is None or not start <= timestamp <= end:
                continue
            payload = record.get("payload")
            if not isinstance(payload, dict) or record.get("type") != "response_item":
                continue
            if payload.get("type") not in {"custom_tool_call", "function_call"}:
                continue
            raw_input = payload.get("input", payload.get("arguments", ""))
            input_text = _flatten_text(raw_input)
            tool_name = payload.get("name")
            if not _has_initial_read_intent(input_text, tool_name):
                continue
            paths = sorted(set(SKILL_PATH_PATTERN.findall(input_text)))
            for skill_path in paths:
                identity = _identity_from_skill_path(skill_path)
                if identity is None or not _matches(identity, target_kind, target_name):
                    continue
                output = outputs.get(str(payload.get("call_id")))
                direct_read = _has_direct_read(input_text, skill_path, tool_name)
                definitive_failure = direct_read and (
                    len(paths) == 1 or skill_path in _flatten_text(output)
                )
                status, category = _classify_codex_output(
                    output, identity[1], definitive_failure=definitive_failure
                )
                if status == "incomplete" and not direct_read:
                    continue
                invocations.append({"status": status, "category": category})

        sessions.append({"client": "codex", "cwd": cwd, "invocations": invocations})
    return sessions


def _scan_claude(
    root: Path,
    target_kind: str,
    target_name: str,
    start: datetime,
    end: datetime,
    warnings: Counter[tuple[str, str]],
) -> list[dict[str, Any]]:
    if not root.is_dir():
        warnings[("claude", "missing-session-root")] += 1
        return []

    sessions = []
    for path in sorted(root.rglob("*.jsonl")):
        records = _read_records(path, "claude", warnings)
        timed_records = [
            (record, _parse_timestamp(record.get("timestamp"))) for record in records
        ]
        in_window = any(
            timestamp is not None and start <= timestamp <= end
            for _, timestamp in timed_records
        )
        if not in_window:
            continue

        cwd = next(
            (
                resolved
                for record, _ in timed_records
                if (resolved := _resolve_cwd(record.get("cwd"))) is not None
            ),
            None,
        )
        if cwd is None:
            warnings[("claude", "missing-session-cwd")] += 1
        results: dict[str, bool] = {}
        for record, _ in timed_records:
            for block in _content_blocks(record):
                if block.get("type") == "tool_result" and block.get("tool_use_id"):
                    results[str(block["tool_use_id"])] = bool(block.get("is_error"))

        invocations = []
        for record, timestamp in timed_records:
            if timestamp is None or not start <= timestamp <= end:
                continue
            for block in _content_blocks(record):
                if block.get("type") != "tool_use" or block.get("name") != "Skill":
                    continue
                tool_input = block.get("input")
                skill_name = tool_input.get("skill") if isinstance(tool_input, dict) else None
                if not isinstance(skill_name, str):
                    warnings[("claude", "unsupported-skill-record")] += 1
                    continue
                identity = _identity_from_qualified_skill(skill_name)
                if not _matches(identity, target_kind, target_name):
                    continue
                call_id = str(block.get("id", ""))
                if call_id not in results:
                    invocations.append({"status": "incomplete", "category": None})
                elif results[call_id]:
                    invocations.append(
                        {"status": "problem", "category": "skill-error"}
                    )
                else:
                    invocations.append({"status": "successful", "category": None})

            for command_name in COMMAND_NAME_PATTERN.findall(_message_text(record)):
                identity = _identity_from_qualified_skill(command_name.strip())
                if _matches(identity, target_kind, target_name):
                    invocations.append({"status": "successful", "category": None})

        sessions.append({"client": "claude", "cwd": cwd, "invocations": invocations})
    return sessions


def _read_records(
    path: Path, client: str, warnings: Counter[tuple[str, str]]
) -> list[dict[str, Any]]:
    records = []
    try:
        with path.open(encoding="utf-8", errors="replace") as source:
            for line in source:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    warnings[(client, "malformed-json")] += 1
                    continue
                if isinstance(record, dict):
                    if record.get("type") not in KNOWN_RECORD_TYPES[client]:
                        warnings[(client, "unknown-record")] += 1
                    records.append(record)
    except OSError:
        warnings[(client, "unreadable-session")] += 1
    return records


def _summarize(sessions: Iterable[dict[str, Any]]) -> dict[str, Any]:
    by_client = {"codex": _empty_counts(), "claude": _empty_counts()}
    categories: Counter[tuple[str, str]] = Counter()
    for session in sessions:
        counts = by_client[session["client"]]
        counts["scanned_sessions"] += 1
        if session["invocations"]:
            counts["matched_sessions"] += 1
        for invocation in session["invocations"]:
            counts["attempts"] += 1
            count_key = (
                "problems"
                if invocation["status"] == "problem"
                else invocation["status"]
            )
            counts[count_key] += 1
            if invocation["category"]:
                categories[(session["client"], invocation["category"])] += 1

    combined = {
        key: sum(client_counts[key] for client_counts in by_client.values())
        for key in _empty_counts()
    }
    return {
        "combined": combined,
        "clients": by_client,
        "problem_categories": [
            {"client": client, "category": category, "count": count}
            for (client, category), count in sorted(categories.items())
        ],
    }


def _empty_counts() -> dict[str, int]:
    return {
        "attempts": 0,
        "successful": 0,
        "problems": 0,
        "incomplete": 0,
        "scanned_sessions": 0,
        "matched_sessions": 0,
    }


def _identity_from_skill_path(path: str) -> tuple[str | None, str] | None:
    normalized = path.replace("\\", "/")
    patterns = (
        r"(?:^|/)plugins/cache/[^/]+/([^/]+)/[^/]+/skills/([^/]+)/SKILL\.md$",
        r"(?:^|/)plugins/([^/]+)/skills/([^/]+)/SKILL\.md$",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return match.group(1), match.group(2)
    standalone = re.search(
        r"(?:^|/)(?:\.codex|\.claude)/skills/(?:\.system/)?([^/]+)/SKILL\.md$",
        normalized,
    )
    if standalone:
        return None, standalone.group(1)
    return None


def _identity_from_qualified_skill(name: str) -> tuple[str | None, str]:
    normalized = name.removeprefix("/")
    if ":" in normalized:
        plugin, skill = normalized.split(":", 1)
        return plugin, skill
    return None, normalized


def _matches(
    identity: tuple[str | None, str], target_kind: str, target_name: str
) -> bool:
    plugin, skill = identity
    if target_kind == "plugin":
        return plugin == target_name
    qualified = f"{plugin}:{skill}" if plugin else skill
    return qualified == target_name


def _classify_codex_output(
    output: Any, skill_name: str, *, definitive_failure: bool
) -> tuple[str, str | None]:
    if output is None:
        return "incomplete", None
    text = _flatten_text(output)
    frontmatter = re.compile(
        FRONTMATTER_NAME_PATTERN.format(name=re.escape(skill_name))
    )
    if frontmatter.search(text):
        return "successful", None
    if definitive_failure and ERROR_PATTERN.search(text):
        return "problem", "skill-load-error"
    return "incomplete", None


def _has_initial_read_intent(value: str, tool_name: Any) -> bool:
    return bool(
        tool_name in {"Read", "read_file"}
        or re.search(r"\b(?:cat|head)\s+", value)
        or re.search(r"\bsed\s+-n\s+['\"]?1(?:,|p\b)", value)
    )


def _has_direct_read(value: str, skill_path: str, tool_name: Any) -> bool:
    if tool_name in {"Read", "read_file"}:
        return skill_path in value
    escaped_path = re.escape(skill_path)
    return bool(
        re.search(rf"\b(?:cat|head)\s+[^\n;]{{0,200}}{escaped_path}", value)
        or re.search(
            rf"\bsed\s+-n\s+['\"]?1(?:,|p\b)[^\n;]{{0,240}}{escaped_path}",
            value,
        )
    )


def _content_blocks(record: dict[str, Any]) -> list[dict[str, Any]]:
    message = record.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def _message_text(record: dict[str, Any]) -> str:
    message = record.get("message")
    if not isinstance(message, dict):
        return ""
    return _flatten_text(message.get("content"))


def _flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "\n".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return "\n".join(_flatten_text(item) for item in value)
    return ""


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_cwd(value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    return Path(value).expanduser().resolve(strict=False)


def _belongs_to_project(cwd: Path, project: Path) -> bool:
    return cwd == project or cwd.is_relative_to(project)


def _positive_days(value: str) -> int:
    days = int(value)
    if days <= 0:
        raise argparse.ArgumentTypeError("days must be positive")
    return days


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize recent Codex and Claude skill invocations."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--plugin")
    target.add_argument("--skill")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--days", type=_positive_days, default=30)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    target_kind = "plugin" if arguments.plugin else "skill"
    target_name = arguments.plugin or arguments.skill
    report = analyze(
        target_kind=target_kind,
        target_name=target_name,
        project=arguments.project,
        days=arguments.days,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
