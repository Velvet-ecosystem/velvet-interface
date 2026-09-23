# SPDX-License-Identifier: GPL-3.0-only
"""Read-only evidence bridges for Founder Forge workspaces.

The Forge presentation layer may inspect canonical engineering and module-lab
state, but it does not own either domain and it never gains mutation or physical
execution authority from these adapters.
"""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import yaml

from velvet_interface.eleanor_bridge import EleanorBridge, EleanorUnavailable


MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_DIRECTORY_ENTRIES = 512
MAX_PRESENTED_ITEMS = 24


class ForgeWorkspaceUnavailable(RuntimeError):
    """Raised when canonical Forge evidence cannot be read safely."""


def _text(value: Any, *, limit: int = 1200) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text[:limit]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, (list, tuple)):
        return value
    return ()


def _string_items(value: Any, *, limit: int = MAX_PRESENTED_ITEMS) -> List[str]:
    result = []
    for item in _sequence(value):
        if isinstance(item, str) and item.strip():
            result.append(item.strip()[:240])
        if len(result) >= limit:
            break
    return result


def _collection_count(value: Any) -> int:
    if isinstance(value, Mapping):
        return len(value)
    if isinstance(value, (list, tuple)):
        return len(value)
    return 0


def _read_yaml_mapping(path: Path) -> Mapping[str, Any]:
    target = Path(path).expanduser()
    try:
        metadata = target.lstat()
    except OSError as exc:
        raise ForgeWorkspaceUnavailable("engineering manifest unavailable: %s" % exc) from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise ForgeWorkspaceUnavailable("engineering manifest must not be a symlink")
    if not stat.S_ISREG(metadata.st_mode):
        raise ForgeWorkspaceUnavailable("engineering manifest must be a regular file")
    if not 2 <= metadata.st_size <= MAX_MANIFEST_BYTES:
        raise ForgeWorkspaceUnavailable("engineering manifest size is outside supported bounds")
    try:
        raw = target.read_bytes()
    except OSError as exc:
        raise ForgeWorkspaceUnavailable("engineering manifest could not be read: %s" % exc) from exc
    if len(raw) != metadata.st_size:
        raise ForgeWorkspaceUnavailable("engineering manifest changed during read")
    try:
        document = yaml.safe_load(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ForgeWorkspaceUnavailable("engineering manifest is not valid UTF-8 YAML") from exc
    if not isinstance(document, Mapping):
        raise ForgeWorkspaceUnavailable("engineering manifest root must be a mapping")
    if document.get("schema") != "velvet.eleanor.engineering-project":
        raise ForgeWorkspaceUnavailable("unsupported Eleanor engineering manifest schema")
    return document


def _directory(path: Path, label: str) -> Path:
    target = Path(path).expanduser()
    try:
        metadata = target.lstat()
    except OSError as exc:
        raise ForgeWorkspaceUnavailable("%s unavailable: %s" % (label, exc)) from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise ForgeWorkspaceUnavailable("%s must not be a symlink" % label)
    if not stat.S_ISDIR(metadata.st_mode):
        raise ForgeWorkspaceUnavailable("%s must be a directory" % label)
    return target


def _bounded_children(path: Path) -> List[Path]:
    try:
        children = sorted(path.iterdir(), key=lambda item: item.name.casefold())
    except OSError as exc:
        raise ForgeWorkspaceUnavailable("workspace directory could not be listed: %s" % exc) from exc
    if len(children) > MAX_DIRECTORY_ENTRIES:
        raise ForgeWorkspaceUnavailable("workspace directory exceeds presentation entry bound")
    return children


class EngineeringDesignBridge:
    """Project the canonical Eleanor record into a read-only design snapshot."""

    def __init__(self, eleanor: EleanorBridge) -> None:
        self.eleanor = eleanor

    def snapshot(self) -> Dict[str, Any]:
        # Eleanor remains the validator. Interface only projects already-canonical
        # record fields for presentation.
        validation = self.eleanor.validate()
        document = _read_yaml_mapping(self.eleanor.manifest)
        project = _mapping(document.get("project"))
        intent = _mapping(document.get("intent"))
        authority = _mapping(document.get("authority"))
        physical = _mapping(authority.get("physical_execution"))
        handoff = _mapping(document.get("handoff"))

        return {
            "source": str(self.eleanor.manifest),
            "schema_version": _text(document.get("version"), limit=40),
            "record_status": _text(document.get("status"), limit=80),
            "project": {
                "id": _text(project.get("id"), limit=160),
                "name": _text(project.get("name"), limit=240),
                "description": _text(project.get("description")),
                "lifecycle": _text(project.get("lifecycle"), limit=120),
                "revision": project.get("revision"),
            },
            "intent": {
                "statement": _text(intent.get("statement")),
                "desired_outcome": _text(intent.get("desired_outcome")),
            },
            "counts": {
                "requirements": _collection_count(document.get("requirements")),
                "assumptions": _collection_count(document.get("assumptions")),
                "evidence": _collection_count(document.get("evidence")),
                "decisions": _collection_count(document.get("decisions")),
                "artifacts": _collection_count(document.get("artifacts")),
                "calculations": _collection_count(document.get("calculations")),
                "risks": _collection_count(document.get("risks")),
                "approvals": _collection_count(document.get("approvals")),
            },
            "authority": {
                "current_gate": _text(authority.get("current_gate"), limit=120),
                "allowed_actions": _string_items(authority.get("allowed_actions")),
                "prohibited_actions": _string_items(authority.get("prohibited_actions")),
                "physical_execution_allowed": physical.get("allowed") is True,
            },
            "handoff": {
                "status": _text(handoff.get("status"), limit=120),
                "summary": _text(handoff.get("summary")),
                "recommended_next_actions": _string_items(
                    handoff.get("recommended_next_actions"), limit=8
                ),
            },
            "validation": {
                "errors": int(validation.get("errors", 0)),
                "warnings": int(validation.get("warnings", 0)),
            },
        }


class TestBenchBridge:
    """Expose Eleanor validation and artifact checks without execution authority."""

    def __init__(self, eleanor: EleanorBridge) -> None:
        self.eleanor = eleanor

    @staticmethod
    def _issues(payload: Mapping[str, Any]) -> List[Dict[str, str]]:
        result = []
        for issue in _sequence(payload.get("issues")):
            if not isinstance(issue, Mapping):
                continue
            result.append(
                {
                    "severity": _text(issue.get("severity"), limit=40),
                    "code": _text(issue.get("code"), limit=120),
                    "message": _text(issue.get("message"), limit=360),
                }
            )
            if len(result) >= 12:
                break
        return result

    def snapshot(self) -> Dict[str, Any]:
        validation = self.eleanor.validate()
        artifact_validation = self.eleanor.validate_artifacts()
        coverage = self.eleanor.coverage()
        requirements = []
        for row in _sequence(coverage.get("requirements")):
            if not isinstance(row, Mapping):
                continue
            requirements.append(
                {
                    "id": _text(row.get("id"), limit=120),
                    "priority": _text(row.get("priority"), limit=80),
                    "status": _text(row.get("requirement_status"), limit=80),
                    "coverage": _text(row.get("coverage_state"), limit=80),
                }
            )
            if len(requirements) >= 16:
                break

        raw_summary = _mapping(coverage.get("summary"))
        summary = {str(key)[:80]: value for key, value in list(raw_summary.items())[:24]}
        return {
            "source": str(self.eleanor.manifest),
            "validation": {
                "errors": int(validation.get("errors", 0)),
                "warnings": int(validation.get("warnings", 0)),
                "issues": self._issues(validation),
            },
            "artifact_validation": {
                "errors": int(artifact_validation.get("errors", 0)),
                "warnings": int(artifact_validation.get("warnings", 0)),
                "issues": self._issues(artifact_validation),
            },
            "coverage": {
                "summary": summary,
                "requirements": requirements,
            },
        }


class ModuleLabBridge:
    """Inventory canonical Module Lab evidence without loading candidate code."""

    def __init__(self, modules_root: Path) -> None:
        self.modules_root = Path(modules_root).expanduser()

    @staticmethod
    def _regular_names(path: Path, suffixes: Iterable[str]) -> List[str]:
        accepted = tuple(suffix.lower() for suffix in suffixes)
        result = []
        for child in _bounded_children(path):
            try:
                metadata = child.lstat()
            except OSError:
                continue
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                continue
            if child.name.startswith(".") or child.name == "__init__.py":
                continue
            if accepted and child.suffix.lower() not in accepted:
                continue
            result.append(child.name)
            if len(result) >= MAX_PRESENTED_ITEMS:
                break
        return result

    def snapshot(self) -> Dict[str, Any]:
        root = _directory(self.modules_root, "Modules repository")
        lab = _directory(root / "lab", "Module Lab")
        candidates_root = _directory(lab / "candidates", "Module Lab candidates")
        intake_root = _directory(lab / "intake", "Module Lab intake")
        reports_root = _directory(lab / "reports", "Module Lab reports")
        modules_root = _directory(root / "modules", "promoted modules")

        candidates = []
        for child in _bounded_children(candidates_root):
            try:
                metadata = child.lstat()
            except OSError:
                continue
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                continue
            if child.name.startswith("_") or child.name.startswith("."):
                continue
            spec = child / "SPEC.md"
            try:
                spec_metadata = spec.lstat()
            except OSError:
                continue
            if stat.S_ISREG(spec_metadata.st_mode) and not stat.S_ISLNK(spec_metadata.st_mode):
                candidates.append(child.name)
            if len(candidates) >= MAX_PRESENTED_ITEMS:
                break

        promoted_domains = []
        for child in _bounded_children(modules_root):
            try:
                metadata = child.lstat()
            except OSError:
                continue
            if stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
                if not child.name.startswith((".", "_")):
                    promoted_domains.append(child.name)
            if len(promoted_domains) >= MAX_PRESENTED_ITEMS:
                break

        suffixes = (".md", ".json", ".yaml", ".yml", ".txt")
        return {
            "source": str(root),
            "candidates": candidates,
            "intake": self._regular_names(intake_root, suffixes),
            "reports": self._regular_names(reports_root, suffixes),
            "promoted_domains": promoted_domains,
            "read_only": True,
        }
