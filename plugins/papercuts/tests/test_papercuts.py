from __future__ import annotations

import io
import json
import socket
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

PLUGIN_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PLUGIN_SRC))

from papercuts.models import PapercutsError, PrunePolicy, sanitize_context
from papercuts.cli import main as cli_main
from papercuts.paths import discover_project, project_ref, resolve_storage, set_scope
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

            from papercuts.mcp_server import _invoke_project_tool, invoke_tool

            mcp_result = invoke_tool(
                service,
                "list_complaints",
                {"status": "all", "query": "manifest", "limit": 10},
            )
            self.assertEqual(mcp_result["complaints"][0]["id"], complaint_id)
            self.assertEqual(mcp_result["count"], 1)

            invalid_project_result = _invoke_project_tool(
                str(root / "missing"),
                "inspect_storage",
                {},
            )
            self.assertFalse(invalid_project_result["ok"])
            self.assertEqual(
                invalid_project_result["error"]["code"],
                "invalid_input",
            )

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

            first_secret = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"
            second_secret = "sk-proj-zyxwvutsrqponmlkjihgfedcba654321"
            first_sensitive = service.lodge(
                (
                    f"Trace at {root} used "
                    f"https://user:password@example.invalid and {first_secret}"
                ),
                tags=[f"root={root}", first_secret],
            )
            second_sensitive = service.lodge(
                (
                    f"Trace at {root} used "
                    f"https://other:secret@example.invalid and {second_secret}"
                ),
                tags=[f"root={root}", second_secret],
            )
            with self.subTest("complaint identity uses sanitized strings"):
                self.assertEqual(
                    first_sensitive["record"]["id"],
                    second_sensitive["record"]["id"],
                )
            with self.subTest("complaint text and tags do not persist sensitive data"):
                persisted = storage.journal_path.read_text(encoding="utf-8")
                for sensitive_value in (
                    str(root),
                    "password@example",
                    "secret@example",
                    first_secret,
                    second_secret,
                ):
                    self.assertNotIn(sensitive_value, persisted)

            environment_shapes = {
                "two-key JSON": json.dumps(
                    {
                        "AWS_ACCESS_KEY_ID": "example-access-key",
                        "CI_JOB_JWT": "example.jwt.value",
                    }
                ),
                "declare export": (
                    'declare -x AWS_ACCESS_KEY_ID="example-access-key"\n'
                    'declare -x CI_JOB_JWT="example.jwt.value"'
                ),
                "NUL separated": (
                    "HOME=/Users/example\0PATH=/usr/local/bin:/usr/bin\0"
                ),
            }
            for shape, evidence in environment_shapes.items():
                with self.subTest(environment_shape=shape):
                    with self.assertRaises(PapercutsError) as rejected_dump:
                        sanitize_context({"stderr": evidence})
                    self.assertEqual(rejected_dump.exception.code, "invalid_input")
            sanitized_secret_note = sanitize_context(
                {
                    "note": (
                        "AWS_ACCESS_KEY_ID=example-access-key "
                        "CI_JOB_JWT=example.jwt.value"
                    )
                }
            )["note"]
            with self.subTest("secret-shaped environment names are redacted"):
                self.assertNotIn("example-access-key", sanitized_secret_note)
                self.assertNotIn("example.jwt.value", sanitized_secret_note)

            symlink_destination = root / "symlink-destination"
            (symlink_destination / "nested").mkdir(parents=True)
            intermediate_link = root / "intermediate-link"
            intermediate_link.symlink_to(
                symlink_destination,
                target_is_directory=True,
            )
            traversing_store = JournalStore(
                intermediate_link / "nested" / "papercuts.jsonl"
            )
            with self.subTest("journal path rejects intermediate symlink"):
                with self.assertRaises(PapercutsError) as rejected_path:
                    with traversing_store.mutation():
                        self.fail("intermediate symlink was accepted")
                self.assertEqual(rejected_path.exception.code, "invalid_input")

            append_target = root / "append-target.jsonl"
            append_target.write_bytes(b"sentinel\n")
            append_path = root / "append-race.jsonl"
            append_store = JournalStore(append_path)
            with self.subTest("append refuses a final symlink introduced under lock"):
                with append_store.mutation():
                    append_path.symlink_to(append_target)
                    with self.assertRaises(PapercutsError) as rejected_append:
                        append_store.append_events_locked([valid_event])
                    self.assertEqual(rejected_append.exception.code, "invalid_input")
                self.assertEqual(append_target.read_bytes(), b"sentinel\n")

            journal_events = [
                json.loads(line)
                for line in storage.journal_path.read_text(encoding="utf-8").splitlines()
            ]
            complaint_event = next(
                event for event in journal_events if event["kind"] == "complaint"
            )
            encounter_event = next(
                event for event in journal_events if event["kind"] == "encounter"
            )
            orphan_event = {
                **encounter_event,
                "complaint_id": "pc_missing_parent",
            }
            mismatched_event = {
                **encounter_event,
                "complaint_id": complaint_event["id"],
                "project": {
                    **encounter_event["project"],
                    "id": "prj_other_project",
                },
            }
            relational_cases = (
                ("orphan", [orphan_event], 1),
                ("duplicate", [complaint_event, complaint_event], 2),
                ("project-mismatch", [complaint_event, mismatched_event], 2),
            )
            for name, corrupt_events, error_line in relational_cases:
                relational_path = root / f"relational-{name}.jsonl"
                relational_path.write_text(
                    "".join(json.dumps(event) + "\n" for event in corrupt_events),
                    encoding="utf-8",
                )
                with self.subTest(relational_corruption=name):
                    with self.assertRaises(PapercutsError) as rejected_relational:
                        JournalStore(relational_path).doctor()
                    self.assertEqual(
                        rejected_relational.exception.code,
                        "malformed_journal",
                    )
                    self.assertIn(
                        f"{relational_path}:{error_line}",
                        rejected_relational.exception.message,
                    )
                    self.assertNotIn(
                        "<events>",
                        rejected_relational.exception.message,
                    )

            with self.subTest("missing Git falls back to cwd"):
                with patch(
                    "papercuts.paths.subprocess.run",
                    side_effect=FileNotFoundError("git is unavailable"),
                ):
                    self.assertEqual(discover_project(root), (root, None))

            config_root = root / "config-permission"
            config_root.mkdir()
            with self.subTest("config permission failure is public and cleans temp"):
                with patch(
                    "papercuts.paths.discover_project",
                    return_value=(config_root, None),
                ), patch(
                    "papercuts.paths.os.replace",
                    side_effect=PermissionError("read-only configuration"),
                ):
                    with self.assertRaises(PapercutsError) as rejected_config:
                        set_scope(
                            config_root,
                            "project",
                            "project",
                            home=home,
                        )
                self.assertEqual(
                    rejected_config.exception.code,
                    "permission_denied",
                )
                self.assertEqual(
                    list(
                        (config_root / ".codex").glob(
                            ".papercuts.config.json.*"
                        )
                    ),
                    [],
                )

            config_write_root = root / "config-write-permission"
            config_write_root.mkdir()
            with self.subTest("config write failure also cleans temp"):
                with patch(
                    "papercuts.paths.discover_project",
                    return_value=(config_write_root, None),
                ), patch(
                    "papercuts.paths.json.dump",
                    side_effect=PermissionError("configuration write failed"),
                ):
                    with self.assertRaises(PapercutsError) as rejected_write:
                        set_scope(
                            config_write_root,
                            "project",
                            "project",
                            home=home,
                        )
                self.assertEqual(
                    rejected_write.exception.code,
                    "permission_denied",
                )
                self.assertEqual(
                    list(
                        (config_write_root / ".codex").glob(
                            ".papercuts.config.json.*"
                        )
                    ),
                    [],
                )

            permission_store = JournalStore(root / "permission-denied.jsonl")
            with self.subTest("journal permission failure uses public code"):
                with patch(
                    "papercuts.store.os.open",
                    side_effect=PermissionError("read-only journal"),
                ):
                    with self.assertRaises(PapercutsError) as rejected_journal:
                        permission_store.append_events_locked([valid_event])
                self.assertEqual(
                    rejected_journal.exception.code,
                    "permission_denied",
                )
                self.assertEqual(rejected_journal.exception.exit_status, 77)

            inspection_before = storage.journal_path.read_bytes()
            concurrent_event = {
                **valid_event,
                "id": "pc_concurrent_snapshot",
                "text": "Concurrent inspection event",
            }
            concurrent_record = (
                json.dumps(
                    concurrent_event,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
            original_read_bytes = service.store._read_bytes

            def read_then_append() -> bytes:
                snapshot = original_read_bytes()
                storage.journal_path.write_bytes(snapshot + concurrent_record)
                return snapshot

            with self.subTest("inspection fields use one journal snapshot"):
                with patch.object(
                    service.store,
                    "_read_bytes",
                    side_effect=read_then_append,
                ):
                    inspection = service.inspect_storage()
                self.assertEqual(
                    inspection["byte_count"],
                    len(inspection_before),
                )
                self.assertEqual(
                    inspection["event_count"],
                    len(inspection_before.splitlines()),
                )
                self.assertTrue(inspection["healthy"])

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

            fresh_service = PapercutsService(
                storage,
                now=lambda: datetime(2026, 9, 1, tzinfo=timezone.utc),
            )
            fresh_preview = fresh_service.preview_prune(PrunePolicy())
            before_permission_failure = storage.journal_path.read_bytes()
            original_stat = Path.stat

            def deny_journal_metadata(path: Path, *args, **kwargs):
                if path == storage.journal_path:
                    raise PermissionError("journal metadata denied")
                return original_stat(path, *args, **kwargs)

            with patch(
                "papercuts.service.Path.stat",
                autospec=True,
                side_effect=deny_journal_metadata,
            ):
                with self.assertRaises(PapercutsError) as rejected_prune_stat:
                    fresh_service.apply_prune(
                        PrunePolicy(),
                        fresh_preview["plan_id"],
                    )
            self.assertEqual(
                rejected_prune_stat.exception.code,
                "permission_denied",
            )
            self.assertEqual(
                storage.journal_path.read_bytes(),
                before_permission_failure,
            )
            self.assertFalse(backup_dir.exists())

            before_fresh_apply = storage.journal_path.read_bytes()
            applied = fresh_service.apply_prune(
                PrunePolicy(),
                fresh_preview["plan_id"],
            )
            backup_path = Path(applied["backup"])
            self.assertTrue(applied["changed"])
            self.assertEqual(applied["removed_complaints"], 1)
            self.assertEqual(backup_path.read_bytes(), before_fresh_apply)
            self.assertNotIn(old, storage.journal_path.read_text(encoding="utf-8"))
            self.assertIn(
                "New complaint after preview",
                storage.journal_path.read_text(encoding="utf-8"),
            )
