# SPDX-License-Identifier: GPL-3.0-only

import ast
from pathlib import Path


def test_runtime_boot_window_parses_as_python38() -> None:
    source = Path("examples/runtime_boot_window.py").read_text(encoding="utf-8")
    ast.parse(source, filename="examples/runtime_boot_window.py", feature_version=(3, 8))
