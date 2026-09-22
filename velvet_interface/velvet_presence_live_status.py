# SPDX-License-Identifier: GPL-3.0-only
"""Evidence-backed ambient presence state for the Founder Velvet layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from velvet_interface.boot_status import load_boot_snapshot


@dataclass(frozen=True)
class VelvetPresenceStatus:
    state: str
    runtime_state: str
    conversation_available: bool
    message: str


def load_velvet_presence_status(
    boot_snapshot: Path,
    conversation_socket: Path,
) -> VelvetPresenceStatus:
    """Summarize local evidence without turning presence into authority."""

    boot = load_boot_snapshot(Path(boot_snapshot))
    runtime_active = boot.runtime == "ACTIVE"

    socket = Path(conversation_socket)
    try:
        conversation_available = socket.is_socket()
    except OSError:
        conversation_available = False

    if runtime_active and conversation_available:
        state = "READY"
        message = "Local Runtime and written conversation are available"
    elif runtime_active:
        state = "AWAKE"
        message = "Runtime active; local conversation transport is unavailable"
    elif conversation_available:
        state = "DEGRADED"
        message = "Conversation socket exists without verified active Runtime evidence"
    else:
        state = "WAITING"
        message = boot.message

    return VelvetPresenceStatus(
        state=state,
        runtime_state=boot.runtime,
        conversation_available=conversation_available,
        message=message,
    )
