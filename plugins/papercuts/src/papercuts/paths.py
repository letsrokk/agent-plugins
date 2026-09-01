from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Literal, Mapping
from urllib.parse import urlsplit

from papercuts.models import (
    Client,
    PapercutsError,
    ProjectRef,
    Scope,
    StorageContext,
    filesystem_error,
)

_CONFIG_NAME = "papercuts.config.json"
_JOURNAL_NAME = "papercuts.jsonl"
_SCOPE_VALUES = {"project", "user"}
_CLIENT_VALUES = {"codex", "claude"}


def resolve_client(
    explicit: str | None,
    environ: Mapping[str, str] | None = None,
) -> Client:
    """Resolve the selected client from an explicit value, environment, or default."""
    if explicit is not None:
        if explicit not in _CLIENT_VALUES:
            raise ValueError(f"unknown client: {explicit}")
        return explicit  # type: ignore[return-value]

    environment = os.environ if environ is None else environ
    selected = environment.get("PAPERCUTS_CLIENT", "codex")
    if selected not in _CLIENT_VALUES:
        raise PapercutsError(
            "invalid_config",
            "PAPERCUTS_CLIENT must be codex or claude",
            exit_status=78,
        )
    return selected  # type: ignore[return-value]


def discover_project(cwd: Path) -> tuple[Path, str | None]:
    """Return the Git worktree root and sanitized remote input, or cwd and None."""
    try:
        root_result = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return cwd, None
    except OSError as error:
        raise filesystem_error("discover Git project", cwd, error) from error
    if root_result.returncode != 0:
        return cwd, None

    root = Path(root_result.stdout.strip())
    try:
        remote_result = subprocess.run(
            ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return root, None
    except OSError as error:
        raise filesystem_error("discover Git remote", root, error) from error
    remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else None
    return root, remote_url or None


def project_ref(root: Path, remote_url: str | None) -> ProjectRef:
    """Hash normalized remote identity, falling back to the canonical root."""
    identity = _normalize_remote(remote_url) if remote_url else None
    if identity is None:
        identity = str(root.resolve())
    digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
    return ProjectRef(id=f"prj_{digest}", name=root.resolve().name)


def resolve_storage(
    cwd: Path,
    *,
    client: Client = "codex",
    explicit_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    project_root: Path | None = None,
    remote_url: str | None = None,
) -> StorageContext:
    """Apply explicit file, environment, project config, user config, default precedence."""
    discovered_root: Path | None = None
    discovered_remote: str | None = None
    if project_root is None or remote_url is None:
        discovered_root, discovered_remote = discover_project(cwd)

    root = project_root or discovered_root or cwd
    remote = remote_url if remote_url is not None else discovered_remote
    resolved_home = home if home is not None else Path.home()
    project = project_ref(root, remote)

    if explicit_file is not None:
        return StorageContext(project, root, explicit_file, "project", None, client)

    environment = os.environ if environ is None else environ
    environment_file = environment.get("PAPERCUTS_FILE")
    if environment_file:
        journal_path = Path(environment_file)
        if not journal_path.is_absolute():
            journal_path = cwd / journal_path
        return StorageContext(project, root, journal_path, "project", None, client)

    project_config = _config_path(root, client)
    project_scope = _read_scope(project_config)
    if project_scope is not None:
        return _storage_context(
            project, root, resolved_home, project_scope, project_config, client
        )

    user_config = _config_path(resolved_home, client)
    user_scope = _read_scope(user_config)
    if user_scope is not None:
        return _storage_context(
            project, root, resolved_home, user_scope, user_config, client
        )

    return _storage_context(project, root, resolved_home, "project", None, client)


def set_scope(
    cwd: Path,
    scope: Scope,
    level: Literal["project", "user"],
    *,
    client: Client = "codex",
    home: Path | None = None,
) -> Path:
    """Atomically write one scope configuration and return its path."""
    if scope not in _SCOPE_VALUES:
        raise ValueError(f"unknown scope: {scope}")
    if level not in {"project", "user"}:
        raise ValueError(f"unknown configuration level: {level}")

    root, _ = discover_project(cwd)
    config_path = _config_path(
        root if level == "project" else home or Path.home(),
        client,
    )
    temporary_path: Path | None = None
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=config_path.parent,
            prefix=f".{config_path.name}.",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump({"scope": scope}, temporary_file)
            temporary_file.write("\n")
        os.replace(temporary_path, config_path)
        temporary_path = None
    except OSError as error:
        raise filesystem_error(
            "write Papercuts configuration",
            config_path,
            error,
        ) from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass
    return config_path


def _normalize_remote(remote_url: str) -> str | None:
    remote = remote_url.strip()
    if not remote:
        return None

    if re.match(r"^[^/@\s]+@[^/:\s]+:", remote):
        host, path = remote.split("@", 1)[1].split(":", 1)
    else:
        parsed = urlsplit(remote)
        host = parsed.hostname
        path = parsed.path
        if host is None:
            return None

    path = path.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    path = path.strip("/")
    return f"{host.lower()}/{path}" if path else host.lower()


def _config_path(base: Path, client: Client) -> Path:
    return base / f".{client}" / _CONFIG_NAME


def _read_scope(path: Path) -> Scope | None:
    try:
        with path.open(encoding="utf-8") as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as error:
        raise PapercutsError(
            "invalid_config",
            f"Invalid Papercuts configuration: {path}",
            exit_status=78,
        ) from error
    except OSError as error:
        raise filesystem_error(
            "read Papercuts configuration",
            path,
            error,
        ) from error

    scope = config.get("scope") if isinstance(config, dict) else None
    if (
        not isinstance(config, dict)
        or set(config) != {"scope"}
        or not isinstance(scope, str)
        or scope not in _SCOPE_VALUES
    ):
        raise PapercutsError(
            "invalid_config",
            f"Invalid Papercuts configuration: {path}",
            exit_status=78,
        )
    return scope


def _storage_context(
    project: ProjectRef,
    root: Path,
    home: Path,
    scope: Scope,
    config_source: Path | None,
    client: Client,
) -> StorageContext:
    journal_base = root if scope == "project" else home
    return StorageContext(
        project=project,
        project_root=root,
        journal_path=journal_base / f".{client}" / _JOURNAL_NAME,
        scope=scope,
        config_source=config_source,
        client=client,
    )
