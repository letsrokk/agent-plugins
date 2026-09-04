from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ANALYZER_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "inspect-plugin-usage"
    / "scripts"
    / "inspect_sessions.py"
)


def load_analyzer():
    spec = importlib.util.spec_from_file_location("inspect_sessions", ANALYZER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InspectSessionsTests(unittest.TestCase):
    def test_counts_recent_plugin_and_skill_usage_globally_and_by_project(self) -> None:
        self.assertTrue(ANALYZER_PATH.exists(), "analyzer entry point is missing")
        analyzer = load_analyzer()
        now = datetime(2026, 9, 4, 12, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_home = root / ".codex"
            claude_home = root / ".claude"
            project = root / "projects" / "sample"
            other_project = root / "projects" / "other"
            project.mkdir(parents=True)
            other_project.mkdir(parents=True)

            skill_path = (
                root
                / ".codex/plugins/cache/market/plugin-a/1.0.0"
                / "skills/review/SKILL.md"
            )
            self._write_jsonl(
                codex_home / "sessions/2026/09/03/current.jsonl",
                [
                    self._codex_record(
                        "2026-09-03T10:00:00Z",
                        "session_meta",
                        {"cwd": str(project)},
                    ),
                    self._codex_record(
                        "2026-09-03T10:01:00Z",
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec",
                            "call_id": "codex-success",
                            "input": f"sed -n '1,200p' '{skill_path}'",
                        },
                    ),
                    self._codex_record(
                        "2026-09-03T10:01:01Z",
                        "response_item",
                        {
                            "type": "custom_tool_call_output",
                            "call_id": "codex-success",
                            "output": [
                                {
                                    "type": "input_text",
                                    "text": "---\nname: review\ndescription: Review code\n---\n",
                                }
                            ],
                        },
                    ),
                ],
            )
            self._write_jsonl(
                codex_home / "sessions/2026/07/01/old.jsonl",
                [
                    self._codex_record(
                        "2026-07-01T10:00:00Z",
                        "session_meta",
                        {"cwd": str(project)},
                    ),
                    self._codex_record(
                        "2026-07-01T10:01:00Z",
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec",
                            "call_id": "old",
                            "input": f"cat '{skill_path}'",
                        },
                    ),
                ],
            )

            self._write_jsonl(
                claude_home / "projects/sample/session.jsonl",
                [
                    {
                        "type": "assistant",
                        "timestamp": "2026-09-02T11:00:00Z",
                        "cwd": str(project / "src"),
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": "Skill",
                                    "id": "claude-success",
                                    "input": {"skill": "plugin-a:review"},
                                }
                            ]
                        },
                    },
                    {
                        "type": "user",
                        "timestamp": "2026-09-02T11:00:01Z",
                        "cwd": str(project / "src"),
                        "message": {
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "claude-success",
                                    "content": "Launching skill: plugin-a:review",
                                    "is_error": False,
                                }
                            ]
                        },
                    },
                ],
            )
            self._write_jsonl(
                claude_home / "projects/other/session/subagents/agent-1.jsonl",
                [
                    {
                        "type": "user",
                        "timestamp": "2026-09-01T09:00:00Z",
                        "cwd": str(other_project),
                        "isMeta": True,
                        "message": {
                            "content": (
                                "<command-name>plugin-a:review</command-name>"
                            )
                        },
                    }
                ],
            )

            report = analyzer.analyze(
                target_kind="plugin",
                target_name="plugin-a",
                project=project,
                days=30,
                now=now,
                codex_home=codex_home,
                claude_home=claude_home,
            )

            self.assertEqual(
                report["scopes"]["all"]["combined"],
                {
                    "attempts": 3,
                    "successful": 3,
                    "problems": 0,
                    "incomplete": 0,
                    "scanned_sessions": 3,
                    "matched_sessions": 3,
                },
            )
            self.assertEqual(
                report["scopes"]["all"]["clients"]["codex"]["successful"],
                1,
            )
            self.assertEqual(
                report["scopes"]["all"]["clients"]["claude"]["successful"],
                2,
            )
            self.assertEqual(
                report["scopes"]["project"]["combined"]["attempts"],
                2,
            )
            self.assertEqual(
                report["scopes"]["project"]["combined"]["matched_sessions"],
                2,
            )

            skill_report = analyzer.analyze(
                target_kind="skill",
                target_name="plugin-a:review",
                project=None,
                days=30,
                now=now,
                codex_home=codex_home,
                claude_home=claude_home,
            )
            self.assertEqual(
                skill_report["scopes"]["all"]["combined"]["attempts"],
                3,
            )

    def test_reports_direct_failures_and_coverage_gaps_without_transcript_text(
        self,
    ) -> None:
        analyzer = load_analyzer()
        now = datetime(2026, 9, 4, 12, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_home = root / ".codex"
            claude_home = root / ".claude"
            project = root / "project"
            project.mkdir()
            skill_path = (
                root
                / ".codex/plugins/cache/market/plugin-a/1.0.0"
                / "skills/review/SKILL.md"
            )

            self._write_jsonl(
                codex_home / "sessions/2026/09/03/failure.jsonl",
                [
                    self._codex_record(
                        "2026-09-03T10:00:00Z",
                        "session_meta",
                        {"cwd": str(project)},
                    ),
                    self._codex_record(
                        "2026-09-03T10:01:00Z",
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec",
                            "call_id": "codex-failure",
                            "input": f"cat '{skill_path}'",
                        },
                    ),
                    self._codex_record(
                        "2026-09-03T10:01:01Z",
                        "response_item",
                        {
                            "type": "custom_tool_call_output",
                            "call_id": "codex-failure",
                            "output": "No such file: PRIVATE_TRANSCRIPT_TEXT",
                        },
                    ),
                    self._codex_record(
                        "2026-09-03T10:02:00Z",
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec",
                            "call_id": "diagnostic-mention",
                            "input": (
                                "sed -n '1,20p' "
                                "'/plugins/read-the-room/skills/write/SKILL.md'; "
                                "wc -l "
                                f"'{skill_path}' "
                            ),
                        },
                    ),
                    self._codex_record(
                        "2026-09-03T10:02:01Z",
                        "response_item",
                        {
                            "type": "custom_tool_call_output",
                            "call_id": "diagnostic-mention",
                            "output": "An old transcript contained an error",
                        },
                    ),
                    self._codex_record(
                        "2026-09-03T10:03:00Z",
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec",
                            "call_id": "continuation-read",
                            "input": f"sed -n '180,280p' '{skill_path}'",
                        },
                    ),
                    self._codex_record(
                        "2026-09-03T10:03:01Z",
                        "response_item",
                        {
                            "type": "custom_tool_call_output",
                            "call_id": "continuation-read",
                            "output": "Describe how failed commands are reported.",
                        },
                    ),
                    self._codex_record(
                        "2026-09-03T10:04:00Z",
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec",
                            "call_id": "multi-skill-failure",
                            "input": (
                                f"cat '{skill_path}' "
                                "'/plugins/other/skills/check/SKILL.md'"
                            ),
                        },
                    ),
                    self._codex_record(
                        "2026-09-03T10:04:01Z",
                        "response_item",
                        {
                            "type": "custom_tool_call_output",
                            "call_id": "multi-skill-failure",
                            "output": f"cat: {skill_path}: No such file",
                        },
                    ),
                ],
            )

            claude_path = claude_home / "projects/sample/failure.jsonl"
            claude_path.parent.mkdir(parents=True)
            claude_records = [
                {
                    "type": "future_record",
                    "timestamp": "2026-09-02T10:59:59Z",
                    "cwd": str(project),
                },
                {
                    "type": "assistant",
                    "timestamp": "2026-09-02T11:00:00Z",
                    "cwd": str(project),
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Skill",
                                "id": "claude-failure",
                                "input": {"skill": "plugin-a:review"},
                            },
                            {
                                "type": "tool_use",
                                "name": "Skill",
                                "id": "claude-incomplete",
                                "input": {"skill": "plugin-a:review"},
                            },
                        ]
                    },
                },
                {
                    "type": "user",
                    "timestamp": "2026-09-02T11:00:01Z",
                    "cwd": str(project),
                    "message": {
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": "claude-failure",
                                "content": "PRIVATE_TRANSCRIPT_TEXT",
                                "is_error": True,
                            }
                        ]
                    },
                },
            ]
            claude_path.write_text(
                "{malformed\n"
                + "".join(json.dumps(record) + "\n" for record in claude_records),
                encoding="utf-8",
            )
            self._write_jsonl(
                claude_home / "projects/unknown/session.jsonl",
                [
                    {
                        "type": "user",
                        "timestamp": "2026-09-01T09:00:00Z",
                        "isMeta": True,
                        "message": {
                            "content": (
                                "<command-name>plugin-a:review</command-name>"
                            )
                        },
                    }
                ],
            )

            report = analyzer.analyze(
                target_kind="skill",
                target_name="plugin-a:review",
                project=None,
                days=30,
                now=now,
                codex_home=codex_home,
                claude_home=claude_home,
            )

            totals = report["scopes"]["all"]["combined"]
            self.assertEqual(totals["attempts"], 5)
            self.assertEqual(totals["successful"], 1)
            self.assertEqual(totals["problems"], 3)
            self.assertEqual(totals["incomplete"], 1)
            self.assertEqual(
                report["scopes"]["all"]["problem_categories"],
                [
                    {"client": "claude", "category": "skill-error", "count": 1},
                    {
                        "client": "codex",
                        "category": "skill-load-error",
                        "count": 2,
                    },
                ],
            )
            self.assertIn(
                {"client": "claude", "category": "malformed-json", "count": 1},
                report["warnings"],
            )
            self.assertIn(
                {"client": "claude", "category": "unknown-record", "count": 1},
                report["warnings"],
            )
            self.assertIn(
                {
                    "client": "claude",
                    "category": "missing-session-cwd",
                    "count": 1,
                },
                report["warnings"],
            )
            self.assertNotIn("PRIVATE_TRANSCRIPT_TEXT", json.dumps(report))

            missing_root_report = analyzer.analyze(
                target_kind="skill",
                target_name="plugin-a:review",
                project=None,
                days=30,
                now=now,
                codex_home=codex_home,
                claude_home=root / "missing-claude",
            )
            self.assertIn(
                {
                    "client": "claude",
                    "category": "missing-session-root",
                    "count": 1,
                },
                missing_root_report["warnings"],
            )

    @staticmethod
    def _codex_record(timestamp: str, record_type: str, payload: dict) -> dict:
        return {"timestamp": timestamp, "type": record_type, "payload": payload}

    @staticmethod
    def _write_jsonl(path: Path, records: list[dict]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
