"""Audit history view allowing inspection, loading, and deletion of past SQLite audit records."""

from __future__ import annotations

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class HistoryView(QWidget):
    """View displaying historical audit records stored in SQLite."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.db = None
        self.main_window = None
        self.audits_data: List[dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("📊 Audit History (SQLite Archive)")
        title.setObjectName("viewTitle")
        layout.addWidget(title)

        subtitle = QLabel("Browse historical host scans, reload previous findings, or remove archived audit runs.")
        subtitle.setObjectName("viewSubtitle")
        layout.addWidget(subtitle)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Audit Timestamp", "OS Platform", "Hostname", "Audited User", "Score", "Risk Level"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemDoubleClicked.connect(self._on_load_selected)
        layout.addWidget(self.table)

        # Action Buttons
        btns = QHBoxLayout()
        btns.setSpacing(10)
        self.load_btn = QPushButton("📂 Load Selected Audit into Views")
        self.load_btn.clicked.connect(self._on_load_selected)
        btns.addWidget(self.load_btn)

        self.del_btn = QPushButton("🗑️ Delete Selected Audit")
        self.del_btn.setObjectName("accent")
        self.del_btn.clicked.connect(self._on_delete_selected)
        btns.addWidget(self.del_btn)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._load_history)
        btns.addWidget(self.refresh_btn)

        btns.addStretch()
        layout.addLayout(btns)

    def set_db(self, db, main_window=None) -> None:
        self.db = db
        self.main_window = main_window
        self._load_history()

    def update_data(self, _audit_result=None) -> None:
        self._load_history()

    def _load_history(self) -> None:
        if not self.db:
            return
        try:
            self.audits_data = self.db.get_audits()
            self.table.setRowCount(len(self.audits_data))

            for row, audit in enumerate(self.audits_data):
                ts_item = QTableWidgetItem(audit.get("timestamp", ""))
                os_item = QTableWidgetItem(audit.get("os", "Unknown"))
                host_item = QTableWidgetItem(audit.get("hostname", "Unknown"))
                user_item = QTableWidgetItem(audit.get("username", "Unknown"))

                score_val = audit.get("score", 0)
                score_item = QTableWidgetItem()
                score_item.setData(Qt.DisplayRole, score_val)
                score_item.setTextAlignment(Qt.AlignCenter)

                risk_val = audit.get("risk_level", "Unknown")
                risk_item = QTableWidgetItem(risk_val)
                risk_item.setTextAlignment(Qt.AlignCenter)
                if score_val >= 90:
                    risk_item.setForeground(Qt.GlobalColor(Qt.green))
                elif score_val >= 60:
                    risk_item.setForeground(Qt.GlobalColor(Qt.yellow))
                else:
                    risk_item.setForeground(Qt.GlobalColor(Qt.red))

                self.table.setItem(row, 0, ts_item)
                self.table.setItem(row, 1, os_item)
                self.table.setItem(row, 2, host_item)
                self.table.setItem(row, 3, user_item)
                self.table.setItem(row, 4, score_item)
                self.table.setItem(row, 5, risk_item)
        except Exception as e:
            logger.error("Error loading audit history: %s", e)

    def _on_load_selected(self) -> None:
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, "Selection Required", "Please select an audit record from the table first.")
            return
        row = sel[0].row()
        if 0 <= row < len(self.audits_data):
            audit_id = self.audits_data[row]["id"]
            if self.main_window and hasattr(self.main_window, "load_historical_audit"):
                self.main_window.load_historical_audit(audit_id)
            else:
                QMessageBox.information(self, "Audit Selected", f"Loaded audit run: {audit_id}")

    def _on_delete_selected(self) -> None:
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, "Selection Required", "Please select an audit record to delete.")
            return
        row = sel[0].row()
        if 0 <= row < len(self.audits_data):
            audit_id = self.audits_data[row]["id"]
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to permanently delete audit record:\n{audit_id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes and self.db:
                self.db.delete_audit(audit_id)
                self._load_history()
