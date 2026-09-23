import json
import socket
import struct
import tempfile
import threading
import unittest
from pathlib import Path

from velvet_interface.conversation_bridge import (
    ConversationBridgeError,
    UnixConversationBridge,
)


class ConversationBridgeTests(unittest.TestCase):
    def test_submit_uses_runtime_unix_rpc_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "conversation.sock"
            captured = {}
            ready = threading.Event()

            def server():
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                    listener.bind(str(path))
                    listener.listen(1)
                    ready.set()
                    conn, _ = listener.accept()
                    with conn:
                        size = struct.unpack("!I", self._recv(conn, 4))[0]
                        request = json.loads(self._recv(conn, size).decode())
                        captured.update(request)
                        result = {
                            "conversation_id": "c",
                            "turn_id": "c:1",
                            "turn_number": 1,
                            "text": "hello",
                            "generator": "test",
                            "requires_authority_check": False,
                            "authority_granted": False,
                            "grants_execution": False,
                            "grants_actuation": False,
                        }
                        response = {
                            "protocol": "velvet.runtime.unix.v1",
                            "kind": "response",
                            "request_id": request["request_id"],
                            "ok": True,
                            "result": result,
                            "error_type": None,
                            "error": None,
                            "transport_only": True,
                            "canonical": False,
                            "grants_authority": False,
                            "grants_execution": False,
                            "grants_actuation": False,
                            "authority": "none",
                        }
                        raw = json.dumps(response, separators=(",", ":")).encode()
                        conn.sendall(struct.pack("!I", len(raw)) + raw)

            thread = threading.Thread(target=server)
            thread.start()
            ready.wait(2)
            reply = UnixConversationBridge(path).submit("Hi Velvet")
            thread.join(2)

            self.assertEqual(captured["protocol"], "velvet.runtime.unix.v1")
            self.assertEqual(captured["kind"], "request")
            self.assertTrue(captured["request_id"])
            self.assertEqual(captured["operation"], "submit_turn")
            self.assertEqual(
                captured["payload"],
                {"text": "Hi Velvet", "modality": "text"},
            )
            self.assertIs(captured["transport_only"], True)
            self.assertIs(captured["canonical"], False)
            self.assertIs(captured["grants_authority"], False)
            self.assertIs(captured["grants_execution"], False)
            self.assertIs(captured["grants_actuation"], False)
            self.assertEqual(captured["authority"], "none")
            self.assertEqual(reply["text"], "hello")

    def test_transport_flag_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "conversation.sock"
            ready = threading.Event()

            def server():
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                    listener.bind(str(path))
                    listener.listen(1)
                    ready.set()
                    conn, _ = listener.accept()
                    with conn:
                        size = struct.unpack("!I", self._recv(conn, 4))[0]
                        request = json.loads(self._recv(conn, size).decode())
                        response = {
                            "protocol": "velvet.runtime.unix.v1",
                            "kind": "response",
                            "request_id": request["request_id"],
                            "ok": False,
                            "result": {},
                            "error_type": "ValueError",
                            "error": "bad flags",
                            "transport_only": False,
                            "canonical": False,
                            "grants_authority": False,
                            "grants_execution": False,
                            "grants_actuation": False,
                            "authority": "none",
                        }
                        raw = json.dumps(response, separators=(",", ":")).encode()
                        conn.sendall(struct.pack("!I", len(raw)) + raw)

            thread = threading.Thread(target=server)
            thread.start()
            ready.wait(2)
            with self.assertRaises(ConversationBridgeError):
                UnixConversationBridge(path).submit("Hi Velvet")
            thread.join(2)

    def test_authority_claim_fails_closed(self):
        result = {
            "conversation_id": "c",
            "turn_id": "c:1",
            "turn_number": 1,
            "text": "x",
            "generator": "test",
            "requires_authority_check": False,
            "authority_granted": True,
            "grants_execution": False,
            "grants_actuation": False,
        }
        from velvet_interface.conversation_bridge import _validate_result

        with self.assertRaises(ConversationBridgeError):
            _validate_result(result)

    @staticmethod
    def _recv(conn, count):
        out = b""
        while len(out) < count:
            out += conn.recv(count - len(out))
        return out


if __name__ == "__main__":
    unittest.main()
