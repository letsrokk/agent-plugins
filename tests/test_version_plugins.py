from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


VERSION_SCRIPT = Path(__file__).parents[1] / "scripts/version_plugins.py"


class PluginVersioningTests(unittest.TestCase):
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

    def _write_json(self, relative_path: str, payload: dict[str, object]) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _write_plugin(
        self,
        name: str,
        version: str,
        *,
        codex: bool = True,
        claude: bool = False,
        runtime: bool = False,
    ) -> None:
        self._write_json(
            f"plugins/{name}/plugin.json",
            {"name": name, "version": version},
        )
        if codex:
            self._write_json(
                f"plugins/{name}/.codex-plugin/plugin.json",
                {"name": name, "version": version},
            )
        if claude:
            self._write_json(
                f"plugins/{name}/.claude-plugin/plugin.json",
                {"name": name, "version": version},
            )
        if runtime:
            package_name = name.replace("-", "_")
            path = self.root / f"plugins/{name}/src/{package_name}/__init__.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'__version__ = "{version}"\n', encoding="utf-8")

    def _commit(self, message: str) -> str:
        self._git("add", "-A")
        self._git("commit", "-m", message)
        return self._git("rev-parse", "HEAD")

    def _run_versioner(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VERSION_SCRIPT), *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def _manifest_version(self, relative_path: str) -> str:
        payload = json.loads((self.root / relative_path).read_text(encoding="utf-8"))
        return payload["version"]

    def test_apply_patch_bumps_all_changed_plugins_and_synchronizes_declarations(self) -> None:
        self._write_plugin("alpha-plugin", "1.2.3", claude=True, runtime=True)
        self._write_plugin("beta", "0.9.9")
        base = self._commit("add plugins")
        (self.root / "plugins/alpha-plugin/README.md").write_text("changed\n", encoding="utf-8")
        (self.root / "plugins/beta/README.md").write_text("changed\n", encoding="utf-8")
        head = self._commit("change plugins")

        result = self._run_versioner("apply", base, head)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self._manifest_version("plugins/alpha-plugin/plugin.json"),
            "1.2.4",
        )
        self.assertEqual(
            self._manifest_version("plugins/alpha-plugin/.codex-plugin/plugin.json"),
            "1.2.4",
        )
        self.assertEqual(
            self._manifest_version("plugins/alpha-plugin/.claude-plugin/plugin.json"),
            "1.2.4",
        )
        self.assertEqual(
            (self.root / "plugins/alpha-plugin/src/alpha_plugin/__init__.py").read_text(
                encoding="utf-8"
            ),
            '__version__ = "1.2.4"\n',
        )
        self.assertEqual(self._manifest_version("plugins/beta/plugin.json"), "0.9.10")

        bot_head = self._commit("chore: bump plugin versions")
        rerun = self._run_versioner("apply", head, bot_head)
        self.assertEqual(rerun.returncode, 0, rerun.stderr)
        self.assertEqual(self._git("status", "--porcelain"), "")

    def test_explicit_version_is_preserved_and_new_or_deleted_plugins_are_excluded(self) -> None:
        self._write_plugin("existing", "1.2.3", claude=True, runtime=True)
        self._write_plugin("deleted", "0.1.0")
        base = self._commit("add existing plugins")
        self._write_plugin("existing", "2.0.0", claude=True, runtime=True)
        (self.root / "plugins/existing/README.md").write_text("changed\n", encoding="utf-8")
        shutil.rmtree(self.root / "plugins/deleted")
        self._write_plugin("new-plugin", "0.1.0")
        (self.root / "README.md").write_text("repository docs\n", encoding="utf-8")
        head = self._commit("make mixed changes")

        check = self._run_versioner("check", base, head)
        apply = self._run_versioner("apply", base, head)

        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertEqual(apply.returncode, 0, apply.stderr)
        self.assertEqual(self._manifest_version("plugins/existing/plugin.json"), "2.0.0")
        self.assertEqual(self._manifest_version("plugins/new-plugin/plugin.json"), "0.1.0")
        self.assertEqual(self._git("status", "--porcelain"), "")

    def test_newer_main_version_covers_an_older_unversioned_change(self) -> None:
        self._write_plugin("example", "1.2.3", claude=True)
        base = self._commit("add plugin")
        (self.root / "plugins/example/README.md").write_text("first change\n", encoding="utf-8")
        head = self._commit("change plugin without version")
        self._write_plugin("example", "2.0.0", claude=True)
        self._commit("publish later version")

        result = self._run_versioner("apply", base, head)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._manifest_version("plugins/example/plugin.json"), "2.0.0")
        self.assertEqual(self._git("status", "--porcelain"), "")

    def test_stale_explicit_event_does_not_restore_its_version_to_main(self) -> None:
        self._write_plugin("example", "1.2.3")
        base = self._commit("add plugin")
        self._write_plugin("example", "2.0.0")
        head = self._commit("request major version")
        self._write_plugin("example", "1.5.0")
        self._commit("replace event version on main")

        result = self._run_versioner("apply", base, head)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to restore stale event version 2.0.0", result.stderr)
        self.assertEqual(self._manifest_version("plugins/example/plugin.json"), "1.5.0")
        self.assertEqual(self._git("status", "--porcelain"), "")

    def test_plugin_deleted_after_event_is_a_no_op(self) -> None:
        self._write_plugin("example", "1.2.3")
        base = self._commit("add plugin")
        (self.root / "plugins/example/README.md").write_text("changed\n", encoding="utf-8")
        head = self._commit("change plugin")
        shutil.rmtree(self.root / "plugins/example")
        self._commit("delete plugin")

        result = self._run_versioner("apply", base, head)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "plugins/example").exists())
        self.assertEqual(self._git("status", "--porcelain"), "")

    def test_check_rejects_decreased_version(self) -> None:
        self._write_plugin("example", "1.2.3")
        base = self._commit("add plugin")
        self._write_plugin("example", "1.2.2")
        head = self._commit("decrease version")

        result = self._run_versioner("check", base, head)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("version decreased from 1.2.3 to 1.2.2", result.stderr)

    def test_check_rejects_invalid_and_inconsistent_versions(self) -> None:
        self._write_plugin("example", "1.2.3", claude=True, runtime=True)
        base = self._commit("add plugin")
        self._write_plugin("example", "2.0.0", claude=True, runtime=True)
        self._write_json(
            "plugins/example/.claude-plugin/plugin.json",
            {"name": "example", "version": "v2"},
        )
        head = self._commit("write invalid compatibility version")

        result = self._run_versioner("check", base, head)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must use stable MAJOR.MINOR.PATCH SemVer", result.stderr)
        self.assertIn("must match portable manifest version 2.0.0", result.stderr)

    def test_check_validates_new_plugin_version_without_scheduling_a_bump(self) -> None:
        (self.root / "README.md").write_text("repository\n", encoding="utf-8")
        base = self._commit("initialize repository")
        self._write_plugin("new-plugin", "0.1")
        head = self._commit("add plugin with invalid release version")

        result = self._run_versioner("check", base, head)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must use stable MAJOR.MINOR.PATCH SemVer", result.stderr)


if __name__ == "__main__":
    unittest.main()
