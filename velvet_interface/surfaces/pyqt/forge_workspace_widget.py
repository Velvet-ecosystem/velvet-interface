# SPDX-License-Identifier: GPL-3.0-only
"""Transparent live-data overlays for the Founder Forge scroll."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from velvet_interface.eleanor_bridge import EleanorUnavailable
from velvet_interface.forge_workspace_bridges import ForgeWorkspaceUnavailable


_TITLES = {
    "engineering_design": "ENGINEERING DESIGN",
    "module_lab": "MODULE LAB / HARDWARE ENGINEERING",
    "test_bench": "TEST BENCH / VALIDATION",
}

# Founder physical review showed the title can safely move upward between the
# scroll-line ornaments. Preserve the measured left/right/bottom bounds while
# extending the writing frame upward to expose more vertical text capacity.
_SCROLL_CONTENT_RECT = (0.175347, 0.180000, 0.647570, 0.590062)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    return value if isinstance(value, (list, tuple)) else ()


def _lines(items: Sequence[Any], *, prefix: str = "• ", limit: int = 8) -> str:
    rendered = []
    for item in items[:limit]:
        text = str(item).strip()
        if text:
            rendered.append(prefix + text)
    return "\n".join(rendered) if rendered else "None recorded"


class QtForgeWorkspaceWidget(QWidget):
    """Render canonical read-only Forge evidence as ink over the scroll artwork."""

    def __init__(
        self,
        workspace_id: str,
        snapshot_provider: Callable[[], Mapping[str, Any]],
        *,
        development_mode: bool = False,
        refresh_ms: int = 5000,
    ) -> None:
        if workspace_id not in _TITLES:
            raise ValueError("unsupported Forge workspace: %s" % workspace_id)
        if not callable(snapshot_provider):
            raise TypeError("snapshot_provider must be callable")
        if not 1000 <= int(refresh_ms) <= 60000:
            raise ValueError("refresh_ms must be between 1000 and 60000")
        super().__init__()
        self.workspace_id = workspace_id
        self.snapshot_provider = snapshot_provider
        self.development_mode = bool(development_mode)

        # The parent image scene owns clicks. This overlay is deliberately ink,
        # not a second opaque application surface.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet(
            "QWidget { background: transparent; color: #2d1c11; }"
            "QLabel { background: transparent; color: #2d1c11; }"
            "QLabel#forgeNav { font-size: 13px; font-weight: 600; color: #5b3520; }"
            "QLabel#forgeTitle { font-size: 27px; font-weight: 700; color: #3a2214; }"
            "QLabel#forgeStatus { font-size: 13px; color: #65452f; }"
            "QLabel#forgeSection { font-size: 15px; font-weight: 700; color: #4d2d1a; }"
            "QLabel#forgeBody { font-size: 13px; color: #2d1c11; }"
            "QLabel#forgeFooter { font-size: 11px; font-weight: 600; color: #704b32; }"
        )

        # Keep the navigation labels in their existing top-screen positions so
        # they continue to line up with the separate image-surface press points.
        root = QVBoxLayout(self)
        root.setContentsMargins(66, 28, 66, 30)
        root.setSpacing(0)

        nav = QHBoxLayout()
        back = QLabel("‹ FORGE")
        back.setObjectName("forgeNav")
        back.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        emergency = QLabel("EMERGENCY ›")
        emergency.setObjectName("forgeNav")
        emergency.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        nav.addWidget(back)
        nav.addStretch(1)
        nav.addWidget(emergency)
        root.addLayout(nav)
        root.addStretch(1)

        # The actual workspace ink lives in a physically measured frame inside
        # the parchment artwork. All three Forge workspaces share this widget and
        # therefore share the same Founder-mapped writing area.
        self.content_frame = QWidget(self)
        self.content_frame.setAttribute(Qt.WA_TranslucentBackground, True)
        self.content_frame.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        content = QVBoxLayout(self.content_frame)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(8)

        title = QLabel(_TITLES[workspace_id])
        title.setObjectName("forgeTitle")
        title.setAlignment(Qt.AlignCenter)
        content.addWidget(title)

        self.status = QLabel("Reading canonical workspace evidence…")
        self.status.setObjectName("forgeStatus")
        self.status.setAlignment(Qt.AlignCenter)
        content.addWidget(self.status)

        body = QHBoxLayout()
        body.setSpacing(26)
        left = QVBoxLayout()
        right = QVBoxLayout()
        self.left_title = QLabel()
        self.left_title.setObjectName("forgeSection")
        self.left_body = QLabel()
        self.left_body.setObjectName("forgeBody")
        self.left_body.setWordWrap(True)
        self.left_body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.right_title = QLabel()
        self.right_title.setObjectName("forgeSection")
        self.right_body = QLabel()
        self.right_body.setObjectName("forgeBody")
        self.right_body.setWordWrap(True)
        self.right_body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        left.addWidget(self.left_title)
        left.addWidget(self.left_body, 1)
        right.addWidget(self.right_title)
        right.addWidget(self.right_body, 1)
        body.addLayout(left, 1)
        body.addLayout(right, 1)
        content.addLayout(body, 1)

        self.footer = QLabel()
        self.footer.setObjectName("forgeFooter")
        self.footer.setAlignment(Qt.AlignCenter)
        prefix = "DEVELOPMENT • " if self.development_mode else ""
        self.footer.setText(
            prefix
            + "PRESENTATION AUTHORITY ONLY • PHYSICAL EXECUTION DISABLED"
        )
        content.addWidget(self.footer)
        self._position_content_frame()

        self.timer = QTimer(self)
        self.timer.setInterval(int(refresh_ms))
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def _position_content_frame(self) -> None:
        x, y, width, height = _SCROLL_CONTENT_RECT
        self.content_frame.setGeometry(
            int(round(self.width() * x)),
            int(round(self.height() * y)),
            max(1, int(round(self.width() * width))),
            max(1, int(round(self.height() * height))),
        )
        self.content_frame.raise_()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        if hasattr(self, "content_frame"):
            self._position_content_frame()

    def refresh(self) -> None:
        try:
            snapshot = self.snapshot_provider()
            if not isinstance(snapshot, Mapping):
                raise TypeError("workspace snapshot must be a mapping")
            if self.workspace_id == "engineering_design":
                self._render_engineering(snapshot)
            elif self.workspace_id == "module_lab":
                self._render_module_lab(snapshot)
            else:
                self._render_test_bench(snapshot)
        except (ForgeWorkspaceUnavailable, EleanorUnavailable, OSError, TypeError, ValueError) as exc:
            self.status.setText("Canonical workspace evidence unavailable")
            self.left_title.setText("STATUS")
            self.left_body.setText(str(exc))
            self.right_title.setText("BOUNDARY")
            self.right_body.setText(
                "No synthetic success state was created.\n"
                "Mutation and physical execution remain unavailable."
            )

    def _render_engineering(self, snapshot: Mapping[str, Any]) -> None:
        project = _mapping(snapshot.get("project"))
        intent = _mapping(snapshot.get("intent"))
        counts = _mapping(snapshot.get("counts"))
        authority = _mapping(snapshot.get("authority"))
        handoff = _mapping(snapshot.get("handoff"))
        validation = _mapping(snapshot.get("validation"))
        self.status.setText(
            "%s • lifecycle=%s • revision=%s • errors=%s warnings=%s"
            % (
                project.get("id", "project"),
                project.get("lifecycle", "unknown"),
                project.get("revision", "?"),
                validation.get("errors", 0),
                validation.get("warnings", 0),
            )
        )
        self.left_title.setText("PROJECT / DESIGN LEDGER")
        self.left_body.setText(
            "%s\n\n%s\n\nIntent\n%s\n\nDesired outcome\n%s"
            % (
                project.get("name", "Unnamed project"),
                project.get("description", ""),
                intent.get("statement", ""),
                intent.get("desired_outcome", ""),
            )
        )
        self.right_title.setText("STATE / NEXT WORK")
        self.right_body.setText(
            "Record status: %s\nAuthority gate: %s\n"
            "Requirements: %s   Assumptions: %s\n"
            "Evidence: %s   Decisions: %s\n"
            "Artifacts: %s   Calculations: %s\n"
            "Risks: %s   Approvals: %s\n\n"
            "Handoff: %s\n%s\n\nRecommended next actions\n%s"
            % (
                snapshot.get("record_status", "unknown"),
                authority.get("current_gate", "unknown"),
                counts.get("requirements", 0),
                counts.get("assumptions", 0),
                counts.get("evidence", 0),
                counts.get("decisions", 0),
                counts.get("artifacts", 0),
                counts.get("calculations", 0),
                counts.get("risks", 0),
                counts.get("approvals", 0),
                handoff.get("status", "unknown"),
                handoff.get("summary", ""),
                _lines(_sequence(handoff.get("recommended_next_actions")), limit=6),
            )
        )

    def _render_module_lab(self, snapshot: Mapping[str, Any]) -> None:
        candidates = _sequence(snapshot.get("candidates"))
        intake = _sequence(snapshot.get("intake"))
        reports = _sequence(snapshot.get("reports"))
        promoted = _sequence(snapshot.get("promoted_domains"))
        self.status.setText(
            "%d candidates • %d intake records • %d reports • read-only"
            % (len(candidates), len(intake), len(reports))
        )
        self.left_title.setText("LAB CANDIDATES")
        self.left_body.setText(
            _lines(candidates, limit=14)
            + "\n\nINTAKE\n"
            + _lines(intake, limit=7)
        )
        self.right_title.setText("VALIDATION / PROMOTION EVIDENCE")
        self.right_body.setText(
            "Reports\n%s\n\nPromoted module domains\n%s\n\n"
            "Lab state is evidence only. Presence here does not grant Runtime, Court, "
            "deployment, or hardware authority."
            % (_lines(reports, limit=9), _lines(promoted, limit=10))
        )

    def _render_test_bench(self, snapshot: Mapping[str, Any]) -> None:
        validation = _mapping(snapshot.get("validation"))
        artifact = _mapping(snapshot.get("artifact_validation"))
        coverage = _mapping(snapshot.get("coverage"))
        summary = _mapping(coverage.get("summary"))
        issues = _sequence(validation.get("issues"))
        artifact_issues = _sequence(artifact.get("issues"))
        requirements = _sequence(coverage.get("requirements"))
        self.status.setText(
            "validation errors=%s warnings=%s • artifact errors=%s warnings=%s"
            % (
                validation.get("errors", 0),
                validation.get("warnings", 0),
                artifact.get("errors", 0),
                artifact.get("warnings", 0),
            )
        )
        issue_lines = []
        for issue in issues[:8]:
            item = _mapping(issue)
            issue_lines.append(
                "%s %s: %s"
                % (
                    str(item.get("severity", "")).upper(),
                    item.get("code", ""),
                    item.get("message", ""),
                )
            )
        for issue in artifact_issues[:4]:
            item = _mapping(issue)
            issue_lines.append(
                "ARTIFACT %s %s: %s"
                % (
                    str(item.get("severity", "")).upper(),
                    item.get("code", ""),
                    item.get("message", ""),
                )
            )
        self.left_title.setText("VALIDATION EVIDENCE")
        self.left_body.setText(
            "Eleanor structural validation and registered-artifact re-read are live.\n\n"
            + ("\n".join(issue_lines) if issue_lines else "No validation issues reported.")
        )
        coverage_lines = []
        for row in requirements[:12]:
            item = _mapping(row)
            coverage_lines.append(
                "%s  [%s]  %s / %s"
                % (
                    item.get("id", ""),
                    item.get("priority", ""),
                    item.get("status", ""),
                    item.get("coverage", ""),
                )
            )
        summary_text = "  ".join(
            "%s=%s" % (key, value) for key, value in sorted(summary.items())
        )
        self.right_title.setText("REQUIREMENT COVERAGE")
        self.right_body.setText(
            (summary_text or "No coverage summary")
            + "\n\n"
            + ("\n".join(coverage_lines) if coverage_lines else "No requirements reported.")
            + "\n\nPassing validation is evidence, not fabrication or execution authority."
        )
