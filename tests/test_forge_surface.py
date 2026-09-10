from pathlib import Path
import unittest

import yaml


class ForgeSurfaceTests(unittest.TestCase):
    def test_forge_surface_uses_new_artwork_and_waits_for_mapped_tool_points(self):
        path = Path("examples/surfaces/forge.surface.yaml")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(document["name"], "forge")
        self.assertEqual(document["background"]["image"], "../assets/forge.png")
        self.assertEqual(
            [point["id"] for point in document["press_points"]],
            ["return_home", "emergency"],
        )
        self.assertEqual(document["metadata"]["physical_control"], "disabled")
        self.assertIn("placement mapping", document["metadata"]["implementation_status"])

    def test_reusable_workspace_scroll_asset_exists(self):
        self.assertTrue(Path("examples/assets/workspace_scroll.png").is_file())
        self.assertTrue(Path("examples/assets/forge.png").is_file())


if __name__ == "__main__":
    unittest.main()
