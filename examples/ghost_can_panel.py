# SPDX-License-Identifier: GPL-3.0-only
"""Render the public-safe Ghost CAN panel as terminal text."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from velvet_interface.core.ghost_can_panel import render_ghost_can_text, view_model_from_ghost_can_event


def main() -> int:
    fixture = Path(__file__).parent / "fixtures" / "ghost_can_panel_event.json"
    event = json.loads(fixture.read_text(encoding="utf-8"))
    print(render_ghost_can_text(view_model_from_ghost_can_event(event)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
