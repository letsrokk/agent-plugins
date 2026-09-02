#!/usr/bin/env python3
from __future__ import annotations

import errno
import os
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path
from typing import Mapping


MCP_VERSION = "2.1.1"
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SAFE_TAG = re.compile(r"^[A-Za-z0-9._-]+$")


def publish_dependency_cache(private_dir: Path, dependency_dir: Path) -> None:
    try:
        os.rename(private_dir, dependency_dir)
    except OSError as error:
        if error.errno not in {errno.EEXIST, errno.ENOTEMPTY} or not (
            dependency_dir / ".installed"
        ).is_file():
            raise
        shutil.rmtree(private_dir)


def _pythonpath(paths: list[Path], environment: Mapping[str, str]) -> str:
    entries = [str(path) for path in paths]
    inherited = environment.get("PYTHONPATH")
    if inherited:
        entries.append(inherited)
    return os.pathsep.join(entries)


def _cache_root(environment: Mapping[str, str]) -> Path:
    configured = environment.get("XDG_CACHE_HOME")
    if configured and Path(configured).is_absolute():
        return Path(configured)
    home = environment.get("HOME")
    resolved_home = Path(home) if home and Path(home).is_absolute() else Path.home()
    return resolved_home / ".cache"


def _run(command: list[str], environment: dict[str, str]) -> int:
    return subprocess.run(command, env=environment, check=False).returncode


def main(environ: Mapping[str, str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print("papercuts MCP requires Python 3.11 or later", file=sys.stderr)
        return 78

    environment = dict(os.environ if environ is None else environ)
    source_dir = PLUGIN_ROOT / "src"
    uv = shutil.which("uv", path=environment.get("PATH"))
    if uv is not None:
        environment["PYTHONPATH"] = _pythonpath([source_dir], environment)
        try:
            return _run(
                [
                    uv,
                    "run",
                    "--quiet",
                    "--with",
                    f"mcp=={MCP_VERSION}",
                    "--",
                    "python",
                    "-m",
                    "papercuts.mcp_server",
                ],
                environment,
            )
        except OSError as error:
            print(f"papercuts MCP could not start uv: {error}", file=sys.stderr)
            return 78

    python_tag = f"{sys.implementation.cache_tag}-{sysconfig.get_platform()}"
    if not SAFE_TAG.fullmatch(python_tag):
        print(
            "papercuts MCP could not determine a safe Python cache tag",
            file=sys.stderr,
        )
        return 78

    dependency_parent = _cache_root(environment) / "papercuts" / python_tag
    dependency_dir = dependency_parent / f"mcp-{MCP_VERSION}"
    installed_marker = dependency_dir / ".installed"
    private_dir: Path | None = None
    try:
        if not installed_marker.is_file():
            dependency_parent.mkdir(parents=True, exist_ok=True)
            private_dir = Path(
                tempfile.mkdtemp(
                    prefix=f".mcp-{MCP_VERSION}.",
                    dir=dependency_parent,
                )
            )
            install_result = _run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--quiet",
                    "--upgrade",
                    "--target",
                    str(private_dir),
                    f"mcp=={MCP_VERSION}",
                ],
                environment,
            )
            if install_result != 0:
                print(
                    f"papercuts MCP could not install mcp=={MCP_VERSION} with pip",
                    file=sys.stderr,
                )
                return 78
            (private_dir / ".installed").touch()
            publish_dependency_cache(private_dir, dependency_dir)
            private_dir = None
    except OSError as error:
        print(
            f"papercuts MCP could not publish its dependency cache: {error}",
            file=sys.stderr,
        )
        return 78
    finally:
        if private_dir is not None:
            shutil.rmtree(private_dir, ignore_errors=True)

    environment["PYTHONPATH"] = _pythonpath(
        [dependency_dir, source_dir],
        environment,
    )
    try:
        return _run(
            [sys.executable, "-m", "papercuts.mcp_server"],
            environment,
        )
    except OSError as error:
        print(f"papercuts MCP could not start Python: {error}", file=sys.stderr)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
