from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import sysconfig
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_PATH = PLUGIN_ROOT / "scripts/launch_mcp.py"
CLI_LAUNCHER_PATH = PLUGIN_ROOT / "scripts/papercuts"


def load_launcher():
    spec = importlib.util.spec_from_file_location("papercuts_launch_mcp", LAUNCHER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Papercuts MCP launcher")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PapercutsLauncherTests(unittest.TestCase):
    def test_cli_launcher_discovers_supported_versioned_python(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            output_path = root / "invocation.txt"

            dirname = bin_dir / "dirname"
            dirname.write_text(
                '#!/bin/sh\n[ "$1" = "--" ] && shift\nprintf "%s\\n" "${1%/*}"\n',
                encoding="utf-8",
            )
            dirname.chmod(0o755)

            for name in (
                "python3",
                "python3.14",
                "python3.13",
                "python3.12",
                "python3.11",
            ):
                old_python = bin_dir / name
                old_python.write_text(
                    '#!/bin/sh\n[ "$1" = "-c" ] && exit 1\nexit 99\n',
                    encoding="utf-8",
                )
                old_python.chmod(0o755)

            supported_python = root / "python3.42"
            supported_python.write_text(
                '#!/bin/sh\n[ "$1" = "-c" ] && exit 0\nprintf "%s\\n" "$@" > "$PAPERCUTS_TEST_OUTPUT"\n',
                encoding="utf-8",
            )
            supported_python.chmod(0o755)

            environment = dict(os.environ)
            environment["PATH"] = f"{bin_dir}{os.pathsep}"
            environment["PAPERCUTS_TEST_OUTPUT"] = str(output_path)
            result = subprocess.run(
                [str(CLI_LAUNCHER_PATH), "list", "--status", "open"],
                cwd=root,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                output_path.read_text(encoding="utf-8").splitlines(),
                ["-m", "papercuts.cli", "list", "--status", "open"],
            )

    def test_launcher_uses_native_paths_and_publishes_a_real_pip_cache(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache_root = root / "cache"
            server_environments: list[dict[str, str]] = []

            def run(command, **kwargs):
                if command[1:4] == ["-m", "pip", "install"]:
                    target = Path(command[command.index("--target") + 1])
                    (target / "mcp").mkdir()
                    return subprocess.CompletedProcess(command, 0)
                server_environments.append(kwargs["env"])
                return subprocess.CompletedProcess(command, 0)

            environment = {
                "PATH": os.environ.get("PATH", ""),
                "XDG_CACHE_HOME": str(cache_root),
                "PYTHONPATH": str(root / "existing"),
            }
            with (
                patch.object(launcher.shutil, "which", return_value=None),
                patch.object(launcher.subprocess, "run", side_effect=run),
            ):
                result = launcher.main(environment)

            python_tag = f"{sys.implementation.cache_tag}-{sysconfig.get_platform()}"
            dependency_dir = cache_root / f"papercuts/{python_tag}/mcp-2.1.1"
            self.assertEqual(result, 0)
            self.assertTrue((dependency_dir / ".installed").is_file())
            self.assertFalse(dependency_dir.is_symlink())
            self.assertEqual(len(server_environments), 1)
            self.assertEqual(
                server_environments[0]["PYTHONPATH"].split(os.pathsep),
                [
                    str(dependency_dir),
                    str(PLUGIN_ROOT / "src"),
                    str(root / "existing"),
                ],
            )

            uv_environments: list[dict[str, str]] = []

            def run_uv(command, **kwargs):
                uv_environments.append(kwargs["env"])
                return subprocess.CompletedProcess(command, 0)

            with (
                patch.object(launcher.shutil, "which", return_value=str(root / "uv")),
                patch.object(launcher.subprocess, "run", side_effect=run_uv),
            ):
                uv_result = launcher.main(environment)

            self.assertEqual(uv_result, 0)
            self.assertEqual(
                uv_environments[0]["PYTHONPATH"].split(os.pathsep),
                [str(PLUGIN_ROOT / "src"), str(root / "existing")],
            )

            for manifest_path, expected_argument in (
                (
                    PLUGIN_ROOT / ".claude-plugin/plugin.json",
                    "${CLAUDE_PLUGIN_ROOT}/scripts/launch_mcp.py",
                ),
                (
                    PLUGIN_ROOT / ".codex-plugin/plugin.json",
                    "./scripts/launch_mcp.py",
                ),
            ):
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                server = manifest["mcpServers"]["papercuts"]
                self.assertEqual(server["command"], "python3")
                self.assertEqual(server["args"], [expected_argument])

    def test_cache_publication_accepts_a_complete_winner_and_reports_other_errors(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private_dir = root / "private"
            dependency_dir = root / "mcp-2.1.1"
            private_dir.mkdir()
            dependency_dir.mkdir()
            (private_dir / ".installed").touch()
            (dependency_dir / ".installed").touch()

            launcher.publish_dependency_cache(private_dir, dependency_dir)

            self.assertFalse(private_dir.exists())
            self.assertTrue((dependency_dir / ".installed").is_file())

            failed_private_dir = root / "failed-private"
            failed_dependency_dir = root / "failed-dependency"
            failed_private_dir.mkdir()
            failed_dependency_dir.mkdir()
            (failed_dependency_dir / ".installed").touch()
            with patch.object(
                launcher.os,
                "rename",
                side_effect=PermissionError("publication denied"),
            ):
                with self.assertRaisesRegex(PermissionError, "publication denied"):
                    launcher.publish_dependency_cache(
                        failed_private_dir,
                        failed_dependency_dir,
                    )


if __name__ == "__main__":
    unittest.main()
