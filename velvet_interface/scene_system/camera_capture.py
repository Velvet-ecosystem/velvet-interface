# SPDX-License-Identifier: GPL-3.0-only
"""Trusted current-frame capture seam for Surface Studio.

Camera nodes may publish one atomically replaced PNG or JPEG still. Surface
Studio captures that exact current file through this bounded provider. Missing,
stale, malformed, oversized, or symlinked files fail closed. No placeholder or
synthetic image is returned.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_JPEG_SIGNATURE = b"\xff\xd8\xff"
_ALLOWED_FORMATS = {"png", "jpg", "jpeg"}


class CameraFrameUnavailable(RuntimeError):
    """Raised when no trustworthy current camera frame can be captured."""


@dataclass(frozen=True)
class CapturedCameraFrame:
    """One immutable still captured from a trusted camera-feed boundary."""

    image_bytes: bytes
    image_format: str
    source_id: str
    captured_at: float
    receipt_id: str

    def __post_init__(self) -> None:
        image_format = self.image_format.strip().lower()
        if image_format not in _ALLOWED_FORMATS:
            raise ValueError("camera frame format must be png, jpg, or jpeg")
        if not isinstance(self.image_bytes, bytes) or len(self.image_bytes) < 8:
            raise ValueError("camera frame bytes are missing or too small")
        _verify_signature(self.image_bytes, image_format)
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("camera source_id must be non-empty")
        if not isinstance(self.receipt_id, str) or not self.receipt_id.strip():
            raise ValueError("camera capture receipt_id must be non-empty")
        if isinstance(self.captured_at, bool) or not isinstance(self.captured_at, (int, float)):
            raise TypeError("camera captured_at must be numeric")
        if not math.isfinite(float(self.captured_at)) or float(self.captured_at) <= 0:
            raise ValueError("camera captured_at must be a positive finite timestamp")

    @property
    def suffix(self) -> str:
        return ".jpg" if self.image_format.lower() in {"jpg", "jpeg"} else ".png"


class FileCameraFrameProvider:
    """Read an atomically published latest-frame file at capture time."""

    def __init__(
        self,
        frame_path: Path,
        source_id: str = "camera.current_frame",
        max_age_seconds: float = 2.0,
        max_bytes: int = 32 * 1024 * 1024,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("camera source_id must be non-empty")
        if isinstance(max_age_seconds, bool) or not isinstance(max_age_seconds, (int, float)):
            raise TypeError("max_age_seconds must be numeric")
        if not math.isfinite(float(max_age_seconds)) or float(max_age_seconds) <= 0:
            raise ValueError("max_age_seconds must be positive and finite")
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int):
            raise TypeError("max_bytes must be an integer")
        if max_bytes < 1024 or max_bytes > 512 * 1024 * 1024:
            raise ValueError("max_bytes is outside supported bounds")

        self.frame_path = Path(frame_path).expanduser()
        self.source_id = source_id.strip()
        self.max_age_seconds = float(max_age_seconds)
        self.max_bytes = max_bytes
        self.clock = clock or time.time

    def __call__(self) -> CapturedCameraFrame:
        raw_path = self.frame_path
        if raw_path.is_symlink():
            raise CameraFrameUnavailable("camera frame path is a symlink")
        path = raw_path.resolve()
        if not path.is_file():
            raise CameraFrameUnavailable("current camera frame is unavailable")

        suffix = path.suffix.lower().lstrip(".")
        if suffix not in _ALLOWED_FORMATS:
            raise CameraFrameUnavailable("camera frame must be PNG or JPEG")

        try:
            stat = path.stat()
        except OSError as exc:
            raise CameraFrameUnavailable("camera frame cannot be inspected: %s" % exc)
        if stat.st_size < 8 or stat.st_size > self.max_bytes:
            raise CameraFrameUnavailable("camera frame size is outside supported bounds")

        now = float(self.clock())
        age = now - float(stat.st_mtime)
        if age < -5.0:
            raise CameraFrameUnavailable("camera frame timestamp is untrustworthily in the future")
        if age > self.max_age_seconds:
            raise CameraFrameUnavailable(
                "camera frame is stale by %.3f seconds" % age
            )

        try:
            descriptor = os.open(str(path), os.O_RDONLY)
            try:
                opened_stat = os.fstat(descriptor)
                if opened_stat.st_ino != stat.st_ino or opened_stat.st_dev != stat.st_dev:
                    raise CameraFrameUnavailable("camera frame changed during capture")
                chunks = []
                remaining = self.max_bytes + 1
                while remaining > 0:
                    chunk = os.read(descriptor, min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                content = b"".join(chunks)
            finally:
                os.close(descriptor)
        except CameraFrameUnavailable:
            raise
        except OSError as exc:
            raise CameraFrameUnavailable("camera frame cannot be read: %s" % exc)

        if len(content) != stat.st_size or len(content) > self.max_bytes:
            raise CameraFrameUnavailable("camera frame changed or exceeded bounds during capture")
        try:
            _verify_signature(content, suffix)
        except ValueError as exc:
            raise CameraFrameUnavailable(str(exc))

        return CapturedCameraFrame(
            image_bytes=content,
            image_format=suffix,
            source_id=self.source_id,
            captured_at=float(stat.st_mtime),
            receipt_id=str(uuid4()),
        )


def _verify_signature(content: bytes, image_format: str) -> None:
    normalized = image_format.strip().lower()
    if normalized == "png" and not content.startswith(_PNG_SIGNATURE):
        raise ValueError("camera PNG signature is invalid")
    if normalized in {"jpg", "jpeg"} and not content.startswith(_JPEG_SIGNATURE):
        raise ValueError("camera JPEG signature is invalid")
