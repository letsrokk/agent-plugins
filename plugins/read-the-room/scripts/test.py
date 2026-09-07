#!/usr/bin/env python3
"""Run the Read the Room plugin tests."""

import unittest
from pathlib import Path


plugin_root = Path(__file__).resolve().parents[1]
suite = unittest.defaultTestLoader.discover(str(plugin_root / "tests"))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
