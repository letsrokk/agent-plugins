from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.plugin_ci import changed_scripted_plugins


class PluginCISelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self._git("init", "-b", "main")
        self._git("config", "user.name", "Test User")
        self._git("config", "user.email", "test@example.com")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def _write(self, relative_path: str, content: str = "test\n") -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _commit(self, message: str) -> str:
        self._git("add", "-A")
        self._git("commit", "-m", message)
        return self._git("rev-parse", "HEAD")

    def test_selects_only_changed_scripted_plugins_present_at_head(self) -> None:
        self._write("plugins/alpha/src/alpha.py")
        self._write("plugins/skill-only/skills/example/SKILL.md")
        self._write("plugins/deleted/scripts/helper.py")
        base = self._commit("add plugins")

        self._write("plugins/alpha/src/alpha.py", "changed\n")
        self._write("plugins/skill-only/skills/example/SKILL.md", "changed\n")
        shutil.rmtree(self.root / "plugins/deleted")
        self._write("plugins/new-scripted/skills/example/scripts/check.py")
        head = self._commit("change plugins")

        self.assertEqual(
            changed_scripted_plugins(self.root, base, head),
            ["alpha", "new-scripted"],
        )

    def test_shared_contract_change_selects_every_scripted_plugin(self) -> None:
        self._write("plugins/alpha/src/alpha.py")
        self._write("plugins/gamma/skills/example/scripts/check.py")
        self._write("plugins/skill-only/skills/example/SKILL.md")
        self._write("docs/plugin-development.md", "before\n")
        base = self._commit("add plugins")
        self._write("docs/plugin-development.md", "after\n")
        head = self._commit("change shared contract")

        self.assertEqual(
            changed_scripted_plugins(self.root, base, head),
            ["alpha", "gamma"],
        )


if __name__ == "__main__":
    unittest.main()
