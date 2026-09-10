# SPDX-License-Identifier: GPL-3.0-only
"""PyQt Character Foundry workspace backed by the canonical Foundry service."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QPainter, QPixmap
    from PyQt5.QtWidgets import (
        QComboBox,
        QFormLayout,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    PYQT_AVAILABLE = False
    QWidget = object  # type: ignore

from velvet_interface.foundry_bridge import FoundryBridge, FoundryUnavailable


BackCallback = Callable[[], Any]


class QtCharacterFoundryWidget(QWidget):
    """Full-screen, authority-free editor for local Foundry candidate drafts.

    The widget never decides candidate validity or promotion itself. Every write
    goes through ``FoundryBridge`` and therefore through Persona Continuity's
    canonical ``FoundryService``.
    """

    KINDS = (
        ("Character", "character"),
        ("Software Module", "software_module"),
        ("Hardware Module", "hardware_module"),
    )

    def __init__(
        self,
        bridge: FoundryBridge,
        target_size: Tuple[int, int],
        background_path: Path,
        on_back: Optional[BackCallback] = None,
    ) -> None:
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is required for Character Foundry")
        super().__init__()
        self.bridge = bridge
        self.target_size = target_size
        self.background_path = Path(background_path)
        self.on_back = on_back
        self._background = QPixmap(str(self.background_path))
        self._mapping = None  # type: Optional[Dict[str, Any]]
        self._content_hash = None  # type: Optional[str]
        self._persisted = False

        self.setObjectName("characterFoundry")
        self.setFixedSize(*target_size)
        self.setStyleSheet(
            "QWidget#characterFoundry { color: #24180f; }"
            "QWidget#foundryPanel { background: rgba(246, 235, 211, 218); border: 1px solid rgba(78, 51, 28, 150); border-radius: 10px; }"
            "QLabel#foundryTitle { font-size: 27px; font-weight: 600; color: #3a2415; }"
            "QLabel#foundrySection { font-size: 16px; font-weight: 600; color: #4e321c; }"
            "QLabel#foundryStatus { color: #67451f; padding: 4px; }"
            "QPushButton { min-height: 34px; padding: 4px 10px; }"
            "QLineEdit, QTextEdit, QComboBox, QSpinBox, QListWidget { background: rgba(255, 252, 244, 235); color: #21170f; }"
            "QTabWidget::pane { background: rgba(246, 235, 211, 205); border: 1px solid rgba(78, 51, 28, 120); }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("CHARACTER FOUNDRY")
        title.setObjectName("foundryTitle")
        self.status_label = QLabel("Local draft workshop")
        self.status_label.setObjectName("foundryStatus")
        self.back_button = QPushButton("Back")
        header.addWidget(title)
        header.addWidget(self.status_label, 1)
        header.addWidget(self.back_button)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(10)
        body.addWidget(self._build_library_panel(), 2)
        body.addWidget(self._build_editor_panel(), 6)
        body.addWidget(self._build_guardrail_panel(), 3)
        root.addLayout(body, 1)

        self.back_button.clicked.connect(self._go_back)
        self.refresh_candidates()
        self._set_editor_enabled(False)

    def paintEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        if self._background.isNull():
            painter.fillRect(self.rect(), Qt.black)
            return
        scaled = self._background.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        x = (scaled.width() - self.width()) // 2
        y = (scaled.height() - self.height()) // 2
        painter.drawPixmap(0, 0, scaled, x, y, self.width(), self.height())

    def _panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("foundryPanel")
        return panel

    def _build_library_panel(self) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        section = QLabel("Draft Library")
        section.setObjectName("foundrySection")
        self.candidate_list = QListWidget()
        self.kind_selector = QComboBox()
        for label, value in self.KINDS:
            self.kind_selector.addItem(label, value)
        self.new_button = QPushButton("New Candidate")
        self.refresh_button = QPushButton("Refresh")
        self.discard_button = QPushButton("Discard Draft")
        layout.addWidget(section)
        layout.addWidget(self.candidate_list, 1)
        layout.addWidget(self.kind_selector)
        layout.addWidget(self.new_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.discard_button)
        self.candidate_list.itemDoubleClicked.connect(lambda _item: self.open_selected())
        self.new_button.clicked.connect(self.new_candidate)
        self.refresh_button.clicked.connect(self.refresh_candidates)
        self.discard_button.clicked.connect(self.discard_current)
        return panel

    def _build_editor_panel(self) -> QWidget:
        panel = self._panel()
        outer = QVBoxLayout(panel)
        row = QHBoxLayout()
        section = QLabel("Candidate Draft")
        section.setObjectName("foundrySection")
        self.open_button = QPushButton("Open")
        self.validate_button = QPushButton("Validate")
        self.save_button = QPushButton("Create Draft")
        row.addWidget(section)
        row.addStretch(1)
        row.addWidget(self.open_button)
        row.addWidget(self.validate_button)
        row.addWidget(self.save_button)
        outer.addLayout(row)

        tabs = QTabWidget()
        tabs.addTab(self._build_identity_tab(), "Identity")
        tabs.addTab(self._build_character_tab(), "Character / Role")
        tabs.addTab(self._build_evidence_tab(), "Evidence")
        tabs.addTab(self._build_advanced_tab(), "Advanced")
        outer.addWidget(tabs, 1)

        self.open_button.clicked.connect(self.open_selected)
        self.validate_button.clicked.connect(self.validate_current)
        self.save_button.clicked.connect(self.save_current)
        return panel

    def _scroll_form(self) -> Tuple[QWidget, QFormLayout]:
        holder = QWidget()
        form = QFormLayout(holder)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)
        shell = QWidget()
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(scroll)
        return shell, form

    def _build_identity_tab(self) -> QWidget:
        shell, form = self._scroll_form()
        self.candidate_id = QLineEdit()
        self.display_name = QLineEdit()
        self.identity_level = QSpinBox()
        self.identity_level.setRange(0, 4)
        self.foundation_mode = QComboBox()
        self.foundation_mode.addItems(["independent", "derived"])
        self.foundation_ref = QLineEdit()
        self.continuity_scope = QComboBox()
        self.continuity_scope.addItems(["deployment", "foundation"])
        self.purpose_summary = QTextEdit()
        self.purpose_summary.setMaximumHeight(92)
        self.target_repository = QLineEdit()
        form.addRow("Candidate ID", self.candidate_id)
        form.addRow("Display name", self.display_name)
        form.addRow("Identity level", self.identity_level)
        form.addRow("Foundation", self.foundation_mode)
        form.addRow("Foundation ref", self.foundation_ref)
        form.addRow("Continuity scope", self.continuity_scope)
        form.addRow("Purpose", self.purpose_summary)
        form.addRow("Target repository", self.target_repository)
        return shell

    def _build_character_tab(self) -> QWidget:
        shell, form = self._scroll_form()
        self.role_enabled = QComboBox()
        self.role_enabled.addItems(["false", "true"])
        self.role_boundary = QTextEdit()
        self.role_boundary.setMaximumHeight(80)
        self.pronouns = QLineEdit()
        self.founding_tendencies = QTextEdit()
        self.founding_tendencies.setPlaceholderText("One tendency per line")
        self.expression_notes = QTextEdit()
        self.expression_notes.setPlaceholderText("One note per line")
        self.capability_requests = QTextEdit()
        self.capability_requests.setPlaceholderText(
            "Optional JSON list of capability request objects. Requests are never grants."
        )
        form.addRow("Operational role", self.role_enabled)
        form.addRow("Responsibility boundary", self.role_boundary)
        form.addRow("Pronouns", self.pronouns)
        form.addRow("Founding tendencies", self.founding_tendencies)
        form.addRow("Expression notes", self.expression_notes)
        form.addRow("Capability requests", self.capability_requests)
        return shell

    def _build_evidence_tab(self) -> QWidget:
        shell, form = self._scroll_form()
        self.recognition_tests = QTextEdit()
        self.recognition_tests.setPlaceholderText("One test per line")
        self.drift_tests = QTextEdit()
        self.drift_tests.setPlaceholderText("One test per line")
        self.privacy_tests = QTextEdit()
        self.privacy_tests.setPlaceholderText("One test per line")
        self.bench_evidence = QTextEdit()
        self.bench_evidence.setPlaceholderText("One evidence reference per line")
        self.required_reviews = QTextEdit()
        self.required_reviews.setPlaceholderText("One review requirement per line")
        self.required_evidence = QTextEdit()
        self.required_evidence.setPlaceholderText("One evidence requirement per line")
        form.addRow("Recognition tests", self.recognition_tests)
        form.addRow("Drift tests", self.drift_tests)
        form.addRow("Privacy tests", self.privacy_tests)
        form.addRow("Bench evidence", self.bench_evidence)
        form.addRow("Required reviews", self.required_reviews)
        form.addRow("Required evidence", self.required_evidence)
        return shell

    def _build_advanced_tab(self) -> QWidget:
        shell = QWidget()
        layout = QVBoxLayout(shell)
        note = QLabel(
            "Canonical candidate JSON. Validation and persistence still pass through Persona Continuity."
        )
        note.setWordWrap(True)
        self.advanced_json = QTextEdit()
        self.reload_json_button = QPushButton("Reload From Structured Fields")
        self.apply_json_button = QPushButton("Apply JSON To Draft")
        layout.addWidget(note)
        layout.addWidget(self.advanced_json, 1)
        controls = QHBoxLayout()
        controls.addWidget(self.reload_json_button)
        controls.addWidget(self.apply_json_button)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.reload_json_button.clicked.connect(self.reload_advanced_json)
        self.apply_json_button.clicked.connect(self.apply_advanced_json)
        return shell

    def _build_guardrail_panel(self) -> QWidget:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        section = QLabel("Foundry Guardrails")
        section.setObjectName("foundrySection")
        layout.addWidget(section)
        guardrails = (
            "Authority: NONE",
            "Capability grants: NONE",
            "Court tokens: NONE",
            "Execution: DISABLED",
            "Actuation: DISABLED",
            "Canonical memory write: DISABLED",
            "Lineage certification: DISABLED",
            "Automatic merge/deploy: DISABLED",
        )
        for text in guardrails:
            label = QLabel("🔒  " + text)
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addSpacing(12)
        promotion = QLabel("Promotion Review")
        promotion.setObjectName("foundrySection")
        self.promotion_output = QTextEdit()
        self.promotion_output.setReadOnly(True)
        self.promotion_output.setPlaceholderText(
            "Promotion remains external-review-required. Handoffs appear here."
        )
        self.promotion_button = QPushButton("Prepare Promotion Review")
        layout.addWidget(promotion)
        layout.addWidget(self.promotion_output, 1)
        layout.addWidget(self.promotion_button)
        self.promotion_button.clicked.connect(self.propose_promotion)
        return panel

    @staticmethod
    def _lines(editor: QTextEdit) -> list:
        return [line.strip() for line in editor.toPlainText().splitlines() if line.strip()]

    @staticmethod
    def _set_lines(editor: QTextEdit, values: Any) -> None:
        editor.setPlainText("\n".join(str(value) for value in (values or [])))

    def _set_editor_enabled(self, enabled: bool) -> None:
        for widget in (
            self.validate_button,
            self.save_button,
            self.discard_button,
            self.promotion_button,
            self.candidate_id,
            self.display_name,
            self.identity_level,
            self.foundation_mode,
            self.foundation_ref,
            self.continuity_scope,
            self.purpose_summary,
            self.target_repository,
            self.role_enabled,
            self.role_boundary,
            self.pronouns,
            self.founding_tendencies,
            self.expression_notes,
            self.capability_requests,
            self.recognition_tests,
            self.drift_tests,
            self.privacy_tests,
            self.bench_evidence,
            self.required_reviews,
            self.required_evidence,
            self.advanced_json,
            self.reload_json_button,
            self.apply_json_button,
        ):
            widget.setEnabled(enabled)

    def refresh_candidates(self) -> None:
        try:
            candidates = self.bridge.list_candidates()
        except (FoundryUnavailable, FileNotFoundError, OSError, TypeError, ValueError) as exc:
            self._status("Foundry unavailable: %s" % exc)
            return
        selected = self.candidate_list.currentItem().text() if self.candidate_list.currentItem() else ""
        self.candidate_list.clear()
        for candidate in candidates:
            candidate_id = self._candidate_id_from_result(candidate)
            if candidate_id:
                self.candidate_list.addItem(candidate_id)
        if selected:
            matches = self.candidate_list.findItems(selected, Qt.MatchExactly)
            if matches:
                self.candidate_list.setCurrentItem(matches[0])
        self._status("%d local draft%s" % (len(candidates), "" if len(candidates) == 1 else "s"))

    def new_candidate(self) -> None:
        candidate_id, accepted = QInputDialog.getText(self, "New candidate", "Stable candidate ID")
        candidate_id = candidate_id.strip()
        if not accepted or not candidate_id:
            return
        kind = str(self.kind_selector.currentData())
        display_name = ""
        if kind == "character":
            display_name, accepted = QInputDialog.getText(self, "Character name", "Display name")
            display_name = display_name.strip()
            if not accepted or not display_name:
                return
        try:
            mapping = self.bridge.scaffold(candidate_id, kind, display_name=display_name)
        except (FoundryUnavailable, OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Scaffold rejected", str(exc))
            return
        self._mapping = copy.deepcopy(mapping)
        self._content_hash = None
        self._persisted = False
        self._load_mapping(self._mapping)
        self._set_editor_enabled(True)
        self.candidate_id.setEnabled(True)
        self.save_button.setText("Create Draft")
        self._status("New %s scaffold. Not yet persisted." % kind.replace("_", " "))

    def open_selected(self) -> None:
        item = self.candidate_list.currentItem()
        if item is None:
            self._status("Select a saved draft first")
            return
        try:
            result = self.bridge.inspect(item.text())
        except (FoundryUnavailable, FileNotFoundError, OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Draft unavailable", str(exc))
            return
        mapping, content_hash = self._mapping_and_hash(result)
        self._mapping = mapping
        self._content_hash = content_hash
        self._persisted = True
        self._load_mapping(mapping)
        self._set_editor_enabled(True)
        self.candidate_id.setEnabled(False)
        self.save_button.setText("Update Draft")
        self._status("Opened %s" % item.text())

    def _load_mapping(self, mapping: Dict[str, Any]) -> None:
        candidate = mapping.get("candidate", {})
        foundation = mapping.get("foundation", {})
        purpose = mapping.get("purpose", {})
        role = mapping.get("operational_role", {})
        character = mapping.get("character", {})
        validation = mapping.get("validation", {})
        promotion = mapping.get("promotion", {})
        self.candidate_id.setText(str(candidate.get("candidate_id", "")))
        self.display_name.setText(str(candidate.get("display_name", "") or ""))
        self.identity_level.setValue(int(candidate.get("identity_level", 0)))
        self.foundation_mode.setCurrentText(str(foundation.get("mode", "independent")))
        self.foundation_ref.setText(str(foundation.get("foundation_ref", "") or ""))
        self.continuity_scope.setCurrentText(str(foundation.get("continuity_scope", "deployment")))
        self.purpose_summary.setPlainText(str(purpose.get("summary", "")))
        self.target_repository.setText(str(promotion.get("target_repository", "") or ""))
        self.role_enabled.setCurrentText("true" if role.get("enabled") else "false")
        self.role_boundary.setPlainText(str(role.get("responsibility_boundary", "")))
        self.pronouns.setText(str(character.get("pronouns", "") or ""))
        self._set_lines(self.founding_tendencies, character.get("founding_tendencies"))
        self._set_lines(self.expression_notes, character.get("expression_notes"))
        self.capability_requests.setPlainText(
            json.dumps(mapping.get("capability_requests", []), indent=2, sort_keys=True)
        )
        self._set_lines(self.recognition_tests, validation.get("recognition_tests"))
        self._set_lines(self.drift_tests, validation.get("drift_tests"))
        self._set_lines(self.privacy_tests, validation.get("privacy_tests"))
        self._set_lines(self.bench_evidence, validation.get("bench_evidence_refs"))
        self._set_lines(self.required_reviews, promotion.get("required_reviews"))
        self._set_lines(self.required_evidence, promotion.get("required_evidence"))
        self.advanced_json.setPlainText(json.dumps(mapping, indent=2, sort_keys=True))
        self.promotion_output.clear()

    def _structured_mapping(self) -> Dict[str, Any]:
        if self._mapping is None:
            raise ValueError("No candidate draft is open")
        mapping = copy.deepcopy(self._mapping)
        candidate = mapping["candidate"]
        candidate["candidate_id"] = self.candidate_id.text().strip()
        candidate["display_name"] = self.display_name.text().strip()
        candidate["identity_level"] = int(self.identity_level.value())
        foundation = mapping["foundation"]
        foundation["mode"] = self.foundation_mode.currentText()
        foundation_ref = self.foundation_ref.text().strip()
        foundation["foundation_ref"] = foundation_ref or None
        foundation["continuity_scope"] = self.continuity_scope.currentText()
        mapping["purpose"]["summary"] = self.purpose_summary.toPlainText().strip()
        role = mapping["operational_role"]
        role["enabled"] = self.role_enabled.currentText() == "true"
        role["responsibility_boundary"] = self.role_boundary.toPlainText().strip()
        character = mapping["character"]
        character["pronouns"] = self.pronouns.text().strip() or None
        character["founding_tendencies"] = self._lines(self.founding_tendencies)
        character["expression_notes"] = self._lines(self.expression_notes)
        try:
            capability_requests = json.loads(self.capability_requests.toPlainText() or "[]")
        except ValueError as exc:
            raise ValueError("Capability requests must be valid JSON: %s" % exc)
        if not isinstance(capability_requests, list):
            raise ValueError("Capability requests must be a JSON list")
        mapping["capability_requests"] = capability_requests
        validation = mapping["validation"]
        validation["recognition_tests"] = self._lines(self.recognition_tests)
        validation["drift_tests"] = self._lines(self.drift_tests)
        validation["privacy_tests"] = self._lines(self.privacy_tests)
        validation["bench_evidence_refs"] = self._lines(self.bench_evidence)
        promotion = mapping["promotion"]
        promotion["target_repository"] = self.target_repository.text().strip() or None
        promotion["required_reviews"] = self._lines(self.required_reviews)
        promotion["required_evidence"] = self._lines(self.required_evidence)
        return mapping

    def reload_advanced_json(self) -> None:
        try:
            mapping = self._structured_mapping()
        except ValueError as exc:
            QMessageBox.warning(self, "Draft field rejected", str(exc))
            return
        self._mapping = mapping
        self.advanced_json.setPlainText(json.dumps(mapping, indent=2, sort_keys=True))
        self._status("Advanced view refreshed from structured fields")

    def apply_advanced_json(self) -> None:
        try:
            mapping = json.loads(self.advanced_json.toPlainText())
            if not isinstance(mapping, dict):
                raise ValueError("Candidate JSON must be an object")
            report = self.bridge.validate(mapping)
        except (FoundryUnavailable, OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Candidate JSON rejected", str(exc))
            return
        if not report.get("valid"):
            QMessageBox.warning(
                self,
                "Candidate JSON rejected",
                "\n".join(str(item) for item in report.get("errors", [])) or "Validation failed",
            )
            return
        normalized = report.get("normalized")
        if not isinstance(normalized, dict):
            QMessageBox.warning(self, "Candidate JSON rejected", "Canonical normalization was unavailable")
            return
        self._mapping = normalized
        self._load_mapping(normalized)
        self._status("Canonical JSON applied to draft")

    def validate_current(self) -> None:
        try:
            mapping = self._structured_mapping()
            report = self.bridge.validate(mapping)
        except (FoundryUnavailable, OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Validation unavailable", str(exc))
            return
        if report.get("valid"):
            normalized = report.get("normalized")
            if isinstance(normalized, dict):
                self._mapping = normalized
                self._load_mapping(normalized)
            self._status("Candidate validates against canonical Foundry contract")
            return
        QMessageBox.warning(
            self,
            "Candidate needs work",
            "\n".join(str(item) for item in report.get("errors", [])) or "Validation failed",
        )

    def save_current(self) -> None:
        try:
            mapping = self._structured_mapping()
            if self._persisted:
                if not self._content_hash:
                    raise ValueError("Saved draft has no inspected content hash")
                result = self.bridge.update(mapping, self._content_hash)
            else:
                result = self.bridge.create(mapping)
        except (FoundryUnavailable, FileNotFoundError, OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Draft not saved", str(exc))
            return
        normalized, content_hash = self._mapping_and_hash(result)
        self._mapping = normalized
        self._content_hash = content_hash
        self._persisted = True
        self._load_mapping(normalized)
        self.candidate_id.setEnabled(False)
        self.save_button.setText("Update Draft")
        self.refresh_candidates()
        self._status("Draft saved with optimistic content-hash protection")

    def discard_current(self) -> None:
        if not self._persisted or self._mapping is None or not self._content_hash:
            self._status("Open a persisted draft before discarding")
            return
        candidate_id = str(self._mapping.get("candidate", {}).get("candidate_id", ""))
        answer = QMessageBox.question(
            self,
            "Discard candidate draft",
            "Discard local draft %s? This does not alter registry, lineage, Runtime, or deployed code."
            % candidate_id,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.bridge.discard(candidate_id, self._content_hash)
        except (FoundryUnavailable, FileNotFoundError, OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Draft not discarded", str(exc))
            return
        self._mapping = None
        self._content_hash = None
        self._persisted = False
        self._set_editor_enabled(False)
        self.refresh_candidates()
        self._status("Local candidate draft discarded")

    def propose_promotion(self) -> None:
        if not self._persisted or self._mapping is None:
            self._status("Save the draft before preparing promotion review")
            return
        candidate_id = str(self._mapping.get("candidate", {}).get("candidate_id", ""))
        try:
            plan = self.bridge.propose_promotion(candidate_id)
        except (FoundryUnavailable, FileNotFoundError, OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Promotion review unavailable", str(exc))
            return
        self.promotion_output.setPlainText(json.dumps(plan, indent=2, sort_keys=True))
        decision = str(plan.get("decision", "external_review_required"))
        self._status("Promotion plan prepared: %s" % decision)

    @staticmethod
    def _candidate_id_from_result(result: Dict[str, Any]) -> str:
        candidate = result.get("candidate")
        if isinstance(candidate, dict):
            value = candidate.get("candidate_id")
            if value:
                return str(value)
        normalized = result.get("normalized")
        if isinstance(normalized, dict):
            candidate = normalized.get("candidate")
            if isinstance(candidate, dict) and candidate.get("candidate_id"):
                return str(candidate["candidate_id"])
        return str(result.get("candidate_id", ""))

    @staticmethod
    def _mapping_and_hash(result: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        normalized = result.get("normalized")
        if isinstance(normalized, dict):
            mapping = copy.deepcopy(normalized)
        else:
            mapping = copy.deepcopy(result)
            mapping.pop("content_hash", None)
        content_hash = result.get("content_hash")
        return mapping, str(content_hash) if content_hash else None

    def _status(self, text: str) -> None:
        self.status_label.setText(text)

    def _go_back(self) -> None:
        if self.on_back is not None:
            self.on_back()
