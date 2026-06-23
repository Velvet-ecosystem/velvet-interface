# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.boot_status import load_boot_snapshot, view_model_from_snapshot


class BootStatusTests(unittest.TestCase):
    def test_ready_snapshot_maps_to_visible_safe_state(self):
        model = view_model_from_snapshot(
            {
                "doctor": {"ready": True, "state": "ready", "checks": []},
                "service": {"active_state": "active", "sub_state": "running"},
                "route_count": 4,
            }
        )
        self.assertEqual(model.continuity, "VERIFIED")
        self.assertEqual(model.court, "READY")
        self.assertEqual(model.runtime, "ACTIVE")
        self.assertEqual(model.routes, "4 READ-ONLY")
        self.assertEqual(model.physical_control, "DISABLED")
        self.assertEqual(model.message, "Waiting for Mister")

    def test_blocked_snapshot_surfaces_exact_reason(self):
        model = view_model_from_snapshot(
            {
                "doctor": {
                    "ready": False,
                    "state": "blocked",
                    "checks": [{"name": "continuity", "ok": False, "detail": "signature mismatch"}],
                },
                "service": {"active_state": "failed", "sub_state": "failed"},
            }
        )
        self.assertEqual(model.court, "BLOCKED")
        self.assertIn("signature mismatch", model.message)
        self.assertEqual(model.physical_control, "DISABLED")

    def test_missing_snapshot_fails_visible_and_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = load_boot_snapshot(Path(tmp) / "missing.json")
        self.assertEqual(model.court, "BLOCKED")
        self.assertIn("not found", model.message.lower())
        self.assertEqual(model.physical_control, "DISABLED")

    def test_invalid_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshot.json"
            path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
            model = load_boot_snapshot(path)
        self.assertEqual(model.continuity, "SNAPSHOT_INVALID")
        self.assertEqual(model.court, "BLOCKED")


if __name__ == "__main__":
    unittest.main()
