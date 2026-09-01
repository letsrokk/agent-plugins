from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.validate_marketplaces as marketplace_validator
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

    def _write_portable_manifest(self, name: str, *, version: str = "0.1.0") -> None:
        self._write_json(
            f"plugins/{name}/plugin.json",
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": name,
                "version": version,
            },
        )

    def _write_codex_manifest(
        self,
        name: str,
        *,
        version: str = "0.1.0",
        skills: bool = True,
    ) -> None:
        payload: dict[str, object] = {"name": name, "version": version}
        if skills:
            payload["skills"] = "./skills/"
        self._write_json(f"plugins/{name}/.codex-plugin/plugin.json", payload)

    def _write_skill(self, plugin: str, skill: str, *, frontmatter_name: str | None = None) -> None:
        path = self.root / f"plugins/{plugin}/skills/{skill}/SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {frontmatter_name or skill}\ndescription: Test skill.\n---\n\n# Test skill\n",
            encoding="utf-8",
        )

    def _write_code_simplifier_package(
        self, *, include_notice: bool = True, include_agent: bool = True
    ) -> None:
        self._write_json(
            "plugins/code-simplifier/plugin.json",
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": "code-simplifier",
                "version": "0.1.0",
                "description": "Simplify code without changing behavior.",
                "author": {"name": "Rokk Club"},
                "homepage": "https://github.com/letsrokk/agent-plugins",
                "repository": "https://github.com/letsrokk/agent-plugins",
                "license": "Apache-2.0",
                "keywords": ["codex", "code-quality"],
            },
        )
        self._write_codex_manifest("code-simplifier")
        skill_root = self.root / "plugins/code-simplifier/skills/code-simplifier"
        (skill_root / "agents").mkdir(parents=True, exist_ok=True)
        (skill_root / "SKILL.md").write_text(
            "---\nname: code-simplifier\ndescription: Simplify code.\n---\n\n"
            "# Code Simplifier\n\nAdapted from Anthropic's Code Simplifier.\n"
            "Dispatch `code_simplifier`.\n",
            encoding="utf-8",
        )
        (skill_root / "agents/openai.yaml").write_text(
            'interface:\n  display_name: "Code Simplifier"\n',
            encoding="utf-8",
        )
        if include_agent:
            (skill_root / "agents/code_simplifier.toml").write_text(
                "# Adapted from Anthropic's Code Simplifier for Codex.\n"
                'name = "code_simplifier"\n'
                'description = "Simplifies code."\n'
                'developer_instructions = "Preserve behavior."\n',
                encoding="utf-8",
            )
        (self.root / "plugins/code-simplifier/LICENSE").write_text(
            "Apache License\nVersion 2.0, January 2004\n",
            encoding="utf-8",
        )
        if include_notice:
            (self.root / "plugins/code-simplifier/NOTICE").write_text(
                "Code Simplifier includes modified material from Anthropic's Code Simplifier.\n"
                "https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier\n"
                "Rokk Club adapted it from a Claude Code agent into a Codex skill and custom agent.\n",
                encoding="utf-8",
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

    def test_accepts_complete_code_simplifier_package(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("code-simplifier")])
        self._write_code_simplifier_package()

        self.assertEqual(validate_repository(self.root), [])

    def test_accepts_codex_package_with_matching_compatibility_manifest(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("complete")])
        self._write_portable_manifest("complete")
        self._write_codex_manifest("complete")
        self._write_skill("complete", "complete")

        self.assertEqual(validate_repository(self.root), [])

    def test_rejects_inconsistent_codex_compatibility_manifest(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("inconsistent")])
        self._write_portable_manifest("inconsistent", version="1.2.3")
        self._write_json(
            "plugins/inconsistent/.codex-plugin/plugin.json",
            {"name": "other", "version": "1.2.2"},
        )
        self._write_skill("inconsistent", "inconsistent")

        errors = validate_repository(self.root)

        self.assertTrue(any("name must match catalog entry 'inconsistent'" in error for error in errors))
        self.assertTrue(any("version must match portable manifest '1.2.3'" in error for error in errors))
        self.assertTrue(any("skills must be './skills/'" in error for error in errors))

    def test_rejects_unknown_portable_manifest_field(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("unknown-field")])
        self._write_json(
            "plugins/unknown-field/plugin.json",
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": "unknown-field",
                "skills": "./skills/",
            },
        )
        self._write_skill("unknown-field", "unknown-field")

        errors = validate_repository(self.root)

        self.assertTrue(any("unknown field 'skills'" in error for error in errors))

    def test_rejects_plugin_without_discoverable_component(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("empty-plugin")])
        self._write_portable_manifest("empty-plugin")

        errors = validate_repository(self.root)

        self.assertTrue(any("must provide at least one skill or mcp.json" in error for error in errors))

    def test_rejects_skill_name_that_differs_from_directory(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("bad-skill")])
        self._write_portable_manifest("bad-skill")
        self._write_skill("bad-skill", "expected-name", frontmatter_name="different-name")

        errors = validate_repository(self.root)

        self.assertTrue(any("skill name must match directory 'expected-name'" in error for error in errors))

    def test_rejects_malformed_custom_agent_toml(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("bad-agent")])
        self._write_portable_manifest("bad-agent")
        self._write_skill("bad-agent", "bad-agent")
        agent = self.root / "plugins/bad-agent/skills/bad-agent/agents/bad_agent.toml"
        agent.parent.mkdir(parents=True)
        agent.write_text('name = "unterminated\n', encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(any("invalid TOML" in error for error in errors))

    def test_requires_tomllib_for_custom_agent_validation(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("bad-agent")])
        self._write_portable_manifest("bad-agent")
        self._write_skill("bad-agent", "bad-agent")
        agent = self.root / "plugins/bad-agent/skills/bad-agent/agents/bad_agent.toml"
        agent.parent.mkdir(parents=True)
        agent.write_text("name = 'bad_agent'\n", encoding="utf-8")

        with patch.object(marketplace_validator, "tomllib", None):
            errors = validate_repository(self.root)

        self.assertTrue(any("requires Python 3.11 or later" in error for error in errors))

    def test_rejects_custom_agent_name_that_differs_from_filename(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("bad-agent-name")])
        self._write_portable_manifest("bad-agent-name")
        self._write_skill("bad-agent-name", "bad-agent-name")
        agent = self.root / "plugins/bad-agent-name/skills/bad-agent-name/agents/expected_agent.toml"
        agent.parent.mkdir(parents=True)
        agent.write_text('name = "different_agent"\n', encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(any("agent name must match filename 'expected_agent'" in error for error in errors))

    def test_rejects_non_mit_plugin_without_package_license(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("apache-plugin")])
        self._write_json(
            "plugins/apache-plugin/plugin.json",
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": "apache-plugin",
                "license": "Apache-2.0",
            },
        )
        self._write_skill("apache-plugin", "apache-plugin")

        errors = validate_repository(self.root)

        self.assertTrue(any("declares Apache-2.0 but has no package LICENSE" in error for error in errors))

    def test_rejects_code_simplifier_without_attribution_notice(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("code-simplifier")])
        self._write_code_simplifier_package(include_notice=False)

        errors = validate_repository(self.root)

        self.assertTrue(any("code-simplifier/NOTICE is missing" in error for error in errors))

    def test_rejects_code_simplifier_without_custom_agent(self) -> None:
        self._write_catalogs(codex_plugins=[self._codex_entry("code-simplifier")])
        self._write_code_simplifier_package(include_agent=False)

        errors = validate_repository(self.root)

        self.assertTrue(any("code_simplifier.toml is missing" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
