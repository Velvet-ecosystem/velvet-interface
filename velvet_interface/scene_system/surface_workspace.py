# SPDX-License-Identifier: GPL-3.0-only
"""Managed draft and promotion workspace for on-device surface authoring.

Surface Studio edits a private draft workspace. Promotion into the active
surface directory is a separate, explicit maintenance operation and produces an
append-only receipt. This module grants no Runtime, Court, executor, or physical
authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from velvet_interface.scene_system.authoring import SurfaceLayoutAuthoringSession
from velvet_interface.scene_system.camera_capture import CapturedCameraFrame
from velvet_interface.scene_system.surface_manifest import SurfaceManifestLoader


_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_JPEG_SIGNATURE = b"\xff\xd8\xff"


class SurfaceWorkspaceError(ValueError):
    """Raised when a workspace operation is unsafe or malformed."""


@dataclass(frozen=True)
class SurfacePromotionContext:
    """Evidence required before a draft may replace an active surface."""

    maintenance_unlocked: bool
    owner_present: bool
    vehicle_stationary: bool
    physical_control_disabled: bool
    receipt_id: str

    def __post_init__(self) -> None:
        for name in (
            "maintenance_unlocked",
            "owner_present",
            "vehicle_stationary",
            "physical_control_disabled",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError("%s must be boolean" % name)
        if not isinstance(self.receipt_id, str) or not self.receipt_id.strip():
            raise SurfaceWorkspaceError("promotion receipt_id must be non-empty")

    @property
    def allowed(self) -> bool:
        return (
            self.maintenance_unlocked
            and self.owner_present
            and self.vehicle_stationary
            and self.physical_control_disabled
        )

    def denial_reasons(self) -> Tuple[str, ...]:
        reasons = []
        if not self.maintenance_unlocked:
            reasons.append("maintenance is locked")
        if not self.owner_present:
            reasons.append("owner presence is not verified")
        if not self.vehicle_stationary:
            reasons.append("vehicle is not verified stationary")
        if not self.physical_control_disabled:
            reasons.append("physical control is not disabled")
        return tuple(reasons)


@dataclass(frozen=True)
class SurfacePromotionResult:
    surface_name: str
    manifest_path: Path
    background_path: Path
    receipt_id: str
    promoted_at: float


class SurfaceWorkspace:
    """Own drafts, imported artwork, backups, and active promotions."""

    def __init__(
        self,
        workspace_root: Path,
        active_surface_dir: Path,
        max_asset_bytes: int = 32 * 1024 * 1024,
    ) -> None:
        if isinstance(max_asset_bytes, bool) or not isinstance(max_asset_bytes, int):
            raise TypeError("max_asset_bytes must be an integer")
        if max_asset_bytes < 1024 or max_asset_bytes > 512 * 1024 * 1024:
            raise SurfaceWorkspaceError("max_asset_bytes is outside supported bounds")

        self.root = Path(workspace_root).expanduser().resolve()
        self.active_surface_dir = Path(active_surface_dir).expanduser().resolve()
        self.drafts_dir = self.root / "drafts"
        self.assets_dir = self.root / "assets"
        self.backups_dir = self.root / "backups"
        self.receipts_path = self.root / "receipts" / "surface-promotions.jsonl"
        self.camera_receipts_path = self.root / "receipts" / "camera-captures.jsonl"
        self.max_asset_bytes = max_asset_bytes
        self._ensure_directories()

    def list_drafts(self) -> Tuple[str, ...]:
        names = []
        for path in sorted(self.drafts_dir.glob("*.surface.yaml")):
            name = path.name[: -len(".surface.yaml")]
            if _NAME_PATTERN.fullmatch(name):
                names.append(name)
        return tuple(names)

    def draft_path(self, surface_name: str) -> Path:
        name = _validated_name(surface_name)
        return self.drafts_dir / (name + ".surface.yaml")

    def import_background(self, source_path: Path, surface_name: str) -> Path:
        """Copy one verified PNG/JPEG into the private draft asset directory."""

        name = _validated_name(surface_name)
        raw_source = Path(source_path).expanduser()
        if raw_source.is_symlink():
            raise SurfaceWorkspaceError("background source cannot be a symlink")
        source = raw_source.resolve()
        if not source.is_file():
            raise SurfaceWorkspaceError("background source must be a regular file")
        suffix = source.suffix.lower()
        if suffix not in _ALLOWED_EXTENSIONS:
            raise SurfaceWorkspaceError("background must be PNG or JPEG")
        size = source.stat().st_size
        if size < 8 or size > self.max_asset_bytes:
            raise SurfaceWorkspaceError("background asset size is outside supported bounds")
        _verify_image_signature(source, suffix)

        digest = _sha256_file(source)[:16]
        target = self.assets_dir / ("%s-%s%s" % (name, digest, suffix))
        if target.is_file():
            return target
        _copy_atomic(source, target, 0o600)
        return target

    def import_camera_frame(
        self,
        frame: CapturedCameraFrame,
        surface_name: str,
    ) -> Path:
        """Store one trustworthy current camera still and append its receipt."""

        if not isinstance(frame, CapturedCameraFrame):
            raise TypeError("frame must be a CapturedCameraFrame")
        name = _validated_name(surface_name)
        if len(frame.image_bytes) > self.max_asset_bytes:
            raise SurfaceWorkspaceError("captured camera frame exceeds the asset limit")

        digest = hashlib.sha256(frame.image_bytes).hexdigest()[:16]
        target = self.assets_dir / ("%s-camera-%s%s" % (name, digest, frame.suffix))
        _write_atomic_bytes(target, frame.image_bytes, 0o600)
        receipt = {
            "schema": "velvet.interface.camera_capture_receipt.v1",
            "receipt_id": frame.receipt_id.strip(),
            "surface_name": name,
            "source_id": frame.source_id.strip(),
            "captured_at": float(frame.captured_at),
            "stored_at": time.time(),
            "asset_path": str(target),
            "asset_sha256": hashlib.sha256(frame.image_bytes).hexdigest(),
            "image_format": frame.image_format.lower(),
            "authority": "none",
            "actuation_granted": False,
            "actuation_performed": False,
        }
        _append_jsonl(self.camera_receipts_path, receipt)
        return target

    def create_blank_background(
        self,
        surface_name: str,
        png_bytes: bytes,
    ) -> Path:
        """Store PNG bytes produced by the trusted Qt canvas composer."""

        name = _validated_name(surface_name)
        if not isinstance(png_bytes, bytes) or not png_bytes.startswith(_PNG_SIGNATURE):
            raise SurfaceWorkspaceError("blank background must be encoded PNG bytes")
        if len(png_bytes) > self.max_asset_bytes:
            raise SurfaceWorkspaceError("generated background exceeds the asset limit")
        digest = hashlib.sha256(png_bytes).hexdigest()[:16]
        target = self.assets_dir / ("%s-%s.png" % (name, digest))
        _write_atomic_bytes(target, png_bytes, 0o600)
        return target

    def create_session(
        self,
        surface_name: str,
        background_path: Path,
        base_resolution: Tuple[int, int],
        fit_mode: str = "cover",
    ) -> SurfaceLayoutAuthoringSession:
        name = _validated_name(surface_name)
        background = Path(background_path).expanduser().resolve()
        _require_managed_asset(background, self.assets_dir)
        return SurfaceLayoutAuthoringSession(
            name=name,
            background_path=str(background),
            base_resolution=base_resolution,
            fit_mode=fit_mode,
            metadata={
                "authoring_surface": "surface_studio",
                "draft_only": True,
                "grants_authority": False,
                "grants_execution": False,
                "grants_actuation": False,
            },
        )

    def load_draft(self, surface_name: str) -> SurfaceLayoutAuthoringSession:
        path = self.draft_path(surface_name)
        if not path.is_file():
            raise FileNotFoundError("surface draft not found: %s" % surface_name)
        session = SurfaceLayoutAuthoringSession.load(str(path))
        _require_managed_asset(Path(session.background_path), self.assets_dir)
        return session

    def save_draft(self, session: SurfaceLayoutAuthoringSession) -> Path:
        if not isinstance(session, SurfaceLayoutAuthoringSession):
            raise TypeError("session must be a SurfaceLayoutAuthoringSession")
        name = _validated_name(session.name)
        _require_managed_asset(Path(session.background_path), self.assets_dir)
        session.metadata.update(
            {
                "authoring_surface": "surface_studio",
                "draft_only": True,
                "grants_authority": False,
                "grants_execution": False,
                "grants_actuation": False,
            }
        )
        path = session.save(str(self.draft_path(name)))
        os.chmod(str(path), 0o600)
        self.validate_draft(name)
        return path

    def validate_draft(self, surface_name: str) -> Dict[str, Any]:
        name = _validated_name(surface_name)
        path = self.draft_path(name)
        manifest = SurfaceManifestLoader().load(str(path), require_background=True)
        _require_managed_asset(Path(manifest.background.image_path), self.assets_dir)
        return {
            "surface_name": name,
            "manifest_path": str(path),
            "background_path": manifest.background.image_path,
            "press_point_count": len(manifest.press_points),
            "widget_count": len(manifest.widgets),
            "valid": True,
            "draft_only": True,
            "authority": "none",
            "actuation_granted": False,
            "actuation_performed": False,
        }

    def promote(
        self,
        surface_name: str,
        context: SurfacePromotionContext,
    ) -> SurfacePromotionResult:
        """Promote a validated draft into the active surface directory.

        Promotion is local presentation configuration only. The evidence gate is
        deliberately stricter than ordinary draft editing because an active
        interface change can obscure or relocate controls.
        """

        if not isinstance(context, SurfacePromotionContext):
            raise TypeError("context must be a SurfacePromotionContext")
        if not context.allowed:
            raise PermissionError("surface promotion blocked: %s" % ", ".join(context.denial_reasons()))

        name = _validated_name(surface_name)
        self.validate_draft(name)
        draft = self.load_draft(name)
        active_assets = self.active_surface_dir / "assets"
        active_assets.mkdir(parents=True, exist_ok=True)
        os.chmod(str(active_assets), 0o750)

        source_background = Path(draft.background_path).resolve()
        background_target = active_assets / source_background.name
        _copy_atomic(source_background, background_target, 0o640)

        active_manifest = self.active_surface_dir / (name + ".surface.yaml")
        self._backup_active(name, active_manifest)

        promoted_session = SurfaceLayoutAuthoringSession(
            name=draft.name,
            background_path=str(background_target),
            base_resolution=draft.base_resolution,
            fit_mode=draft.fit_mode,
            press_points=list(draft.press_points),
            widgets=list(draft.widgets),
            metadata=dict(draft.metadata),
            enter_transition=draft.enter_transition,
            exit_transition=draft.exit_transition,
        )
        promoted_session.metadata.update(
            {
                "draft_only": False,
                "promoted_by": "surface_studio",
                "promotion_receipt_id": context.receipt_id.strip(),
                "grants_authority": False,
                "grants_execution": False,
                "grants_actuation": False,
            }
        )
        self.active_surface_dir.mkdir(parents=True, exist_ok=True)
        saved = promoted_session.save(str(active_manifest))
        os.chmod(str(saved), 0o640)
        SurfaceManifestLoader().load(str(saved), require_background=True)

        promoted_at = time.time()
        receipt = {
            "schema": "velvet.interface.surface_promotion_receipt.v1",
            "receipt_id": context.receipt_id.strip(),
            "surface_name": name,
            "draft_manifest": str(self.draft_path(name)),
            "active_manifest": str(saved),
            "active_background": str(background_target),
            "promoted_at": promoted_at,
            "maintenance_unlocked": True,
            "owner_present": True,
            "vehicle_stationary": True,
            "physical_control_disabled": True,
            "authority": "none",
            "actuation_granted": False,
            "actuation_performed": False,
        }
        _append_jsonl(self.receipts_path, receipt)
        return SurfacePromotionResult(
            surface_name=name,
            manifest_path=saved,
            background_path=background_target,
            receipt_id=context.receipt_id.strip(),
            promoted_at=promoted_at,
        )

    def _backup_active(self, surface_name: str, active_manifest: Path) -> None:
        if not active_manifest.is_file():
            return
        stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        target_dir = self.backups_dir / (surface_name + "-" + stamp)
        target_dir.mkdir(parents=True, exist_ok=False)
        os.chmod(str(target_dir), 0o700)
        _copy_atomic(active_manifest, target_dir / active_manifest.name, 0o600)
        try:
            manifest = SurfaceManifestLoader().load(str(active_manifest), require_background=True)
            background = Path(manifest.background.image_path)
            if background.is_file():
                _copy_atomic(background, target_dir / background.name, 0o600)
        except (OSError, TypeError, ValueError):
            # A damaged old active surface must not block a known-good promotion.
            pass

    def _ensure_directories(self) -> None:
        for path in (self.root, self.drafts_dir, self.assets_dir, self.backups_dir):
            path.mkdir(parents=True, exist_ok=True)
            os.chmod(str(path), 0o700)


def _validated_name(value: str) -> str:
    if not isinstance(value, str) or not _NAME_PATTERN.fullmatch(value.strip()):
        raise SurfaceWorkspaceError(
            "surface name must match [a-z][a-z0-9_-]{0,63}"
        )
    return value.strip()


def _require_managed_asset(path: Path, asset_root: Path) -> None:
    resolved = Path(path).expanduser().resolve()
    root = Path(asset_root).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise SurfaceWorkspaceError("surface artwork must live in the managed draft asset directory")
    if resolved.is_symlink() or not resolved.is_file():
        raise SurfaceWorkspaceError("managed surface artwork is unavailable")


def _verify_image_signature(path: Path, suffix: str) -> None:
    with path.open("rb") as handle:
        prefix = handle.read(8)
    if suffix == ".png" and prefix != _PNG_SIGNATURE:
        raise SurfaceWorkspaceError("PNG signature is invalid")
    if suffix in {".jpg", ".jpeg"} and not prefix.startswith(_JPEG_SIGNATURE):
        raise SurfaceWorkspaceError("JPEG signature is invalid")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _copy_atomic(source: Path, target: Path, mode: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % target.name,
        dir=str(target.parent),
    )
    try:
        with os.fdopen(descriptor, "wb") as output, source.open("rb") as input_handle:
            shutil.copyfileobj(input_handle, output, length=1024 * 1024)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, str(target))
        os.chmod(str(target), mode)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _write_atomic_bytes(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name,
        dir=str(path.parent),
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, str(path))
        os.chmod(str(path), mode)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _append_jsonl(path: Path, document: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(str(path.parent), 0o700)
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        line = json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"
        os.write(descriptor, line.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
