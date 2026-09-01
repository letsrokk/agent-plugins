from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PLUGIN_SRC))

from papercuts.paths import project_ref, resolve_storage, set_scope
from papercuts.service import PapercutsService


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
            )
            complaint_id = lodged["record"]["id"]
            self.assertTrue(lodged["changed"])
            self.assertEqual(lodged["record"]["encounter_count"], 1)

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
