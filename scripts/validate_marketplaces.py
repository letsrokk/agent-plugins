#!/usr/bin/env python3
"""Validate the Rokk Club marketplace catalogs and referenced plugins."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

if __package__:
    from .plugin_ci import is_scripted_plugin
else:
    from plugin_ci import is_scripted_plugin

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    tomllib = None


CODEX_CATALOG = Path(".agents/plugins/marketplace.json")
CLAUDE_CATALOG = Path(".claude-plugin/marketplace.json")
AGENT_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
CLAUDE_MARKETPLACE_SCHEMA = "https://json.schemastore.org/claude-code-marketplace.json"
PLUGIN_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")
PORTABLE_MANIFEST_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
STRING_MANIFEST_FIELDS = {
    "version",
    "description",
    "homepage",
    "repository",
    "license",
}
AUTHOR_FIELDS = {"name", "email", "url"}
UPSTREAM_CODE_SIMPLIFIER = (
    "https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier"
)


def _load_json(root: Path, relative_path: Path, errors: list[str]) -> dict[str, Any] | None:
    path = root / relative_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{relative_path}: file is missing")
        return None
    except json.JSONDecodeError as error:
        errors.append(f"{relative_path}: invalid JSON: {error.msg}")
        return None

    if not isinstance(payload, dict):
        errors.append(f"{relative_path}: root value must be an object")
        return None
    return payload


def _valid_plugin_name(name: object) -> bool:
    return (
        isinstance(name, str)
        and PLUGIN_NAME.fullmatch(name) is not None
        and "--" not in name
        and ".." not in name
    )


def _validate_manifest_metadata(
    relative_path: Path, manifest: dict[str, Any], errors: list[str]
) -> None:
    for field in sorted(manifest.keys() - PORTABLE_MANIFEST_FIELDS):
        errors.append(f"{relative_path}: unknown field '{field}'")

    for field in sorted(STRING_MANIFEST_FIELDS):
        if field in manifest and not isinstance(manifest[field], str):
            errors.append(f"{relative_path}: {field} must be a string")

    author = manifest.get("author")
    if author is not None:
        if not isinstance(author, dict):
            errors.append(f"{relative_path}: author must be an object")
        else:
            for field in sorted(author.keys() - AUTHOR_FIELDS):
                errors.append(f"{relative_path}: author has unknown field '{field}'")
            for field, value in author.items():
                if field in AUTHOR_FIELDS and not isinstance(value, str):
                    errors.append(f"{relative_path}: author.{field} must be a string")

    keywords = manifest.get("keywords")
    if keywords is not None and (
        not isinstance(keywords, list) or any(not isinstance(keyword, str) for keyword in keywords)
    ):
        errors.append(f"{relative_path}: keywords must be an array of strings")

    extensions = manifest.get("extensions")
    if extensions is not None and (
        not isinstance(extensions, dict)
        or any(not isinstance(value, dict) for value in extensions.values())
    ):
        errors.append(f"{relative_path}: extensions must map namespaces to objects")


def _skill_frontmatter_name(path: Path, relative_path: Path, errors: list[str]) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        errors.append(f"{relative_path}: must be UTF-8 text")
        return None
    if not lines or lines[0] != "---":
        errors.append(f"{relative_path}: must start with YAML frontmatter")
        return None
    try:
        closing = lines.index("---", 1)
    except ValueError:
        errors.append(f"{relative_path}: YAML frontmatter is not closed")
        return None
    for line in lines[1:closing]:
        match = re.fullmatch(r"name:\s*([^#]+?)\s*", line)
        if match:
            return match.group(1).strip("'\"")
    errors.append(f"{relative_path}: YAML frontmatter must define name")
    return None


def _validate_custom_agents(
    root: Path, skill_directory: Path, relative_skill: Path, errors: list[str]
) -> None:
    agents = skill_directory / "agents"
    if not agents.exists():
        return
    if not agents.is_dir():
        errors.append(f"{relative_skill / 'agents'}: must be a directory")
        return
    if tomllib is None:
        errors.append(
            f"{relative_skill / 'agents'}: custom-agent TOML validation requires Python 3.11 or later"
        )
        return
    for agent in sorted(agents.glob("*.toml")):
        relative_agent = agent.relative_to(root)
        try:
            payload = tomllib.loads(agent.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            errors.append(f"{relative_agent}: invalid TOML: {error}")
            continue
        if payload.get("name") != agent.stem:
            errors.append(f"{relative_agent}: agent name must match filename '{agent.stem}'")


def _validate_plugin_components(root: Path, name: str, errors: list[str]) -> None:
    plugin = root / "plugins" / name
    skills = plugin / "skills"
    mcp = plugin / "mcp.json"
    discovered_skills = 0

    if skills.exists():
        if not skills.is_dir():
            errors.append(f"plugins/{name}/skills: must be a directory")
        else:
            for skill_directory in sorted(path for path in skills.iterdir() if path.is_dir()):
                skill_file = skill_directory / "SKILL.md"
                if not skill_file.is_file():
                    continue
                discovered_skills += 1
                relative_skill = skill_directory.relative_to(root)
                relative_file = skill_file.relative_to(root)
                skill_name = _skill_frontmatter_name(skill_file, relative_file, errors)
                if skill_name is not None and skill_name != skill_directory.name:
                    errors.append(
                        f"{relative_file}: skill name must match directory '{skill_directory.name}'"
                    )
                _validate_custom_agents(root, skill_directory, relative_skill, errors)

    has_mcp = mcp.is_file()
    if discovered_skills == 0 and not has_mcp:
        errors.append(f"plugins/{name}: must provide at least one skill or mcp.json")

def _validate_code_simplifier(root: Path, errors: list[str]) -> None:
    plugin = root / "plugins/code-simplifier"
    skill = plugin / "skills/code-simplifier"
    notice = plugin / "NOTICE"
    license_file = plugin / "LICENSE"
    skill_file = skill / "SKILL.md"
    interface = skill / "agents/openai.yaml"
    agent = skill / "agents/code_simplifier.toml"

    if not notice.is_file():
        errors.append("plugins/code-simplifier/NOTICE is missing")
    else:
        text = notice.read_text(encoding="utf-8")
        for marker in ("Anthropic", "Rokk Club", "adapt", UPSTREAM_CODE_SIMPLIFIER):
            if marker not in text:
                errors.append(f"plugins/code-simplifier/NOTICE: missing attribution marker '{marker}'")

    if license_file.is_file():
        text = license_file.read_text(encoding="utf-8")
        if "Apache License" not in text or "Version 2.0" not in text:
            errors.append("plugins/code-simplifier/LICENSE: must contain Apache License 2.0")

    if skill_file.is_file():
        text = skill_file.read_text(encoding="utf-8")
        if "Anthropic's Code Simplifier" not in text or "code_simplifier" not in text:
            errors.append("plugins/code-simplifier/skills/code-simplifier/SKILL.md: adaptation notice is missing")
    interface_text = interface.read_text(encoding="utf-8") if interface.is_file() else ""
    if re.search(r"^\s*display_name:\s*['\"]?Code Simplifier['\"]?\s*$", interface_text, re.M) is None:
        errors.append(
            "plugins/code-simplifier/skills/code-simplifier/agents/openai.yaml: "
            "Code Simplifier interface metadata is missing"
        )
    if not agent.is_file():
        errors.append(
            "plugins/code-simplifier/skills/code-simplifier/agents/code_simplifier.toml is missing"
        )
    elif "Adapted from Anthropic's Code Simplifier" not in agent.read_text(encoding="utf-8"):
        errors.append(
            "plugins/code-simplifier/skills/code-simplifier/agents/code_simplifier.toml: "
            "adaptation notice is missing"
        )


def _validate_portable_manifest(
    root: Path, name: str, catalog: Path, errors: list[str]
) -> dict[str, Any] | None:
    relative_path = Path("plugins") / name / "plugin.json"
    manifest = _load_json(root, relative_path, errors)
    if manifest is None:
        if not (root / relative_path).exists():
            errors[-1] = f"{catalog}: plugin '{name}' is missing portable manifest {relative_path}"
        return None
    if manifest.get("$schema") != AGENT_PLUGIN_SCHEMA:
        errors.append(f"{relative_path}: $schema must be {AGENT_PLUGIN_SCHEMA}")
    if manifest.get("name") != name:
        errors.append(f"{relative_path}: name must match catalog entry '{name}'")
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        errors.append(f"{relative_path}: version must be a non-empty string")
    _validate_manifest_metadata(relative_path, manifest, errors)
    _validate_plugin_components(root, name, errors)

    license_name = manifest.get("license")
    if isinstance(license_name, str) and license_name != "MIT":
        if not (root / "plugins" / name / "LICENSE").is_file():
            errors.append(
                f"plugins/{name}: declares {license_name} but has no package LICENSE"
            )
    if name == "code-simplifier":
        _validate_code_simplifier(root, errors)
    return manifest


def _validate_codex_manifest(
    root: Path, name: str, portable_manifest: dict[str, Any], errors: list[str]
) -> None:
    relative_path = Path("plugins") / name / ".codex-plugin/plugin.json"
    manifest = _load_json(root, relative_path, errors)
    if manifest is None:
        if not (root / relative_path).exists():
            errors[-1] = (
                f"{CODEX_CATALOG}: plugin '{name}' is missing Codex compatibility manifest "
                f"{relative_path}"
            )
        return

    if manifest.get("name") != name:
        errors.append(f"{relative_path}: name must match catalog entry '{name}'")
    portable_version = portable_manifest.get("version")
    if isinstance(portable_version, str) and portable_version:
        if manifest.get("version") != portable_version:
            errors.append(
                f"{relative_path}: version must match portable manifest '{portable_version}'"
            )

    skills_directory = root / "plugins" / name / "skills"
    has_discoverable_skill = skills_directory.is_dir() and any(
        child.is_dir() and (child / "SKILL.md").is_file() for child in skills_directory.iterdir()
    )
    if has_discoverable_skill:
        if manifest.get("skills") != "./skills/":
            errors.append(f"{relative_path}: skills must be './skills/'")
    elif "skills" in manifest:
        errors.append(f"{relative_path}: skills must be omitted when no skills are present")


def _validate_claude_manifest(root: Path, name: str, errors: list[str]) -> None:
    relative_path = Path("plugins") / name / ".claude-plugin/plugin.json"
    manifest = _load_json(root, relative_path, errors)
    if manifest is None:
        if not (root / relative_path).exists():
            errors[-1] = (
                f"{CLAUDE_CATALOG}: plugin '{name}' is missing Claude compatibility manifest "
                f"{relative_path}"
            )
        return
    if manifest.get("name") != name:
        errors.append(f"{relative_path}: name must match catalog entry '{name}'")


def _validate_plugins(
    root: Path,
    catalog_path: Path,
    plugins: object,
    source_path: Callable[[dict[str, Any]], object],
    errors: list[str],
    *,
    require_codex_manifest: bool = False,
    require_claude_manifest: bool = False,
    validate_entry: Callable[[str, dict[str, Any], list[str]], None] | None = None,
) -> None:
    if not isinstance(plugins, list):
        errors.append(f"{catalog_path}: plugins must be an array")
        return

    seen: set[str] = set()
    for index, entry in enumerate(plugins):
        prefix = f"{catalog_path}: plugins[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue

        name = entry.get("name")
        if not _valid_plugin_name(name):
            errors.append(f"{prefix}.name is not a valid Agent Plugins name")
            continue
        if name in seen:
            errors.append(f"{catalog_path}: duplicate plugin name '{name}'")
        seen.add(name)

        if validate_entry is not None:
            validate_entry(prefix, entry, errors)

        expected_path = f"./plugins/{name}"
        actual_path = source_path(entry)
        if actual_path != expected_path:
            errors.append(f"{prefix}.source must be '{expected_path}'")
            continue

        plugin_directory = root / "plugins" / name
        if not plugin_directory.is_dir():
            errors.append(f"{catalog_path}: plugin '{name}' directory is missing")
            continue
        portable_manifest = _validate_portable_manifest(root, name, catalog_path, errors)
        if require_codex_manifest and portable_manifest is not None:
            _validate_codex_manifest(root, name, portable_manifest, errors)
        if require_claude_manifest:
            _validate_claude_manifest(root, name, errors)


def _codex_source(entry: dict[str, Any]) -> object:
    source = entry.get("source")
    if not isinstance(source, dict) or source.get("source") != "local":
        return None
    return source.get("path")


def _claude_source(entry: dict[str, Any]) -> object:
    return entry.get("source")


def _validate_codex_entry(prefix: str, entry: dict[str, Any], errors: list[str]) -> None:
    policy = entry.get("policy")
    if not isinstance(policy, dict) or policy.get("installation") != "AVAILABLE":
        errors.append(f"{prefix}.policy.installation must be 'AVAILABLE'")
    if not isinstance(policy, dict) or policy.get("authentication") != "ON_INSTALL":
        errors.append(f"{prefix}.policy.authentication must be 'ON_INSTALL'")
    category = entry.get("category")
    if not isinstance(category, str) or not category.strip():
        errors.append(f"{prefix}.category must be a non-empty string")


def _validate_codex_catalog(root: Path, errors: list[str]) -> None:
    catalog = _load_json(root, CODEX_CATALOG, errors)
    if catalog is None:
        return
    if catalog.get("name") != "rokk-club-codex-plugins":
        errors.append(f"{CODEX_CATALOG}: name must be 'rokk-club-codex-plugins'")
    if catalog.get("interface") != {"displayName": "Rokk Club Codex Plugins"}:
        errors.append(f"{CODEX_CATALOG}: interface.displayName must be 'Rokk Club Codex Plugins'")
    _validate_plugins(
        root,
        CODEX_CATALOG,
        catalog.get("plugins"),
        _codex_source,
        errors,
        require_codex_manifest=True,
        validate_entry=_validate_codex_entry,
    )


def _validate_claude_catalog(root: Path, errors: list[str]) -> None:
    catalog = _load_json(root, CLAUDE_CATALOG, errors)
    if catalog is None:
        return
    if catalog.get("$schema") != CLAUDE_MARKETPLACE_SCHEMA:
        errors.append(f"{CLAUDE_CATALOG}: $schema must be {CLAUDE_MARKETPLACE_SCHEMA}")
    if catalog.get("name") != "rokk-club-claude-plugins":
        errors.append(f"{CLAUDE_CATALOG}: name must be 'rokk-club-claude-plugins'")
    if catalog.get("owner") != {"name": "Rokk Club"}:
        errors.append(f"{CLAUDE_CATALOG}: owner.name must be 'Rokk Club'")
    _validate_plugins(
        root,
        CLAUDE_CATALOG,
        catalog.get("plugins"),
        _claude_source,
        errors,
        require_claude_manifest=True,
    )


def _validate_agent_instructions(root: Path, errors: list[str]) -> None:
    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    if not agents.is_file():
        errors.append("AGENTS.md is missing")
    if not claude.is_symlink() or os.readlink(claude) != "AGENTS.md":
        errors.append("CLAUDE.md must be a symlink to AGENTS.md")


def _validate_scripted_plugins(root: Path, errors: list[str]) -> None:
    plugins = root / "plugins"
    if not plugins.is_dir():
        return
    for plugin in sorted(path for path in plugins.iterdir() if path.is_dir()):
        if not is_scripted_plugin(plugin):
            continue
        for entrypoint in ("test.py", "validate.py"):
            if not (plugin / "scripts" / entrypoint).is_file():
                errors.append(f"plugins/{plugin.name}/scripts/{entrypoint} is missing")


def validate_repository(root: Path) -> list[str]:
    """Return all marketplace validation errors for *root*."""
    root = root.resolve()
    errors: list[str] = []
    _validate_codex_catalog(root, errors)
    _validate_claude_catalog(root, errors)
    _validate_agent_instructions(root, errors)
    _validate_scripted_plugins(root, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repository",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of this script)",
    )
    arguments = parser.parse_args(argv)
    errors = validate_repository(arguments.repository)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("Marketplace validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
