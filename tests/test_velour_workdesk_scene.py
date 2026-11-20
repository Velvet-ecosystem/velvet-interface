import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from velvet_interface.workdesk_bridge import WorkDeskBridge, WorkDeskUnavailable
from velvet_interface.scenes.velour_workdesk_scene import VelourWorkDeskScene

class WorkDeskSceneTests(unittest.TestCase):
    def test_scene_fails_closed_when_owner_maintenance_is_not_verified(self):
        scene = VelourWorkDeskScene(bridge=WorkDeskBridge(Path("missing")),
                                    access_provider=lambda: False)
        self.assertFalse(scene._has_access())
        broken = VelourWorkDeskScene(bridge=WorkDeskBridge(Path("missing")),
                                    access_provider=lambda: (_ for _ in ()).throw(RuntimeError()))
        self.assertFalse(broken._has_access())

    def test_bridge_does_not_invent_missing_runtime(self):
        with tempfile.TemporaryDirectory() as raw:
            bridge = WorkDeskBridge(Path(raw) / "missing.json")
            with self.assertRaises(WorkDeskUnavailable):
                bridge.read()

    def test_bridge_requires_readonly_authority_none(self):
        bridge = WorkDeskBridge(Path("fixture"))
        with patch("services.founder_work_desk.load_workdesk_file", return_value={}):
            with patch("services.founder_work_desk.workdesk_report", return_value={
                "schema": "velvet.runtime.workdesk.report.v1", "authority": "execute",
                "read_only": True, "mode": "ghost",
            }):
                with self.assertRaises(WorkDeskUnavailable):
                    bridge.read()

if __name__ == "__main__":
    unittest.main()
