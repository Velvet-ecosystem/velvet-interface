# SPDX-License-Identifier: GPL-3.0-only

import base64
import json
import os
import tempfile
import unittest
from pathlib import Path

from velvet_interface.scene_system.camera_capture import (
    CameraFrameUnavailable,
    CapturedCameraFrame,
    FileCameraFrameProvider,
)
from velvet_interface.scene_system.surface_workspace import SurfaceWorkspace


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAusB9WlVvS8AAAAASUVORK5CYII="
)


class CameraCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_file_provider_returns_only_a_fresh_real_frame(self) -> None:
        frame_path = self.root / "latest-frame.png"
        frame_path.write_bytes(PNG_BYTES)
        os.utime(str(frame_path), (100.0, 100.0))
        provider = FileCameraFrameProvider(
            frame_path=frame_path,
            source_id="camera.front",
            max_age_seconds=3.0,
            clock=lambda: 102.0,
        )

        frame = provider()

        self.assertEqual(frame.image_bytes, PNG_BYTES)
        self.assertEqual(frame.image_format, "png")
        self.assertEqual(frame.source_id, "camera.front")
        self.assertEqual(frame.captured_at, 100.0)
        self.assertTrue(frame.receipt_id)

    def test_file_provider_rejects_stale_missing_and_malformed_frames(self) -> None:
        missing = FileCameraFrameProvider(
            frame_path=self.root / "missing.jpg",
            clock=lambda: 100.0,
        )
        with self.assertRaises(CameraFrameUnavailable):
            missing()

        stale_path = self.root / "stale.png"
        stale_path.write_bytes(PNG_BYTES)
        os.utime(str(stale_path), (90.0, 90.0))
        stale = FileCameraFrameProvider(
            frame_path=stale_path,
            max_age_seconds=3.0,
            clock=lambda: 100.0,
        )
        with self.assertRaises(CameraFrameUnavailable):
            stale()

        malformed_path = self.root / "latest-frame.jpg"
        malformed_path.write_bytes(b"not really a jpeg")
        os.utime(str(malformed_path), (100.0, 100.0))
        malformed = FileCameraFrameProvider(
            frame_path=malformed_path,
            clock=lambda: 100.0,
        )
        with self.assertRaises(CameraFrameUnavailable):
            malformed()

    def test_file_provider_rejects_symlinked_frame(self) -> None:
        real_path = self.root / "real.png"
        real_path.write_bytes(PNG_BYTES)
        link_path = self.root / "latest.png"
        try:
            link_path.symlink_to(real_path)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")
        provider = FileCameraFrameProvider(
            frame_path=link_path,
            clock=lambda: real_path.stat().st_mtime,
        )
        with self.assertRaises(CameraFrameUnavailable):
            provider()

    def test_workspace_stores_capture_and_append_only_receipt(self) -> None:
        workspace = SurfaceWorkspace(
            workspace_root=self.root / "workspace",
            active_surface_dir=self.root / "active",
        )
        frame = CapturedCameraFrame(
            image_bytes=PNG_BYTES,
            image_format="png",
            source_id="camera.cabin",
            captured_at=123.5,
            receipt_id="capture-receipt-1",
        )

        target = workspace.import_camera_frame(frame, "camera_home")

        self.assertTrue(target.is_file())
        self.assertEqual(target.read_bytes(), PNG_BYTES)
        lines = workspace.camera_receipts_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        receipt = json.loads(lines[0])
        self.assertEqual(receipt["receipt_id"], "capture-receipt-1")
        self.assertEqual(receipt["source_id"], "camera.cabin")
        self.assertEqual(receipt["surface_name"], "camera_home")
        self.assertEqual(receipt["authority"], "none")
        self.assertFalse(receipt["actuation_granted"])
        self.assertFalse(receipt["actuation_performed"])

    def test_frame_contract_rejects_false_image_signatures(self) -> None:
        with self.assertRaises(ValueError):
            CapturedCameraFrame(
                image_bytes=b"not actually png",
                image_format="png",
                source_id="camera.front",
                captured_at=1.0,
                receipt_id="receipt",
            )


if __name__ == "__main__":
    unittest.main()
