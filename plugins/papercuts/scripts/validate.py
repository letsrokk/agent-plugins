#!/usr/bin/env python3
"""Validate Python source in the Papercuts plugin without writing bytecode."""

from __future__ import annotations

import sys
import tokenize
from pathlib import Path


def main() -> int:
    plugin_root = Path(__file__).resolve().parents[1]
    failed = False
    for directory in ("scripts", "src", "tests"):
        for path in sorted((plugin_root / directory).rglob("*.py")):
            try:
                with tokenize.open(path) as source:
                    compile(source.read(), str(path.relative_to(plugin_root)), "exec")
            except (OSError, SyntaxError, UnicodeError) as error:
                print(f"{path.relative_to(plugin_root)}: {error}", file=sys.stderr)
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
