# SPDX-License-Identifier: GPL-3.0-only

import unittest
from pathlib import Path

from velvet_interface.scene_system.yaml_loader import YAMLSceneLoader


TRUSTED_BUILT_IN_SCENES = {
    "character_foundry",
    "eleanor_engineering",
    "library_reader",
    "surface_studio",
    "velvets_legs",
    "written_conversation",
}

DEFERRED_SURFACES = {
    "forge_workspace": "compatibility-unrouted",
    "listen": "deferred-unrouted",
    "private": "deferred-owner-private",
    "silent": "deferred-unrouted",
}


class FounderSurfaceReachabilityTests(unittest.TestCase):
    def _load(self):
        root = Path(__file__).resolve().parents[1]
        return YAMLSceneLoader().load_multiple(
            str(root / "examples/surfaces"),
            require_background=True,
        )

    def test_every_manifest_navigation_target_resolves(self):
        documents = self._load()
        available = set(documents) | TRUSTED_BUILT_IN_SCENES
        for scene_name, scene in documents.items():
            for region in scene["regions"]:
                action = str(region["action"])
                if not action.startswith("navigate:"):
                    continue
                target = action.split(":", 1)[1]
                self.assertIn(
                    target,
                    available,
                    "%s routes to missing scene %s" % (scene_name, target),
                )

    def test_deferred_surfaces_are_retained_but_not_targeted(self):
        documents = self._load()
        navigation_targets = set()
        for scene in documents.values():
            for region in scene["regions"]:
                action = str(region["action"])
                if action.startswith("navigate:"):
                    navigation_targets.add(action.split(":", 1)[1])

        for scene_name, expected_status in DEFERRED_SURFACES.items():
            self.assertIn(scene_name, documents)
            self.assertNotIn(scene_name, navigation_targets)
            self.assertEqual(
                documents[scene_name]["metadata"]["navigation_status"],
                expected_status,
            )
            self.assertFalse(documents[scene_name]["metadata"]["physical_control"])

    def test_backroom_is_reachable_but_legs_is_not_a_manifest_route(self):
        documents = self._load()
        home_targets = {
            region["action"].split(":", 1)[1]
            for region in documents["founder_home"]["regions"]
            if region["action"].startswith("navigate:")
        }
        self.assertIn("backroom", home_targets)

        all_actions = {
            region["action"]
            for scene in documents.values()
            for region in scene["regions"]
        }
        self.assertNotIn("navigate:velvets_legs", all_actions)
        self.assertIn(
            "emit:backroom.hidden_owner_maintenance.selected",
            all_actions,
        )


if __name__ == "__main__":
    unittest.main()
