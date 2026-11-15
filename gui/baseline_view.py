"""Baseline creation and configuration drift comparison view."""

from __future__ import annotations

from typing import Any, List, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.baseline import BaselineManager
from core.models import AuditResult, BaselineDiff, BaselineItem


class BaselineView(QWidget):
    """View managing system baseline snapshots and configuration drift analysis."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.db = None
        self.main_window = None
        self.current_audit: Optional[AuditResult] = None
        self.baselines_list: List[dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("📋 System Baselines & Configuration Drift")
        title.setObjectName("viewTitle")
        layout.addWidget(title)

        subtitle = QLabel("Capture known-good configuration baselines and detect unwanted port exposure, service changes, or new administrative accounts.")
        subtitle.setObjectName("viewSubtitle")
        layout.addWidget(subtitle)

        # Controls
        controls = QHBoxLayout()
        self.create_btn = QPushButton("💾 Create Baseline from Current Audit")
        self.create_btn.clicked.connect(self._on_create_baseline)
        controls.addWidget(self.create_btn)

        self.selector = QComboBox()
        self.selector.setMinimumWidth(260)
        controls.addWidget(self.selector)

        self.compare_btn = QPushButton("⚡ Compare Drift")
        self.compare_btn.setObjectName("accent")
        self.compare_btn.clicked.connect(self._on_compare)
        controls.addWidget(self.compare_btn)

        self.del_btn = QPushButton("🗑️ Delete Baseline")
        self.del_btn.clicked.connect(self._on_delete_baseline)
        controls.addWidget(self.del_btn)

        controls.addStretch()
        layout.addLayout(controls)

        self.drift_summary = QLabel("Select a saved baseline and click 'Compare Drift' to analyze configuration changes.")
        self.drift_summary.setStyleSheet("color: #00C853; font-weight: bold; font-size: 13px; margin-top: 4px;")
        layout.addWidget(self.drift_summary)

        # Drift Diff Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Drift Status", "Category", "Key / Component", "Baseline Value", "Current Audit Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def set_db(self, db, main_window=None) -> None:
        self.db = db
        self.main_window = main_window
        self._refresh_baselines()

    def update_data(self, audit_result: Optional[AuditResult]) -> None:
        self.current_audit = audit_result
        self._refresh_baselines()

    def _refresh_baselines(self) -> None:
        if not self.db:
            return
        self.baselines_list = self.db.get_baselines()
        self.selector.clear()
        if not self.baselines_list:
            self.selector.addItem("No saved baselines found")
        else:
            for b in self.baselines_list:
                self.selector.addItem(f"{b['name']} ({b['os']} - {b['timestamp']})", b["id"])

    def _on_create_baseline(self) -> None:
        if not self.current_audit:
            QMessageBox.warning(self, "No Active Audit", "Run an audit first before creating a baseline snapshot.")
            return

        name, ok = QInputDialog.getText(self, "Create Baseline", "Enter a name for this configuration baseline:", text="Production Baseline")
        if ok and name.strip() and self.db:
            items = BaselineManager.create_baseline(self.current_audit)
            self.db.save_baseline(name.strip(), self.current_audit, items)
            self._refresh_baselines()
            QMessageBox.information(self, "Baseline Saved", f"Baseline '{name}' successfully captured with {len(items)} monitored configuration items.")

    def _on_compare(self) -> None:
        if not self.current_audit:
            QMessageBox.warning(self, "No Current Audit", "Run or load an audit first before comparing against a baseline.")
            return
        if not self.baselines_list:
            QMessageBox.information(self, "No Baseline", "No saved baseline selected. Create one first!")
            return

        b_id = self.selector.currentData()
        if not b_id or not self.db:
            return

        base_items = self.db.get_baseline_items(b_id)
        curr_items = BaselineManager.create_baseline(self.current_audit)
        diff = BaselineManager.compare_baseline(base_items, curr_items)

        self._render_diff(diff)

    def _on_delete_baseline(self) -> None:
        b_id = self.selector.currentData()
        if not b_id or not self.db:
            return
        b_name = self.selector.currentText()
        reply = QMessageBox.question(self, "Delete Baseline", f"Delete baseline '{b_name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_baseline(b_id)
            self._refresh_baselines()
            self.table.setRowCount(0)
            self.drift_summary.setText("Baseline deleted.")

    def _render_diff(self, diff: BaselineDiff) -> None:
        total_changes = len(diff.added) + len(diff.removed) + len(diff.changed)
        self.drift_summary.setText(
            f"Configuration Drift Detected: {len(diff.added)} Added (+), {len(diff.removed)} Removed (-), {len(diff.changed)} Changed (!)"
        )

        rows = []
        for item in diff.added:
            rows.append(("+ Added", item.category, item.key, "(None)", f"{item.value} ({item.details})", QColor("#00C853")))
        for item in diff.removed:
            rows.append(("- Removed", item.category, item.key, f"{item.value} ({item.details})", "(Decommissioned)", QColor("#FF1744")))
        for old_item, new_item in diff.changed:
            rows.append(("! Changed", new_item.category, new_item.key, old_item.value, f"{new_item.value} ({new_item.details})", QColor("#FFD600")))

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))

        for row, (status, cat, key, old_v, new_v, color) in enumerate(rows):
            stat_item = QTableWidgetItem(status)
            stat_item.setForeground(color)
            stat_item.setTextAlignment(Qt.AlignCenter)

            cat_item = QTableWidgetItem(cat)
            key_item = QTableWidgetItem(key)
            old_item = QTableWidgetItem(old_v)
            new_item = QTableWidgetItem(new_v)

            self.table.setItem(row, 0, stat_item)
            self.table.setItem(row, 1, cat_item)
            self.table.setItem(row, 2, key_item)
            self.table.setItem(row, 3, old_item)
            self.table.setItem(row, 4, new_item)

        self.table.setSortingEnabled(True)
        if total_changes == 0:
            QMessageBox.information(self, "No Drift", "System state perfectly matches the baseline. No configuration drift detected.")
