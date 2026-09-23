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
    _validate_result,
)


PROTOCOL = "velvet.runtime.unix.v1"
TRANSPORT_FLAGS = {
    "transport_only": True,
    "canonical": False,
    "grants_authority": False,
    "grants_execution": False,
    "grants_actuation": False,
    "authority": "none",
}


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
                    connection, _ = listener.accept()
                    with connection:
                        size = struct.unpack("!I", self._recv(connection, 4))[0]
                        request = json.loads(self._recv(connection, size).decode())
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
                            "protocol": PROTOCOL,
                            "kind": "response",
                            "request_id": request["request_id"],
                            "ok": True,
                            "result": result,
                            "error_type": None,
                            "error": None,
                            **TRANSPORT_FLAGS,
                        }
                        raw = json.dumps(response).encode()
                        connection.sendall(struct.pack("!I", len(raw)) + raw)

            thread = threading.Thread(target=server)
            thread.start()
            ready.wait(2)
            reply = UnixConversationBridge(path).submit("Hi Velvet")
            thread.join(2)

            self.assertEqual(captured["protocol"], PROTOCOL)
            self.assertEqual(captured["kind"], "request")
            self.assertIsInstance(captured["request_id"], str)
            self.assertTrue(captured["request_id"])
            self.assertEqual(captured["operation"], "submit_turn")
            self.assertEqual(
                captured["payload"],
                {"text": "Hi Velvet", "modality": "text"},
            )
            for key, expected in TRANSPORT_FLAGS.items():
                self.assertEqual(captured[key], expected)
            self.assertEqual(reply["text"], "hello")

    def test_response_request_id_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "conversation.sock"
            ready = threading.Event()

            def server():
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                    listener.bind(str(path))
                    listener.listen(1)
                    ready.set()
                    connection, _ = listener.accept()
                    with connection:
                        size = struct.unpack("!I", self._recv(connection, 4))[0]
                        self._recv(connection, size)
                        response = {
                            "protocol": PROTOCOL,
                            "kind": "response",
                            "request_id": "wrong-request-id",
                            "ok": False,
                            "result": {},
                            "error_type": "TestError",
                            "error": "rejected",
                            **TRANSPORT_FLAGS,
                        }
                        raw = json.dumps(response).encode()
                        connection.sendall(struct.pack("!I", len(raw)) + raw)

            thread = threading.Thread(target=server)
            thread.start()
            ready.wait(2)
            with self.assertRaisesRegex(ConversationBridgeError, "request_id"):
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
        with self.assertRaises(ConversationBridgeError):
            _validate_result(result)

    @staticmethod
    def _recv(connection, count):
        output = b""
        while len(output) < count:
            output += connection.recv(count - len(output))
        return output


if __name__ == "__main__":
    unittest.main()
