import tempfile
import unittest
from pathlib import Path

from velvet_interface.scene_system.authoring import SurfaceLayoutAuthoringSession
from velvet_interface.scene_system.image_scene import ImageScene
from velvet_interface.scene_system.scaling import SceneScaler
from velvet_interface.scene_system.surface_manifest import SurfaceManifestLoader


class SurfaceScalingTests(unittest.TestCase):
    def test_contain_centers_image_and_reverses_points(self):
        scaler = SceneScaler(
            base_resolution=(1000, 500),
            target_resolution=(1000, 1000),
            fit_mode="contain",
        )
        self.assertEqual(scaler.get_letterbox_rect(), (0, 250, 1000, 500))
        self.assertEqual(scaler.scale_point(500, 250), (500.0, 500.0))
        self.assertEqual(scaler.unscale_point(500, 500), (500.0, 250.0))
        self.assertFalse(scaler.contains_target_point(500, 100))

    def test_cover_crops_symmetrically(self):
        scaler = SceneScaler(
            base_resolution=(1000, 500),
            target_resolution=(500, 500),
            fit_mode="cover",
        )
        self.assertEqual(scaler.get_letterbox_rect(), (-250, 0, 1000, 500))
        self.assertEqual(scaler.normalized_target_point(250, 250), (0.5, 0.5))

    def test_resized_press_point_uses_one_transform(self):
        scene = ImageScene(
            {
                "name": "home",
                "base_resolution": [1000, 500],
                "background": "home.png",
                "background_fit": "contain",
                "regions": [
                    {
                        "name": "drive",
                        "polygon": [[100, 100], [300, 100], [300, 200], [100, 200]],
                        "action": "navigate:drive",
                        "enabled": True,
                    }
                ],
                "widgets": [
                    {
                        "widget_id": "status",
                        "rect": [700, 50, 200, 100],
                    }
                ],
            }
        )
        scene.setup_scaling((500, 500))

        # Base point (200, 150) becomes target point (100, 325) after contain.
        self.assertEqual(scene.handle_click(100, 325), "navigate:drive")
        self.assertIsNone(scene.handle_click(100, 100))
        self.assertEqual(scene.widget_rect(scene.widget_placements[0]), (350, 275, 100, 50))

    def test_disabled_press_point_is_not_actionable(self):
        scene = ImageScene(
            {
                "name": "home",
                "base_resolution": [100, 100],
                "background": "home.png",
                "regions": [
                    {
                        "name": "hidden",
                        "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]],
                        "action": "navigate:hidden",
                        "enabled": False,
                    }
                ],
            }
        )
        scene.setup_scaling((100, 100))
        self.assertIsNone(scene.handle_click(50, 50))


class SurfaceAuthoringTests(unittest.TestCase):
    def test_capture_press_point_and_widget_as_normalized_geometry(self):
        session = SurfaceLayoutAuthoringSession(
            name="home",
            background_path="/tmp/home.png",
            base_resolution=(1000, 500),
            fit_mode="contain",
        )
        press = session.add_press_point_from_target(
            "drive",
            "navigate:drive",
            [(100, 300), (300, 300), (300, 400), (100, 400)],
            (1000, 1000),
        )
        widget = session.add_widget_from_target(
            "status",
            (700, 300, 200, 100),
            (1000, 1000),
        )

        self.assertEqual(press.polygon[0], (0.1, 0.1))
        self.assertEqual(widget.rect, (0.7, 0.1, 0.2, 0.2))

    def test_authoring_round_trip_yaml(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "home.png"
            image.write_bytes(b"asset")
            output = root / "home.surface.yaml"
            session = SurfaceLayoutAuthoringSession(
                name="home",
                background_path=str(image),
                base_resolution=(1000, 500),
            )
            session.add_press_point_from_target(
                "drive",
                "navigate:drive",
                [(100, 100), (300, 100), (300, 200), (100, 200)],
                (1000, 500),
            )
            session.save(str(output))

            loaded = SurfaceManifestLoader().load(str(output))
            self.assertEqual(loaded.name, "home")
            self.assertEqual(loaded.press_points[0].point_id, "drive")
            self.assertEqual(Path(loaded.background.image_path), image)


if __name__ == "__main__":
    unittest.main()
