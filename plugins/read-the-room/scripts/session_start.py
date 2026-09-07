#!/usr/bin/env python3
"""Load the shared writing policy into a new or restored agent context."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> int:
    if sys.version_info < (3, 11):
        print("read-the-room hooks require Python 3.11 or later", file=sys.stderr)
        return 1

    skill = Path(__file__).resolve().parents[1] / "skills" / "make-it-make-sense"
    try:
        lines = (skill / "SKILL.md").read_text(encoding="utf-8").splitlines()
        if not lines or lines[0] != "---":
            raise ValueError("SKILL.md must start with YAML frontmatter")
        body = "\n".join(lines[lines.index("---", 1) + 1:]).strip()
        body = re.sub(
            r"\]\((references/[^)]+)\)",
            lambda match: f"](<{skill / match.group(1)}>)",
            body,
        )
        guide = (skill / "references" / "agent-responses.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"read-the-room could not load its writing policy: {error}", file=sys.stderr)
        return 1

    context = body + "\n\n" + guide.strip()
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
