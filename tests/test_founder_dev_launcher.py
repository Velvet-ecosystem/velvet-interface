# SPDX-License-Identifier: GPL-3.0-only

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = REPO_ROOT / "scripts" / "run_founder_dev.sh"


@unittest.skipUnless(sys.platform != "win32", "launcher requires a POSIX shell")
class FounderDevLauncherTests(unittest.TestCase):
    def _fake_python(self, root: Path) -> Path:
        fake = root / "fake-python"
        fake.write_text(
            "#!/usr/bin/env bash\n"
            "printf 'args=%s\\n' \"$*\" > \"$VELVET_TEST_LOG\"\n"
            "printf 'boot=%s\\n' \"$VELVET_BOOT_SNAPSHOT_PATH\" >> \"$VELVET_TEST_LOG\"\n"
            "printf 'socket=%s\\n' \"$VELVET_CONVERSATION_SOCKET_PATH\" >> \"$VELVET_TEST_LOG\"\n"
            "printf 'interface_dev=%s\\n' \"$VELVET_INTERFACE_DEVELOPMENT\" >> \"$VELVET_TEST_LOG\"\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        return fake

    def test_defaults_bind_interface_to_runtime_development_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "velvet-runtime"
            dev = runtime / ".velvet-dev"
            dev.mkdir(parents=True)
            (dev / "first-boot-snapshot.json").write_text("{}\n", encoding="utf-8")
            log = root / "launcher.log"
            fake_python = self._fake_python(root)

            environment = os.environ.copy()
            environment.update(
                {
                    "VELVET_RUNTIME_ROOT": str(runtime),
                    "VELVET_INTERFACE_PYTHON": str(fake_python),
                    "VELVET_TEST_LOG": str(log),
                }
            )
            environment.pop("VELVET_BOOT_SNAPSHOT_PATH", None)
            environment.pop("VELVET_CONVERSATION_SOCKET_PATH", None)
            environment.pop("VELVET_INTERFACE_DEVELOPMENT", None)

            result = subprocess.run(
                ["bash", str(LAUNCHER), "--width", "1152", "--height", "648"],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            output = log.read_text(encoding="utf-8")
            self.assertIn(
                "args=-m velvet_interface.founder_surface_launcher --width 1152 --height 648",
                output,
            )
            self.assertIn("boot=%s" % (dev / "first-boot-snapshot.json"), output)
            self.assertIn("socket=%s" % (dev / "run" / "conversation.sock"), output)
            self.assertIn("interface_dev=true", output)

    def test_explicit_runtime_paths_and_development_marker_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "velvet-runtime"
            runtime.mkdir()
            boot = root / "chosen-boot.json"
            boot.write_text("{}\n", encoding="utf-8")
            socket = root / "chosen.sock"
            log = root / "launcher.log"
            fake_python = self._fake_python(root)

            environment = os.environ.copy()
            environment.update(
                {
                    "VELVET_RUNTIME_ROOT": str(runtime),
                    "VELVET_INTERFACE_PYTHON": str(fake_python),
                    "VELVET_TEST_LOG": str(log),
                    "VELVET_BOOT_SNAPSHOT_PATH": str(boot),
                    "VELVET_CONVERSATION_SOCKET_PATH": str(socket),
                    "VELVET_INTERFACE_DEVELOPMENT": "false",
                }
            )

            result = subprocess.run(
                ["bash", str(LAUNCHER)],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            output = log.read_text(encoding="utf-8")
            self.assertIn("boot=%s" % boot, output)
            self.assertIn("socket=%s" % socket, output)
            self.assertIn("interface_dev=false", output)


if __name__ == "__main__":
    unittest.main()
