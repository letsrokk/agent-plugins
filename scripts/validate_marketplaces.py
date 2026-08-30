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


CODEX_CATALOG = Path(".agents/plugins/marketplace.json")
CLAUDE_CATALOG = Path(".claude-plugin/marketplace.json")
AGENT_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
CLAUDE_MARKETPLACE_SCHEMA = "https://json.schemastore.org/claude-code-marketplace.json"
PLUGIN_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")


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


def _validate_portable_manifest(root: Path, name: str, catalog: Path, errors: list[str]) -> None:
    relative_path = Path("plugins") / name / "plugin.json"
    manifest = _load_json(root, relative_path, errors)
    if manifest is None:
        if not (root / relative_path).exists():
            errors[-1] = f"{catalog}: plugin '{name}' is missing portable manifest {relative_path}"
        return
    if manifest.get("$schema") != AGENT_PLUGIN_SCHEMA:
        errors.append(f"{relative_path}: $schema must be {AGENT_PLUGIN_SCHEMA}")
    if manifest.get("name") != name:
        errors.append(f"{relative_path}: name must match catalog entry '{name}'")


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
        _validate_portable_manifest(root, name, catalog_path, errors)
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


def validate_repository(root: Path) -> list[str]:
    """Return all marketplace validation errors for *root*."""
    root = root.resolve()
    errors: list[str] = []
    _validate_codex_catalog(root, errors)
    _validate_claude_catalog(root, errors)
    _validate_agent_instructions(root, errors)
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
