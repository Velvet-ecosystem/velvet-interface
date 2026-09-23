from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from velvet_interface.forge_workspace_bridges import (
    EngineeringDesignBridge,
    ForgeWorkspaceUnavailable,
    ModuleLabBridge,
    TestBenchBridge,
)


class FakeEleanor:
    def __init__(self, manifest: Path) -> None:
        self.manifest = manifest
        self.calls = []

    def validate(self):
        self.calls.append("validate")
        return {"errors": 0, "warnings": 1, "issues": []}

    def validate_artifacts(self):
        self.calls.append("validate_artifacts")
        return {"errors": 0, "warnings": 0, "issues": []}

    def coverage(self):
        self.calls.append("coverage")
        return {
            "summary": {"covered": 1, "uncovered": 1},
            "requirements": [
                {
                    "id": "REQ-1",
                    "priority": "must",
                    "requirement_status": "open",
                    "coverage_state": "covered",
                },
                {
                    "id": "REQ-2",
                    "priority": "should",
                    "requirement_status": "open",
                    "coverage_state": "uncovered",
                },
            ],
        }


class ForgeWorkspaceBridgeTests(unittest.TestCase):
    def _manifest(self, root: Path) -> Path:
        path = root / "engineering-project.yaml"
        path.write_text(
            """schema: velvet.eleanor.engineering-project
version: '0.3'
status: draft
project:
  id: TEST-001
  name: Test board
  description: Read-only fixture
  lifecycle: requirements
  revision: 2
intent:
  statement: Build a test board.
  desired_outcome: Verified design evidence.
requirements:
  - id: REQ-1
assumptions:
  - id: ASM-1
evidence: []
decisions: []
artifacts: {}
calculations: []
risks: []
approvals: []
authority:
  current_gate: research
  allowed_actions: [research, calculate]
  prohibited_actions: [physical_execution, fabrication_release]
  physical_execution:
    allowed: false
handoff:
  status: draft
  summary: Requirements only.
  recommended_next_actions:
    - Add evidence.
""",
            encoding="utf-8",
        )
        return path

    def test_engineering_design_projects_canonical_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = self._manifest(Path(directory))
            fake = FakeEleanor(manifest)
            snapshot = EngineeringDesignBridge(fake).snapshot()
            self.assertEqual(snapshot["project"]["id"], "TEST-001")
            self.assertEqual(snapshot["project"]["revision"], 2)
            self.assertEqual(snapshot["counts"]["requirements"], 1)
            self.assertEqual(snapshot["authority"]["current_gate"], "research")
            self.assertFalse(snapshot["authority"]["physical_execution_allowed"])
            self.assertEqual(snapshot["validation"]["warnings"], 1)
            self.assertEqual(fake.calls, ["validate"])

    def test_engineering_design_rejects_symlink_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = self._manifest(root)
            link = root / "linked.yaml"
            link.symlink_to(real)
            fake = FakeEleanor(link)
            with self.assertRaises(ForgeWorkspaceUnavailable):
                EngineeringDesignBridge(fake).snapshot()

    def test_test_bench_runs_only_read_only_eleanor_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = self._manifest(Path(directory))
            fake = FakeEleanor(manifest)
            snapshot = TestBenchBridge(fake).snapshot()
            self.assertEqual(fake.calls, ["validate", "validate_artifacts", "coverage"])
            self.assertEqual(snapshot["artifact_validation"]["errors"], 0)
            self.assertEqual(len(snapshot["coverage"]["requirements"]), 2)

    def test_module_lab_inventory_uses_specs_not_python_package_dirs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "lab/candidates/audio-level-control").mkdir(parents=True)
            (root / "lab/candidates/audio-level-control/SPEC.md").write_text(
                "# candidate\n", encoding="utf-8"
            )
            (root / "lab/candidates/audio_level_control").mkdir()
            (root / "lab/candidates/audio_level_control/__init__.py").write_text(
                "", encoding="utf-8"
            )
            (root / "lab/intake").mkdir(parents=True)
            (root / "lab/intake/audio.yaml").write_text("id: audio\n", encoding="utf-8")
            (root / "lab/reports").mkdir(parents=True)
            (root / "lab/reports/audio.md").write_text("# report\n", encoding="utf-8")
            (root / "modules/cabin").mkdir(parents=True)

            snapshot = ModuleLabBridge(root).snapshot()
            self.assertEqual(snapshot["candidates"], ["audio-level-control"])
            self.assertEqual(snapshot["intake"], ["audio.yaml"])
            self.assertEqual(snapshot["reports"], ["audio.md"])
            self.assertEqual(snapshot["promoted_domains"], ["cabin"])
            self.assertTrue(snapshot["read_only"])


if __name__ == "__main__":
    unittest.main()
