from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from velvet_interface.eleanor_bridge import EleanorBridge, EleanorUnavailable


class EleanorBridgeTests(unittest.TestCase):
    def test_bridge_uses_allow_listed_read_only_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "eleanor-engineering"
            manifest = root / "project.yaml"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            manifest.write_text("project: {}\n", encoding="utf-8")
            bridge = EleanorBridge(executable, manifest)
            completed = type(
                "Completed",
                (),
                {"stdout": json.dumps({"errors": 0}), "stderr": "", "returncode": 0},
            )()
            with patch(
                "velvet_interface.eleanor_bridge.subprocess.run", return_value=completed
            ) as run:
                self.assertEqual(bridge.validate()["errors"], 0)
                argv = run.call_args.args[0]
                self.assertEqual(argv[1], "validate")
                self.assertEqual(argv[-1], "--json")

                self.assertEqual(bridge.validate_artifacts()["errors"], 0)
                argv = run.call_args.args[0]
                self.assertEqual(argv[1], "validate")
                self.assertIn("--verify-artifacts", argv)
                self.assertEqual(argv[-1], "--json")

            with self.assertRaises(ValueError):
                bridge._run_json("calculate")
            with self.assertRaises(ValueError):
                bridge._run_json("coverage", ("--verify-artifacts",))
            with self.assertRaises(ValueError):
                bridge._run_json("validate", ("--verify-artifacts", "--verify-artifacts"))

    def test_missing_executable_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "project.yaml"
            manifest.write_text("project: {}\n", encoding="utf-8")
            with self.assertRaises(EleanorUnavailable):
                EleanorBridge(Path("/missing/eleanor"), manifest).validate()


if __name__ == "__main__":
    unittest.main()
