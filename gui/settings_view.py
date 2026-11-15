"""Settings view allowing live configuration of theme, scoring penalties, and scan paths."""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.models import Severity


class SettingsView(QWidget):
    """View allowing configuration of visual theme, audit scoring penalties, and target paths."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = None
        self.db = None
        self.auditor = None
        self._suppress_theme_signal = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # ── Header ───────────────────────────────────────────
        title = QLabel("⚙️ Application & Scanner Settings")
        title.setObjectName("viewTitle")
        layout.addWidget(title)

        subtitle = QLabel("Configure theme preferences, rule scoring penalties, and default permission inspection paths.")
        subtitle.setObjectName("viewSubtitle")
        layout.addWidget(subtitle)

        # ── UI / Appearance Settings ─────────────────────────
        ui_group = QGroupBox("User Interface and Theme")
        ui_layout = QFormLayout(ui_group)
        ui_layout.setContentsMargins(16, 20, 16, 16)
        ui_layout.setSpacing(12)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark Theme (Default)", "dark")
        self.theme_combo.addItem("Light Theme", "light")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        ui_layout.addRow("Theme Appearance:", self.theme_combo)

        layout.addWidget(ui_group)

        # ── Scoring Penalties ────────────────────────────────
        score_group = QGroupBox("Security Scoring Weight Penalties")
        score_layout = QFormLayout(score_group)
        score_layout.setContentsMargins(16, 20, 16, 16)
        score_layout.setSpacing(10)

        self.crit_penalty = QSpinBox()
        self.crit_penalty.setRange(0, 100)
        self.crit_penalty.setValue(8)

        self.high_penalty = QSpinBox()
        self.high_penalty.setRange(0, 100)
        self.high_penalty.setValue(4)

        self.med_penalty = QSpinBox()
        self.med_penalty.setRange(0, 100)
        self.med_penalty.setValue(2)

        self.low_penalty = QSpinBox()
        self.low_penalty.setRange(0, 100)
        self.low_penalty.setValue(1)

        score_layout.addRow("🔴 Critical Finding Penalty:", self.crit_penalty)
        score_layout.addRow("🟠 High Finding Penalty:", self.high_penalty)
        score_layout.addRow("🟡 Medium Finding Penalty:", self.med_penalty)
        score_layout.addRow("🟢 Low Finding Penalty:", self.low_penalty)

        btn_apply_score = QPushButton("💾 Save & Apply Scoring Penalties")
        btn_apply_score.clicked.connect(self._on_save_penalties)
        score_layout.addRow("", btn_apply_score)

        layout.addWidget(score_group)

        # ── Scanner Paths Configuration ──────────────────────
        scan_group = QGroupBox("File Permissions Scanner")
        scan_layout = QVBoxLayout(scan_group)
        scan_layout.setContentsMargins(16, 20, 16, 16)
        scan_layout.setSpacing(10)

        path_lbl = QLabel("Default Permission Audit Paths (comma-separated directories):")
        path_lbl.setObjectName("cardHeader")
        scan_layout.addWidget(path_lbl)

        path_row = QHBoxLayout()
        self.paths_edit = QLineEdit("/etc, /usr/bin, /usr/local/bin, /tmp")
        path_row.addWidget(self.paths_edit, 1)

        self.btn_browse_path = QPushButton("📁 Browse...")
        self.btn_browse_path.clicked.connect(self._on_browse_path)
        path_row.addWidget(self.btn_browse_path)

        self.btn_save_paths = QPushButton("💾 Save Paths")
        self.btn_save_paths.clicked.connect(self._on_save_paths)
        path_row.addWidget(self.btn_save_paths)

        scan_layout.addLayout(path_row)
        layout.addWidget(scan_group)

        # ── Academic / About Section ─────────────────────────
        about_frame = QFrame()
        about_frame.setObjectName("card")
        ab_layout = QVBoxLayout(about_frame)
        ab_layout.setSpacing(6)

        ab_title = QLabel("🛡️ Cross-Platform System Security Auditor (CSSA) v1.2")
        ab_title.setObjectName("appTitle")
        ab_layout.addWidget(ab_title)

        ab_course = QLabel("Operating Systems + Windows/Linux/macOS Host Security Project")
        ab_course.setObjectName("cardHeader")
        ab_layout.addWidget(ab_course)

        ab_desc = QLabel(
            "Designed with strict defensive, read-only guarantees. Collects host configuration "
            "metrics using native OS utilities and APIs without destructive actions or privilege escalation."
        )
        ab_desc.setObjectName("viewSubtitle")
        ab_desc.setWordWrap(True)
        ab_layout.addWidget(ab_desc)

        layout.addWidget(about_frame)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def set_main_window(self, win, db=None, auditor=None) -> None:
        self.main_window = win
        self.db = db or getattr(win, "db", None)
        self.auditor = auditor or getattr(win, "auditor", None)
        self._load_saved_settings()

    def _load_saved_settings(self) -> None:
        if not self.db:
            return
        try:
            # Theme
            saved_theme = self.db.get_setting("theme", "dark")
            self._suppress_theme_signal = True
            idx = 1 if saved_theme == "light" else 0
            self.theme_combo.setCurrentIndex(idx)
            self._suppress_theme_signal = False

            # Scan paths
            saved_paths = self.db.get_setting("scan_paths", "")
            if saved_paths:
                self.paths_edit.setText(saved_paths)

            # Penalties
            cp = self.db.get_setting("penalty_critical", "8")
            hp = self.db.get_setting("penalty_high", "4")
            mp = self.db.get_setting("penalty_medium", "2")
            lp = self.db.get_setting("penalty_low", "1")
            self.crit_penalty.setValue(int(cp))
            self.high_penalty.setValue(int(hp))
            self.med_penalty.setValue(int(mp))
            self.low_penalty.setValue(int(lp))

            self._apply_penalties_to_scoring(show_notice=False)
        except Exception:
            pass

    def _on_theme_changed(self, index: int) -> None:
        if self._suppress_theme_signal or not self.main_window:
            return
        theme_val = self.theme_combo.currentData()
        if self.db:
            self.db.set_setting("theme", theme_val)

        is_dark = (theme_val == "dark")
        if self.main_window._dark_theme != is_dark:
            self.main_window.toggle_theme()

    def _on_browse_path(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Add to Default Scan Paths")
        if dir_path:
            current = self.paths_edit.text().strip()
            if current:
                self.paths_edit.setText(f"{current}, {dir_path}")
            else:
                self.paths_edit.setText(dir_path)

    def _on_save_paths(self) -> None:
        val = self.paths_edit.text().strip()
        if self.db:
            self.db.set_setting("scan_paths", val)
            QMessageBox.information(self, "Settings Saved", f"Scan paths updated to:\n{val}")

    def _on_save_penalties(self) -> None:
        if self.db:
            self.db.set_setting("penalty_critical", str(self.crit_penalty.value()))
            self.db.set_setting("penalty_high", str(self.high_penalty.value()))
            self.db.set_setting("penalty_medium", str(self.med_penalty.value()))
            self.db.set_setting("penalty_low", str(self.low_penalty.value()))

        self._apply_penalties_to_scoring(show_notice=True)

    def _apply_penalties_to_scoring(self, show_notice: bool = True) -> None:
        if not self.auditor:
            return
        scoring = getattr(self.auditor, "scoring", None)
        if scoring and hasattr(scoring, "penalties"):
            scoring.penalties[Severity.CRITICAL] = self.crit_penalty.value()
            scoring.penalties[Severity.HIGH] = self.high_penalty.value()
            scoring.penalties[Severity.MEDIUM] = self.med_penalty.value()
            scoring.penalties[Severity.LOW] = self.low_penalty.value()

            # Recalculate current audit score if loaded
            if self.main_window and getattr(self.main_window, "audit_result", None):
                res = self.main_window.audit_result
                res.score = scoring.calculate_score(res.findings)
                # Refresh views
                for v in self.main_window._view_map.values():
                    if hasattr(v, "update_data"):
                        try:
                            v.update_data(res)
                        except Exception:
                            pass

        if show_notice:
            QMessageBox.information(
                self,
                "Penalties Applied",
                f"Updated scoring penalties:\n"
                f"• Critical: -{self.crit_penalty.value()}\n"
                f"• High: -{self.high_penalty.value()}\n"
                f"• Medium: -{self.med_penalty.value()}\n"
                f"• Low: -{self.low_penalty.value()}"
            )

    def update_data(self, audit_result):
        pass

