import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class SessionStartTests(unittest.TestCase):
    def test_packaged_hook_loads_current_policy_from_any_directory(self):
        with tempfile.TemporaryDirectory(prefix="read the room ") as temporary:
            root = Path(temporary).resolve()
            plugin = root / "installed plugin"
            shutil.copytree(PLUGIN_ROOT, plugin)
            config = json.loads((plugin / "hooks" / "hooks.json").read_text())
            group = config["hooks"]["SessionStart"][0]
            self.assertNotIn("matcher", group)
            command = group["hooks"][0]["command"]
            environment = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin))
            skill = plugin / "skills" / "make-it-make-sense"
            for source in ("startup", "resume", "clear", "compact"):
                with self.subTest(source=source):
                    if source == "compact":
                        with (skill / "SKILL.md").open("a") as policy:
                            policy.write("\nFresh policy after compaction.\n")
                    result = subprocess.run(
                        command, shell=True, cwd=root, env=environment,
                        input=json.dumps({"hook_event_name": "SessionStart", "source": source}),
                        capture_output=True, text=True, check=True,
                    )
                    self.assertEqual(result.stderr, "")
                    output = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(output["hookEventName"], "SessionStart")
                    context = output["additionalContext"]
                    self.assertIn("# Make It Make Sense", context)
                    self.assertIn("Drafting does not authorize posting", context)
                    self.assertNotIn("name: make-it-make-sense", context)
                    self.assertIn((skill / "references/agent-responses.md").read_text().strip(), context)
                    for name in ("agent-responses", "version-control", "issue-trackers", "knowledge-bases", "chat"):
                        reference = skill / "references" / f"{name}.md"
                        self.assertIn(f"](<{reference}>)", context)
                        if name != "agent-responses":
                            self.assertNotIn(reference.read_text().strip(), context)
                    if source == "compact":
                        self.assertIn("Fresh policy after compaction.", context)

    def test_missing_policy_files_emit_no_partial_context(self):
        for missing in ("SKILL.md", "references/agent-responses.md"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temporary:
                plugin = Path(temporary) / "plugin"
                shutil.copytree(PLUGIN_ROOT, plugin)
                (plugin / "skills/make-it-make-sense" / missing).unlink()
                result = subprocess.run(
                    [sys.executable, str(plugin / "scripts/session_start.py")],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("could not load its writing policy", result.stderr)
