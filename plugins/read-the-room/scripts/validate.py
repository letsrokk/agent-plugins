#!/usr/bin/env python3
"""Validate Python syntax and the packaged SessionStart configuration."""

import json
import re
import sys
import tokenize
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        for directory in ("scripts", "tests"):
            for path in sorted((root / directory).rglob("*.py")):
                with tokenize.open(path) as source:
                    compile(source.read(), str(path.relative_to(root)), "exec")
        config = json.loads((root / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        expected = {"hooks": {"SessionStart": [{"hooks": [{
            "type": "command",
            "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/session_start.py"',
            "timeout": 5,
        }]}]}}
        if config != expected:
            raise ValueError("hooks/hooks.json must register the shared synchronous SessionStart handler")
        if not (root / "scripts" / "session_start.py").is_file():
            raise ValueError("SessionStart handler is missing")
        skill = root / "skills" / "make-it-make-sense"
        policy = (skill / "SKILL.md").read_text(encoding="utf-8")
        (skill / "references" / "agent-responses.md").read_text(encoding="utf-8")
        for reference in re.findall(r"\]\((references/[^)]+)\)", policy):
            if not (skill / reference).is_file():
                raise ValueError(f"Missing channel reference: {reference}")
    except (OSError, SyntaxError, UnicodeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
