"""Interactive process auditing view with real-time search, sorting, and resource metrics."""

from __future__ import annotations

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import AuditResult, ProcessInfo


class ProcessesView(QWidget):
    """View displaying running host processes with filtering and sorting."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.all_processes: List[ProcessInfo] = []
        self.filtered_processes: List[ProcessInfo] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("⚙️ Running Processes & Resource Utilization")
        title.setObjectName("viewTitle")
        header.addWidget(title)

        self.count_label = QLabel("0 processes")
        self.count_label.setObjectName("viewSubtitle")
        header.addWidget(self.count_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addLayout(header)

        # Controls
        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search by process name, PID, user, or path...")
        self.search.textChanged.connect(self._apply_filter)
        controls.addWidget(self.search, 4)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._apply_filter)
        controls.addWidget(self.refresh_btn, 1)
        layout.addLayout(controls)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["PID", "Process Name", "CPU %", "Memory %", "User", "Parent PID", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def update_data(self, audit_result: Optional[AuditResult]) -> None:
        if not audit_result or not hasattr(audit_result, "processes"):
            self.all_processes = []
        else:
            self.all_processes = list(audit_result.processes)
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self.search.text().lower().strip()
        if not query:
            self.filtered_processes = list(self.all_processes)
        else:
            self.filtered_processes = [
                p for p in self.all_processes
                if query in str(p.pid)
                or query in (p.name or "").lower()
                or query in (p.username or "").lower()
                or query in (p.exe_path or "").lower()
                or query in (p.cmdline or "").lower()
            ]
        self._render_table()

    def _render_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.filtered_processes))
        self.count_label.setText(f"{len(self.filtered_processes)} of {len(self.all_processes)} processes")

        for row, proc in enumerate(self.filtered_processes):
            pid_item = QTableWidgetItem()
            pid_item.setData(Qt.DisplayRole, proc.pid)

            name_item = QTableWidgetItem(proc.name or "unknown")
            if proc.exe_path:
                name_item.setToolTip(f"Path: {proc.exe_path}\nCmdline: {proc.cmdline}")

            cpu_item = QTableWidgetItem()
            cpu_item.setData(Qt.DisplayRole, round(proc.cpu_percent, 1))

            mem_item = QTableWidgetItem()
            mem_item.setData(Qt.DisplayRole, round(proc.memory_percent, 1))

            user_item = QTableWidgetItem(proc.username or "system")
            ppid_item = QTableWidgetItem()
            ppid_item.setData(Qt.DisplayRole, proc.parent_pid)

            status_item = QTableWidgetItem(proc.status or "running")

            self.table.setItem(row, 0, pid_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, cpu_item)
            self.table.setItem(row, 3, mem_item)
            self.table.setItem(row, 4, user_item)
            self.table.setItem(row, 5, ppid_item)
            self.table.setItem(row, 6, status_item)

        self.table.setSortingEnabled(True)
