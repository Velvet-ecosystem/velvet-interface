# SPDX-License-Identifier: GPL-3.0-only
"""Narrow standalone client for Runtime's local conversation Unix socket."""
from __future__ import annotations

import json
import socket
import struct
from pathlib import Path
from typing import Any, Mapping, Union
from uuid import uuid4

_PROTOCOL = "velvet.runtime.unix.v1"
_MAX_FRAME_BYTES = 1024 * 1024
_TRANSPORT_FLAGS = {
    "transport_only": True,
    "canonical": False,
    "grants_authority": False,
    "grants_execution": False,
    "grants_actuation": False,
    "authority": "none",
}


class ConversationBridgeError(RuntimeError):
    """The local Runtime conversation endpoint rejected or failed a request."""


class UnixConversationBridge:
    """Interface-owned client for Runtime's narrow submit_turn contract."""

    def __init__(self, socket_path: Union[str, Path], timeout_seconds: float = 2.0) -> None:
        self.socket_path = Path(socket_path)
        self.timeout_seconds = float(timeout_seconds)
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def submit(self, text: str, *, modality: str = "text") -> Mapping[str, Any]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("conversation text must be non-empty")
        if modality not in {"text", "speech_transcript"}:
            raise ValueError("unsupported conversation modality")

        request_id = uuid4().hex
        request = {
            "protocol": _PROTOCOL,
            "kind": "request",
            "request_id": request_id,
            "operation": "submit_turn",
            "payload": {"text": text.strip(), "modality": modality},
            **_TRANSPORT_FLAGS,
        }
        response = self._call(request)
        _validate_response_envelope(response, request_id)

        if response.get("ok") is not True:
            error_type = str(response.get("error_type") or "RemoteError")
            error = str(response.get("error") or "conversation request failed")
            raise ConversationBridgeError("%s: %s" % (error_type, error))

        result = response.get("result")
        if not isinstance(result, Mapping):
            raise ConversationBridgeError("conversation result must be a mapping")
        return _validate_result(result)

    def _call(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        payload = json.dumps(
            request,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(payload) > _MAX_FRAME_BYTES:
            raise ConversationBridgeError("conversation request exceeds frame bound")
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(self.timeout_seconds)
                client.connect(str(self.socket_path))
                client.sendall(struct.pack("!I", len(payload)) + payload)
                size = struct.unpack("!I", _recv_exact(client, 4))[0]
                if size < 1 or size > _MAX_FRAME_BYTES:
                    raise ConversationBridgeError("conversation response frame is invalid")
                raw = _recv_exact(client, size)
        except (OSError, socket.timeout) as exc:
            raise ConversationBridgeError("conversation socket unavailable: %s" % exc) from exc
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ConversationBridgeError("conversation response is invalid JSON") from exc
        if not isinstance(value, Mapping):
            raise ConversationBridgeError("conversation envelope must be a mapping")
        return value


def _recv_exact(client: socket.socket, count: int) -> bytes:
    chunks = []
    remaining = count
    while remaining:
        chunk = client.recv(remaining)
        if not chunk:
            raise ConversationBridgeError("conversation socket closed early")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _validate_response_envelope(response: Mapping[str, Any], request_id: str) -> None:
    for key, expected in _TRANSPORT_FLAGS.items():
        if response.get(key) != expected:
            raise ConversationBridgeError(
                "conversation response %s must be %r" % (key, expected)
            )
    if response.get("protocol") != _PROTOCOL or response.get("kind") != "response":
        raise ConversationBridgeError("unsupported conversation response protocol")
    if response.get("request_id") != request_id:
        raise ConversationBridgeError("conversation response request_id mismatch")
    if response.get("ok") not in {True, False}:
        raise ConversationBridgeError("conversation response ok field must be boolean")


def _validate_result(result: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("conversation_id", "turn_id", "text", "generator"):
        value = result.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ConversationBridgeError("conversation response %s is invalid" % key)
    turn = result.get("turn_number")
    if isinstance(turn, bool) or not isinstance(turn, int) or turn < 1:
        raise ConversationBridgeError("conversation response turn_number is invalid")
    for key in ("authority_granted", "grants_execution", "grants_actuation"):
        if result.get(key) is not False:
            raise ConversationBridgeError("conversation response attempted to grant %s" % key)
    if not isinstance(result.get("requires_authority_check"), bool):
        raise ConversationBridgeError("conversation authority-check flag is invalid")
    return dict(result)
