from pathlib import Path
import json
import socket
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from velvet_interface.velvet_presence_live_status import load_velvet_presence_status


class VelvetPresenceLiveStatusTests(unittest.TestCase):
    def _write_active_boot(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "doctor": {"ready": True, "state": "ready", "checks": [], "errors": []},
                    "service": {"active_state": "active", "sub_state": "running"},
                    "route_count": 7,
                }
            ),
            encoding="utf-8",
        )

    def test_bound_socket_and_preflight_are_insufficient_for_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            boot = root / "boot.json"
            transport = root / "conversation.sock"
            self._write_active_boot(boot)

            unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                unix_socket.bind(str(transport))
                status = load_velvet_presence_status(boot, transport)
            finally:
                unix_socket.close()

            self.assertEqual(status.state, "WAITING")
            self.assertEqual(status.runtime_state, "UNKNOWN")
            self.assertFalse(status.conversation_available)

    def test_active_runtime_without_socket_is_awake_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            boot = root / "boot.json"
            self._write_active_boot(boot)

            with patch('velvet_interface.velvet_presence_live_status.load_boot_snapshot',
                       return_value=SimpleNamespace(runtime='ACTIVE', session_id='session', message='active')):
                status = load_velvet_presence_status(boot, root / "conversation.sock")

            self.assertEqual(status.state, "AWAKE")
            self.assertEqual(status.runtime_state, "ACTIVE")
            self.assertFalse(status.conversation_available)

    def test_missing_evidence_fails_closed_to_waiting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status = load_velvet_presence_status(
                root / "missing-boot.json",
                root / "missing.sock",
            )

            self.assertEqual(status.state, "WAITING")
            self.assertEqual(status.runtime_state, "UNKNOWN")
            self.assertFalse(status.conversation_available)
            self.assertIn("Boot snapshot not found", status.message)


if __name__ == "__main__":
    unittest.main()
