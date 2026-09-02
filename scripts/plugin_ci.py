#!/usr/bin/env python3
"""Select scripted plugins whose test and validation entrypoints CI must run."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


SHARED_CONTRACT_PATHS = {
    ".github/workflows/validate.yml",
    "AGENTS.md",
    "docs/plugin-development.md",
    "scripts/plugin_ci.py",
    "scripts/validate_marketplaces.py",
}


def is_scripted_plugin(plugin: Path) -> bool:
    """Return whether *plugin* contains repository-defined executable code."""
    if (plugin / "scripts").is_dir() or (plugin / "src").is_dir():
        return True
    skills = plugin / "skills"
    return skills.is_dir() and any(
        skill.is_dir() and (skill / "scripts").is_dir() for skill in skills.iterdir()
    )


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def all_scripted_plugins(root: Path) -> list[str]:
    plugins = root / "plugins"
    if not plugins.is_dir():
        return []
    return sorted(
        plugin.name for plugin in plugins.iterdir() if is_scripted_plugin(plugin)
    )


def changed_scripted_plugins(root: Path, base: str, head: str) -> list[str]:
    """Return scripted plugins affected between the merge base and *head*."""
    root = root.resolve()
    merge_base = _git(root, "merge-base", base, head).strip()
    changed_paths = {
        path
        for path in _git(root, "diff", "--name-only", "-z", merge_base, head).split("\0")
        if path
    }
    if changed_paths & SHARED_CONTRACT_PATHS:
        return all_scripted_plugins(root)

    names = {
        parts[1]
        for path in changed_paths
        if len(parts := Path(path).parts) >= 3 and parts[0] == "plugins"
    }
    return sorted(
        name for name in names if is_scripted_plugin(root / "plugins" / name)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    changed = subparsers.add_parser("changed", help="print affected plugin names as JSON")
    changed.add_argument("base")
    changed.add_argument("head")
    arguments = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    print(json.dumps(changed_scripted_plugins(root, arguments.base, arguments.head)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
