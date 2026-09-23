# SPDX-License-Identifier: GPL-3.0-only

import os
import unittest
from unittest.mock import patch

from velvet_interface.founder_surface_launcher import _owner_maintenance_unlocked
from velvet_interface.scenes.owner_maintenance_scene import OwnerMaintenanceScene


class _FakeRouter:
    def __init__(self, scenes=None):
        self.scenes = set(scenes or ())
        self.navigated = []
        self.back_calls = 0

    def list_scenes(self):
        return sorted(self.scenes)

    def navigate(self, scene_id):
        self.navigated.append(scene_id)
        return scene_id in self.scenes

    def back(self):
        self.back_calls += 1
        return True


class OwnerMaintenanceSceneTests(unittest.TestCase):
    def test_environment_gate_requires_owner_and_maintenance_together(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(_owner_maintenance_unlocked())
        with patch.dict(os.environ, {"VELVET_OWNER_PRESENT": "true"}, clear=True):
            self.assertFalse(_owner_maintenance_unlocked())
        with patch.dict(
            os.environ,
            {"VELVET_MAINTENANCE_UNLOCKED": "true"},
            clear=True,
        ):
            self.assertFalse(_owner_maintenance_unlocked())
        with patch.dict(
            os.environ,
            {
                "VELVET_OWNER_PRESENT": "true",
                "VELVET_MAINTENANCE_UNLOCKED": "true",
            },
            clear=True,
        ):
            self.assertTrue(_owner_maintenance_unlocked())

    def test_access_provider_exceptions_fail_closed(self):
        def broken_access():
            raise RuntimeError("missing owner evidence")

        scene = OwnerMaintenanceScene(
            access_provider=broken_access,
            physical_control_disabled_provider=lambda: True,
        )
        self.assertFalse(scene._has_access())

    def test_surface_studio_cannot_open_without_hidden_room_access(self):
        router = _FakeRouter({"surface_studio"})
        scene = OwnerMaintenanceScene(
            access_provider=lambda: False,
            physical_control_disabled_provider=lambda: True,
        )
        scene.bind_router(router)
        self.assertFalse(scene._open_surface_studio())
        self.assertEqual(router.navigated, [])

    def test_surface_studio_navigation_is_bounded_to_registered_scene(self):
        router = _FakeRouter({"surface_studio"})
        scene = OwnerMaintenanceScene(
            access_provider=lambda: True,
            physical_control_disabled_provider=lambda: True,
        )
        scene.bind_router(router)
        self.assertTrue(scene._open_surface_studio())
        self.assertEqual(router.navigated, ["surface_studio"])

    def test_display_title_can_be_localized_without_changing_scene_id(self):
        scene = OwnerMaintenanceScene(
            access_provider=lambda: True,
            physical_control_disabled_provider=lambda: True,
            display_title="Founder Private Label",
        )
        self.assertEqual(scene.scene_id, "owner_maintenance")
        self.assertEqual(scene.display_title, "Founder Private Label")


if __name__ == "__main__":
    unittest.main()
