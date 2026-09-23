# SPDX-License-Identifier: GPL-3.0-only

import unittest
from pathlib import Path


class FounderHiddenMaintenanceWiringTests(unittest.TestCase):
    def test_launcher_binds_backroom_event_to_double_gated_scene(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "velvet_interface/founder_surface_launcher.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("def _owner_maintenance_unlocked()", source)
        self.assertIn('"VELVET_OWNER_PRESENT") and _env_true(', source)
        self.assertIn('"VELVET_MAINTENANCE_UNLOCKED"', source)
        self.assertIn('"backroom.hidden_owner_maintenance.selected"', source)
        self.assertIn('router.navigate("velvets_legs")', source)
        self.assertIn("VelvetsLegsScene", source)
        self.assertIn('"velvets_legs",', source)

    def test_hidden_room_is_not_a_fallback_initial_scene(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "velvet_interface/founder_surface_launcher.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('initial = "velvets_legs"', source)


if __name__ == "__main__":
    unittest.main()
