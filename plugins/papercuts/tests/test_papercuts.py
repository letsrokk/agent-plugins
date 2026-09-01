from __future__ import annotations

import io
import json
import socket
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PLUGIN_SRC))

from papercuts.models import PapercutsError, PrunePolicy
from papercuts.cli import main as cli_main
from papercuts.paths import project_ref, resolve_storage, set_scope
from papercuts.service import PapercutsService
from papercuts.store import JournalStore


class PapercutsPluginTests(unittest.TestCase):
    def test_main_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "agent-plugins"
            home = Path(directory) / "home"
            root.mkdir()
            home.mkdir()

            project = project_ref(
                root,
                "git@github.com:letsrokk/agent-plugins.git",
            )
            equivalent = project_ref(
                root,
                "https://github.com/letsrokk/agent-plugins",
            )
            self.assertEqual(project.id, equivalent.id)
            self.assertEqual(project.name, "agent-plugins")
            self.assertNotIn(str(root), json.dumps(project.to_dict()))
            self.assertNotIn("github.com", project.id)

            storage = resolve_storage(
                root,
                home=home,
                project_root=root,
                remote_url="git@github.com:letsrokk/agent-plugins.git",
            )
            self.assertEqual(storage.scope, "project")
            self.assertEqual(storage.journal_path, root / ".codex/papercuts.jsonl")

            config_path = set_scope(root, "user", "project", home=home)
            self.assertEqual(config_path, root / ".codex/papercuts.config.json")
            storage = resolve_storage(
                root,
                home=home,
                project_root=root,
                remote_url="git@github.com:letsrokk/agent-plugins.git",
            )
            self.assertEqual(storage.scope, "user")
            self.assertEqual(storage.journal_path, home / ".codex/papercuts.jsonl")

            times = iter(
                datetime(2026, 8, 31, hour, tzinfo=timezone.utc)
                for hour in range(10, 20)
            )
            service = PapercutsService(storage, now=lambda: next(times))

            lodged = service.lodge(
                "Validator hides the invalid manifest path",
                severity="major",
                tags=["tooling", "validator"],
                context={
                    "command": (
                        "curl -H 'Authorization: Bearer bearer-secret-value' "
                        "https://user:password@example.invalid && API_TOKEN=token-value "
                        f"--worktree {root}"
                    ),
                    "exit_status": 1,
                    "stderr": "ghp_abcdefghijklmnopqrstuvwxyz123456 sk-proj-abcdefghijklmnopqrstuvwxyz123456",
                    "note": (
                        "DATABASE_PASSWORD=not-for-the-journal "
                        "remote=https://github.com/acme/private.git "
                        "alias=git@github:acme/private.git"
                    ),
                },
            )
            complaint_id = lodged["record"]["id"]
            self.assertTrue(lodged["changed"])
            self.assertEqual(lodged["record"]["encounter_count"], 1)
            sanitized_context = lodged["record"]["context"]
            self.assertEqual(sanitized_context["exit_status"], 1)
            self.assertNotIn("bearer-secret-value", json.dumps(sanitized_context))
            self.assertNotIn("password@example", json.dumps(sanitized_context))
            self.assertNotIn("token-value", json.dumps(sanitized_context))
            self.assertNotIn("ghp_", json.dumps(sanitized_context))
            self.assertNotIn("sk-proj-", json.dumps(sanitized_context))
            self.assertNotIn("not-for-the-journal", json.dumps(sanitized_context))
            self.assertNotIn(str(root), json.dumps(sanitized_context))
            self.assertNotIn(
                "https://github.com/acme/private.git",
                json.dumps(sanitized_context),
            )
            self.assertNotIn(
                "git@github:acme/private.git",
                json.dumps(sanitized_context),
            )

            journal_before_environment = storage.journal_path.read_bytes()
            with self.assertRaises(PapercutsError) as rejected_environment:
                service.lodge(
                    "Raw environments must not enter evidence",
                    context={
                        "stderr": (
                            "HOME=/Users/example\n"
                            "PATH=/usr/local/bin:/usr/bin\n"
                            "SHELL=/bin/zsh"
                        )
                    },
                )
            self.assertEqual(rejected_environment.exception.code, "invalid_input")
            self.assertEqual(rejected_environment.exception.exit_status, 65)
            self.assertEqual(
                storage.journal_path.read_bytes(), journal_before_environment
            )

            journal_before_headed_environment = storage.journal_path.read_bytes()
            with self.assertRaises(PapercutsError) as rejected_headed_environment:
                service.lodge(
                    "Headed environments must not enter evidence",
                    context={
                        "stderr": (
                            "Environment:\n"
                            "AWS_ACCESS_KEY_ID=example-access-key\n"
                            "CI_JOB_JWT=example.jwt.value"
                        )
                    },
                )
            self.assertEqual(
                rejected_headed_environment.exception.code, "invalid_input"
            )
            self.assertEqual(rejected_headed_environment.exception.exit_status, 65)
            self.assertEqual(
                storage.journal_path.read_bytes(),
                journal_before_headed_environment,
            )

            duplicate = service.lodge(
                "  Validator hides the invalid manifest path  ",
                severity="minor",
                tags=["validator", "tooling"],
            )
            self.assertEqual(duplicate["record"]["id"], complaint_id)
            self.assertEqual(duplicate["record"]["vote_count"], 1)

            voted = service.vote(
                complaint_id[:8], note="Repeated during catalog validation"
            )
            self.assertEqual(voted["record"]["encounter_count"], 3)

            resolved = service.resolve(
                complaint_id, note="Validator now reports the path"
            )
            self.assertEqual(resolved["record"]["status"], "resolved")

            recurred = service.vote(
                complaint_id, note="Regression in a new validation run"
            )
            self.assertEqual(recurred["record"]["status"], "open")
            self.assertEqual(recurred["record"]["vote_count"], 3)

            listed = service.list(query="manifest", tags=["tooling"])
            self.assertEqual([item["id"] for item in listed], [complaint_id])
            self.assertEqual(service.get(complaint_id[:8])["id"], complaint_id)

            from papercuts.mcp_server import invoke_tool

            mcp_result = invoke_tool(
                service,
                "list_complaints",
                {"status": "all", "query": "manifest", "limit": 10},
            )
            self.assertEqual(mcp_result["complaints"][0]["id"], complaint_id)
            self.assertEqual(mcp_result["count"], 1)

            cli_out = io.StringIO()
            cli_err = io.StringIO()
            exit_status = cli_main(
                [
                    "--file",
                    str(storage.journal_path),
                    "list",
                    "--status",
                    "all",
                    "--all-projects",
                ],
                cwd=root,
                environ={},
                stdout=cli_out,
                stderr=cli_err,
            )
            self.assertEqual(exit_status, 0)
            self.assertEqual(cli_err.getvalue(), "")
            cli_payload = json.loads(cli_out.getvalue())
            self.assertTrue(cli_payload["ok"])
            self.assertEqual(cli_payload["meta"]["contract"], 1)
            self.assertEqual(cli_payload["data"][0]["id"], complaint_id)

            markdown_out = io.StringIO()
            markdown_err = io.StringIO()
            markdown_status = cli_main(
                [
                    "--file",
                    str(storage.journal_path),
                    "list",
                    "--status",
                    "all",
                    "--all-projects",
                    "--format",
                    "md",
                ],
                cwd=root,
                environ={},
                stdout=markdown_out,
                stderr=markdown_err,
            )
            self.assertEqual(markdown_status, 0)
            self.assertEqual(markdown_err.getvalue(), "")
            self.assertTrue(markdown_out.getvalue().startswith("# Papercuts\n"))
            self.assertIn(complaint_id, markdown_out.getvalue())

            error_out = io.StringIO()
            error_err = io.StringIO()
            error_status = cli_main(
                ["--file", str(storage.journal_path), "get", "missing"],
                cwd=root,
                environ={},
                stdout=error_out,
                stderr=error_err,
            )
            self.assertEqual(error_status, 66)
            self.assertEqual(error_out.getvalue(), "")
            error_payload = json.loads(error_err.getvalue())
            self.assertFalse(error_payload["ok"])
            self.assertEqual(error_payload["error"]["code"], "not_found")

            health = service.doctor()
            self.assertTrue(health["healthy"])
            self.assertGreaterEqual(health["event_count"], 6)

            journal_before_invalid_event = storage.journal_path.read_bytes()
            invalid_service = PapercutsService(
                storage,
                agent="",
                now=lambda: datetime(2026, 8, 31, 19, tzinfo=timezone.utc),
            )
            with self.assertRaises(PapercutsError):
                invalid_service.lodge("An invalid agent must not poison the journal")
            self.assertEqual(
                storage.journal_path.read_bytes(), journal_before_invalid_event
            )

            foreign_lock = root / "foreign-lock"
            foreign_lock.mkdir()
            foreign_owner = foreign_lock / "owner.json"
            foreign_owner.write_text(
                json.dumps(
                    {
                        "token": "foreign",
                        "pid": 2_147_483_647,
                        "host": socket.gethostname(),
                        "created_at": "2020-01-01T00:00:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            unsafe_store = JournalStore(root / "unsafe.jsonl")
            unsafe_store.lock_path.symlink_to(foreign_lock, target_is_directory=True)
            with self.assertRaises(PapercutsError) as rejected_lock:
                with unsafe_store.mutation():
                    self.fail("symlinked lock was accepted")
            self.assertEqual(rejected_lock.exception.code, "invalid_input")
            self.assertTrue(foreign_owner.exists())

            valid_event = json.loads(storage.journal_path.read_text().splitlines()[0])
            malformed_events = (
                {**valid_event, "kind": []},
                {**valid_event, "severity": []},
            )
            for index, malformed_event in enumerate(malformed_events):
                malformed_path = root / f"malformed-{index}.jsonl"
                malformed_path.write_text(
                    json.dumps(malformed_event) + "\n", encoding="utf-8"
                )
                with self.assertRaises(PapercutsError) as rejected_event:
                    JournalStore(malformed_path).read_events()
                self.assertEqual(
                    rejected_event.exception.code, "malformed_journal"
                )

    def test_stale_prune_plan_cannot_replace_changed_journal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            home = Path(directory) / "home"
            root.mkdir()
            home.mkdir()
            storage = resolve_storage(root, home=home, project_root=root, remote_url=None)
            moments = iter(
                [
                    datetime(2025, 1, 1, tzinfo=timezone.utc),
                    datetime(2026, 8, 31, tzinfo=timezone.utc),
                    datetime(2026, 8, 31, 1, tzinfo=timezone.utc),
                    datetime(2026, 8, 31, 2, tzinfo=timezone.utc),
                ]
            )
            service = PapercutsService(storage, now=lambda: next(moments))
            old = service.lodge("One-off obsolete friction")["record"]["id"]
            preview = service.preview_prune(PrunePolicy())
            self.assertEqual([item["id"] for item in preview["candidates"]], [old])

            service.lodge("New complaint after preview", tags=["new"])
            before = storage.journal_path.read_bytes()

            with self.assertRaises(PapercutsError) as raised:
                service.apply_prune(PrunePolicy(), preview["plan_id"])

            self.assertEqual(raised.exception.code, "stale_prune_plan")
            self.assertEqual(storage.journal_path.read_bytes(), before)
            backup_dir = root / ".codex/papercuts.backups"
            self.assertFalse(backup_dir.exists())
