#!/usr/bin/env python3
"""Validate and apply per-plugin release versions for a Git revision range."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
RUNTIME_VERSION = re.compile(
    r"^(__version__\s*=\s*)(['\"])([^'\"]+)\2(\s*(?:#.*)?)$",
    re.MULTILINE,
)


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: object, path: Path, errors: list[str]) -> Version | None:
        if not isinstance(value, str) or (match := SEMVER.fullmatch(value)) is None:
            errors.append(
                f"{path}: version {value!r} must use stable MAJOR.MINOR.PATCH SemVer"
            )
            return None
        return cls(*(int(part) for part in match.groups()))

    def bump_patch(self) -> Version:
        return Version(self.major, self.minor, self.patch + 1)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class PluginChange:
    name: str
    base_version: Version
    head_version: Version

    @property
    def has_explicit_version(self) -> bool:
        return self.head_version > self.base_version


class VersioningError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
    )


def _verify_revision(root: Path, revision: str, errors: list[str]) -> None:
    result = _git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")
    if result.returncode != 0:
        errors.append(f"invalid Git revision {revision!r}")


def _read_revision_file(root: Path, revision: str, path: Path) -> str | None:
    result = _git(root, "show", f"{revision}:{path.as_posix()}")
    return result.stdout if result.returncode == 0 else None


def _changed_plugin_names(root: Path, base: str, head: str) -> list[str]:
    result = _git(root, "diff", "--name-only", base, head, "--", "plugins/")
    if result.returncode != 0:
        raise VersioningError([result.stderr.strip() or "git diff failed"])
    names = {
        parts[1]
        for line in result.stdout.splitlines()
        if len(parts := Path(line).parts) >= 3 and parts[0] == "plugins"
    }
    return sorted(names)


def _json_version(text: str, path: Path, errors: list[str]) -> tuple[object, Version | None]:
    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError as error:
        errors.append(f"{path}: invalid JSON: {error.msg}")
        return None, None
    if not isinstance(payload, dict):
        errors.append(f"{path}: root value must be an object")
        return None, None
    value = payload.get("version")
    return value, Version.parse(value, path, errors)


def _runtime_version(text: str, path: Path, errors: list[str]) -> tuple[object, Version | None]:
    matches = list(RUNTIME_VERSION.finditer(text))
    if not matches:
        if "__version__" in text:
            errors.append(f"{path}: __version__ must be one plain string assignment")
        return None, None
    if len(matches) > 1:
        errors.append(f"{path}: __version__ must be one plain string assignment")
        return None, None
    value = matches[0].group(3)
    return value, Version.parse(value, path, errors)


def _manifest_paths(name: str) -> tuple[Path, Path, Path]:
    plugin_root = Path("plugins") / name
    return (
        plugin_root / "plugin.json",
        plugin_root / ".codex-plugin/plugin.json",
        plugin_root / ".claude-plugin/plugin.json",
    )


def _runtime_path(name: str) -> Path:
    return Path("plugins") / name / "src" / name.replace("-", "_") / "__init__.py"


def _validate_revision_surfaces(
    root: Path,
    revision: str,
    name: str,
    errors: list[str],
) -> Version | None:
    portable_path, *compatibility_paths = _manifest_paths(name)
    portable_text = _read_revision_file(root, revision, portable_path)
    if portable_text is None:
        errors.append(f"{portable_path}: portable manifest is missing at {revision}")
        return None
    portable_value, portable_version = _json_version(portable_text, portable_path, errors)

    for path in compatibility_paths:
        if (text := _read_revision_file(root, revision, path)) is None:
            continue
        value, _ = _json_version(text, path, errors)
        if value != portable_value:
            errors.append(
                f"{path}: version {value!r} must match portable manifest version {portable_value}"
            )

    runtime_path = _runtime_path(name)
    if (runtime_text := _read_revision_file(root, revision, runtime_path)) is not None:
        value, _ = _runtime_version(runtime_text, runtime_path, errors)
        if value is not None and value != portable_value:
            errors.append(
                f"{runtime_path}: version {value!r} must match portable manifest version "
                f"{portable_value}"
            )

    return portable_version


def analyze_changes(root: Path, base: str, head: str) -> list[PluginChange]:
    errors: list[str] = []
    _verify_revision(root, base, errors)
    _verify_revision(root, head, errors)
    if errors:
        raise VersioningError(errors)

    changes: list[PluginChange] = []
    for name in _changed_plugin_names(root, base, head):
        portable_path = _manifest_paths(name)[0]
        if _read_revision_file(root, head, portable_path) is None:
            continue

        head_version = _validate_revision_surfaces(root, head, name, errors)
        base_text = _read_revision_file(root, base, portable_path)
        if base_text is None:
            continue

        base_errors: list[str] = []
        _, base_version = _json_version(base_text, portable_path, base_errors)
        errors.extend(f"{error} at {base}" for error in base_errors)
        if base_version is None or head_version is None:
            continue
        if head_version < base_version:
            errors.append(
                f"plugins/{name}: version decreased from {base_version} to {head_version}"
            )
            continue
        changes.append(PluginChange(name, base_version, head_version))

    if errors:
        raise VersioningError(errors)
    return changes


def _load_worktree_version(root: Path, name: str, errors: list[str]) -> Version | None:
    portable_path, *compatibility_paths = _manifest_paths(name)
    try:
        portable_text = (root / portable_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    portable_value, portable_version = _json_version(portable_text, portable_path, errors)

    for path in compatibility_paths:
        try:
            text = (root / path).read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        value, _ = _json_version(text, path, errors)
        if value != portable_value:
            errors.append(
                f"{path}: version {value!r} must match portable manifest version {portable_value}"
            )

    runtime_path = _runtime_path(name)
    try:
        runtime_text = (root / runtime_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        pass
    else:
        value, _ = _runtime_version(runtime_text, runtime_path, errors)
        if value is not None and value != portable_value:
            errors.append(
                f"{runtime_path}: version {value!r} must match portable manifest version "
                f"{portable_value}"
            )
    return portable_version


def _write_json_version(path: Path, version: Version) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["version"] = str(version)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_runtime_version(path: Path, version: Version) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = RUNTIME_VERSION.subn(
        lambda match: f"{match.group(1)}{match.group(2)}{version}{match.group(2)}{match.group(4)}",
        text,
    )
    if count != 1:
        raise VersioningError([f"{path}: __version__ must be one plain string assignment"])
    path.write_text(updated, encoding="utf-8")


def _write_version_surfaces(root: Path, name: str, version: Version) -> None:
    for relative_path in _manifest_paths(name):
        path = root / relative_path
        if path.is_file():
            _write_json_version(path, version)
    runtime_path = root / _runtime_path(name)
    if runtime_path.is_file() and "__version__" in runtime_path.read_text(encoding="utf-8"):
        _write_runtime_version(runtime_path, version)


def apply_changes(root: Path, changes: list[PluginChange]) -> list[tuple[str, Version]]:
    errors: list[str] = []
    current_versions = {
        change.name: _load_worktree_version(root, change.name, errors) for change in changes
    }
    if errors:
        raise VersioningError(errors)

    updates: list[tuple[str, Version]] = []
    for change in changes:
        current = current_versions[change.name]
        if current is None:
            continue
        if current > change.head_version:
            continue
        if current < change.head_version:
            errors.append(
                f"plugins/{change.name}: current version {current} is older than event version "
                f"{change.head_version}; refusing to restore stale event version "
                f"{change.head_version}"
            )
            continue
        elif change.has_explicit_version:
            continue
        else:
            target = current.bump_patch()

        updates.append((change.name, target))

    if errors:
        raise VersioningError(errors)
    for name, target in updates:
        _write_version_surfaces(root, name, target)
    return updates


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "apply"))
    parser.add_argument("base", help="Git revision before the change")
    parser.add_argument("head", help="Git revision containing the change")
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    root = Path.cwd()
    try:
        changes = analyze_changes(root, arguments.base, arguments.head)
        if arguments.command == "check":
            print(f"Plugin version policy passed for {len(changes)} changed plugin(s).")
            return 0
        updates = apply_changes(root, changes)
    except VersioningError as error:
        for message in error.errors:
            print(message, file=sys.stderr)
        return 1

    if not updates:
        print("No plugin version changes required.")
        return 0
    for name, version in updates:
        print(f"{name}: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
