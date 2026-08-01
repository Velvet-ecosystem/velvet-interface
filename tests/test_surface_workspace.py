# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path

from velvet_interface.scene_system.surface_workspace import (
    SurfacePromotionContext,
    SurfaceWorkspace,
    SurfaceWorkspaceError,
)


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"surface-studio-test"


class SurfaceWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.workspace = SurfaceWorkspace(
            workspace_root=root / "workspace",
            active_surface_dir=root / "active",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _session(self, name: str = "maintenance"):
        background = self.workspace.create_blank_background(name, PNG_BYTES)
        session = self.workspace.create_session(
            name,
            background,
            (1280, 720),
            fit_mode="cover",
        )
        session.add_press_point_from_target(
            "open_drive",
            "navigate:drive",
            ((100, 100), (300, 100), (300, 250), (100, 250)),
            (1280, 720),
        )
        session.add_widget_from_target(
            "founder_body_status",
            (900, 40, 320, 180),
            (1280, 720),
        )
        return session

    def test_draft_round_trip_stays_in_managed_workspace(self) -> None:
        session = self._session()
        path = self.workspace.save_draft(session)
        self.assertTrue(path.is_file())
        self.assertEqual(self.workspace.list_drafts(), ("maintenance",))

        loaded = self.workspace.load_draft("maintenance")
        self.assertEqual(loaded.name, "maintenance")
        self.assertEqual(len(loaded.press_points), 1)
        self.assertEqual(len(loaded.widgets), 1)
        validation = self.workspace.validate_draft("maintenance")
        self.assertTrue(validation["valid"])
        self.assertTrue(validation["draft_only"])
        self.assertEqual(validation["authority"], "none")

    def test_promotion_fails_closed_when_any_gate_is_missing(self) -> None:
        self.workspace.save_draft(self._session())
        context = SurfacePromotionContext(
            maintenance_unlocked=True,
            owner_present=True,
            vehicle_stationary=False,
            physical_control_disabled=True,
            receipt_id="receipt-denied",
        )
        with self.assertRaises(PermissionError):
            self.workspace.promote("maintenance", context)
        self.assertFalse((self.workspace.active_surface_dir / "maintenance.surface.yaml").exists())

    def test_promotion_writes_active_surface_and_append_only_receipt(self) -> None:
        self.workspace.save_draft(self._session())
        context = SurfacePromotionContext(
            maintenance_unlocked=True,
            owner_present=True,
            vehicle_stationary=True,
            physical_control_disabled=True,
            receipt_id="receipt-approved",
        )
        result = self.workspace.promote("maintenance", context)
        self.assertTrue(result.manifest_path.is_file())
        self.assertTrue(result.background_path.is_file())
        self.assertEqual(result.receipt_id, "receipt-approved")

        receipt_lines = self.workspace.receipts_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(receipt_lines), 1)
        receipt = json.loads(receipt_lines[0])
        self.assertEqual(receipt["surface_name"], "maintenance")
        self.assertEqual(receipt["authority"], "none")
        self.assertFalse(receipt["actuation_granted"])
        self.assertFalse(receipt["actuation_performed"])

    def test_import_rejects_wrong_signature_and_path_like_name(self) -> None:
        root = Path(self.temporary.name)
        fake = root / "not-image.png"
        fake.write_bytes(b"not a png at all")
        with self.assertRaises(SurfaceWorkspaceError):
            self.workspace.import_background(fake, "maintenance")
        with self.assertRaises(SurfaceWorkspaceError):
            self.workspace.create_blank_background("../escape", PNG_BYTES)

    def test_context_lists_every_missing_piece_of_evidence(self) -> None:
        context = SurfacePromotionContext(
            maintenance_unlocked=False,
            owner_present=False,
            vehicle_stationary=False,
            physical_control_disabled=False,
            receipt_id="receipt-all-denied",
        )
        self.assertFalse(context.allowed)
        self.assertEqual(len(context.denial_reasons()), 4)


if __name__ == "__main__":
    unittest.main()
