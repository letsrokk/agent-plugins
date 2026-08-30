import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_marketplaces import validate_repository


class MarketplaceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self._write_catalogs()
        (self.root / "AGENTS.md").write_text("# Agent guidelines\n", encoding="utf-8")
        (self.root / "CLAUDE.md").symlink_to("AGENTS.md")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_json(self, relative_path: str, payload: object) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def _write_catalogs(
        self,
        *,
        codex_plugins: list[dict[str, object]] | None = None,
        claude_plugins: list[dict[str, object]] | None = None,
    ) -> None:
        self._write_json(
            ".agents/plugins/marketplace.json",
            {
                "name": "rokk-club-codex-plugins",
                "interface": {"displayName": "Rokk Club Codex Plugins"},
                "plugins": codex_plugins or [],
            },
        )
        self._write_json(
            ".claude-plugin/marketplace.json",
            {
                "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
                "name": "rokk-club-claude-plugins",
                "owner": {"name": "Rokk Club"},
                "plugins": claude_plugins or [],
            },
        )

    @staticmethod
    def _codex_entry(name: str, path: str | None = None) -> dict[str, object]:
        return {
            "name": name,
            "source": {"source": "local", "path": path or f"./plugins/{name}"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Developer Tools",
        }

    @staticmethod
    def _claude_entry(name: str, path: str | None = None) -> dict[str, object]:
        return {"name": name, "source": path or f"./plugins/{name}"}

    def _write_portable_manifest(self, name: str) -> None:
        self._write_json(
            f"plugins/{name}/plugin.json",
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": name,
            },
        )

    def test_accepts_empty_marketplaces_and_agents_symlink(self) -> None:
        self.assertEqual(validate_repository(self.root), [])

    def test_rejects_duplicate_plugin_names(self) -> None:
        entry = self._codex_entry("duplicate")
        self._write_catalogs(codex_plugins=[entry, entry])
        self._write_portable_manifest("duplicate")

        errors = validate_repository(self.root)

        self.assertTrue(any("duplicate plugin name 'duplicate'" in error for error in errors))

    def test_rejects_source_path_that_can_escape_plugins_directory(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("unsafe", "./plugins/../unsafe")])

        errors = validate_repository(self.root)

        self.assertTrue(any("must be './plugins/unsafe'" in error for error in errors))

    def test_rejects_codex_entry_without_required_policy_and_category(self) -> None:
        self._write_catalogs(
            codex_plugins=[
                {
                    "name": "incomplete",
                    "source": {"source": "local", "path": "./plugins/incomplete"},
                }
            ]
        )
        self._write_portable_manifest("incomplete")

        errors = validate_repository(self.root)

        self.assertTrue(any("policy.installation must be 'AVAILABLE'" in error for error in errors))
        self.assertTrue(any("policy.authentication must be 'ON_INSTALL'" in error for error in errors))
        self.assertTrue(any("category must be a non-empty string" in error for error in errors))

    def test_rejects_plugin_without_portable_manifest(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("missing-manifest")])
        (self.root / "plugins/missing-manifest").mkdir(parents=True)

        errors = validate_repository(self.root)

        self.assertTrue(any("missing portable manifest" in error for error in errors))

    def test_rejects_claude_plugin_without_compatibility_manifest(self) -> None:
        self._write_catalogs(claude_plugins=[self._claude_entry("claude-ready")])
        self._write_portable_manifest("claude-ready")

        errors = validate_repository(self.root)

        self.assertTrue(any("missing Claude compatibility manifest" in error for error in errors))

    def test_rejects_claude_file_instead_of_agents_symlink(self) -> None:
        (self.root / "CLAUDE.md").unlink()
        (self.root / "CLAUDE.md").write_text("# Duplicate instructions\n", encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertIn("CLAUDE.md must be a symlink to AGENTS.md", errors)


if __name__ == "__main__":
    unittest.main()
