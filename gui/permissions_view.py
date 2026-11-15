"""File permissions scanner view allowing targeted directory auditing and risk assessment."""

from __future__ import annotations

import os
import stat
from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
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

from core.models import AuditResult, FilePermission


class PermissionsView(QWidget):
    """View displaying file and directory permission audits with interactive directory scanner."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.permissions: List[FilePermission] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("📁 File & Directory Permissions Audit")
        title.setObjectName("viewTitle")
        layout.addWidget(title)

        # Controls
        controls = QHBoxLayout()
        self.select_btn = QPushButton("📁 Select Directory to Scan")
        self.select_btn.clicked.connect(self._select_dir)
        controls.addWidget(self.select_btn)

        self.scan_btn = QPushButton("🔍 Scan Permissions")
        self.scan_btn.setObjectName("accent")
        self.scan_btn.clicked.connect(self._on_scan)
        controls.addWidget(self.scan_btn)

        self.path_label = QLabel("Default sensitive system paths audited")
        self.path_label.setObjectName("viewSubtitle")
        controls.addWidget(self.path_label)
        controls.addStretch()
        layout.addLayout(controls)

        warning = QLabel("⚠️ Warning: Scanning broad directories (such as / or C:\\) may take a long time. Auditing is non-destructive and read-only.")
        warning.setStyleSheet("color: #FFD600; font-size: 12px;")
        layout.addWidget(warning)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Path", "Owner", "Group", "Mode", "Risk", "Security Rationale"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        self.selected_path: Optional[str] = None

    def _select_dir(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Audit")
        if dir_path:
            self.selected_path = dir_path
            self.path_label.setText(f"Selected: {dir_path}")
            self.path_label.setStyleSheet("color: #00C853; font-weight: bold;")

    def _on_scan(self) -> None:
        target = self.selected_path
        if not target or not os.path.exists(target):
            QMessageBox.information(self, "Select Directory", "Please select a directory to audit first.")
            return

        items: List[FilePermission] = []
        try:
            entries = os.scandir(target)
            count = 0
            for entry in entries:
                if count > 100:  # Safety cap for performance
                    break
                count += 1
                try:
                    st = entry.stat(follow_symlinks=False)
                    mode = st.st_mode
                    is_ww = bool(mode & stat.S_IWOTH)
                    is_suid = bool(mode & stat.S_ISUID)

                    risk = "LOW"
                    reason = "Standard permissions"
                    if is_ww and entry.path != "/tmp":
                        risk = "HIGH"
                        reason = "World-writable (all users can modify/overwrite)"
                    elif is_suid:
                        risk = "MEDIUM"
                        reason = "Elevated SUID execution bit set"

                    items.append(
                        FilePermission(
                            path=entry.path,
                            owner=str(st.st_uid),
                            group=str(st.st_gid),
                            permissions=stat.filemode(mode),
                            numeric_mode=oct(stat.S_IMODE(mode))[2:],
                            is_suid=is_suid,
                            is_world_writable=is_ww,
                            risk=risk,
                            reason=reason,
                        )
                    )
                except Exception:
                    continue
        except Exception as e:
            QMessageBox.warning(self, "Scan Error", f"Could not audit directory: {e}")
            return

        self.permissions = items
        self._render_table()

    def update_data(self, audit_result: Optional[AuditResult]) -> None:
        if not audit_result or not hasattr(audit_result, "file_permissions"):
            self.permissions = []
        else:
            self.permissions = list(audit_result.file_permissions)
        self._render_table()

    def _render_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.permissions))

        for row, perm in enumerate(self.permissions):
            path_item = QTableWidgetItem(perm.path)
            owner_item = QTableWidgetItem(perm.owner)
            group_item = QTableWidgetItem(perm.group)
            mode_item = QTableWidgetItem(f"{perm.permissions} ({perm.numeric_mode})" if perm.numeric_mode else perm.permissions)
            mode_item.setTextAlignment(Qt.AlignCenter)

            risk_val = perm.risk or "LOW"
            risk_item = QTableWidgetItem(risk_val)
            risk_item.setTextAlignment(Qt.AlignCenter)
            if risk_val.upper() == "HIGH":
                risk_item.setForeground(Qt.GlobalColor(Qt.red))
            elif risk_val.upper() == "MEDIUM":
                risk_item.setForeground(Qt.GlobalColor(Qt.yellow))
            else:
                risk_item.setForeground(Qt.GlobalColor(Qt.green))

            reason_item = QTableWidgetItem(perm.reason or "Normal")

            self.table.setItem(row, 0, path_item)
            self.table.setItem(row, 1, owner_item)
            self.table.setItem(row, 2, group_item)
            self.table.setItem(row, 3, mode_item)
            self.table.setItem(row, 4, risk_item)
            self.table.setItem(row, 5, reason_item)

        self.table.setSortingEnabled(True)
