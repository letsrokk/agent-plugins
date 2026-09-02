#!/usr/bin/env python3
"""Run the Papercuts plugin test suite."""

from __future__ import annotations

import unittest
from pathlib import Path


def main() -> int:
    plugin_root = Path(__file__).resolve().parents[1]
    suite = unittest.defaultTestLoader.discover(str(plugin_root / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
