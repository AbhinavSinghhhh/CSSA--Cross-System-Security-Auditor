"""Interactive system services view with multi-filter controls and real-time search."""

from __future__ import annotations

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import AuditResult, ServiceInfo, ServiceStartup, ServiceStatus


class ServicesView(QWidget):
    """View displaying running/stopped system services and startup types."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.all_services: List[ServiceInfo] = []
        self.filtered_services: List[ServiceInfo] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("🔧 System Services & Background Daemons")
        title.setObjectName("viewTitle")
        header.addWidget(title)

        self.count_label = QLabel("0 services")
        self.count_label.setObjectName("viewSubtitle")
        header.addWidget(self.count_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addLayout(header)

        # Filters
        filter_bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search service name, display name, description...")
        self.search.textChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.search, 3)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "RUNNING", "STOPPED"])
        self.status_filter.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.status_filter, 1)

        self.startup_filter = QComboBox()
        self.startup_filter.addItems(["All Startup Types", "AUTOMATIC", "MANUAL", "DISABLED"])
        self.startup_filter.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.startup_filter, 1)

        layout.addLayout(filter_bar)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Name", "Display Name", "Status", "Startup Type", "User Context", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def update_data(self, audit_result: Optional[AuditResult]) -> None:
        if not audit_result or not hasattr(audit_result, "services"):
            self.all_services = []
        else:
            self.all_services = list(audit_result.services)
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search.text().lower().strip()
        stat_filter = self.status_filter.currentText().upper()
        start_filter = self.startup_filter.currentText().upper()

        self.filtered_services = []
        for s in self.all_services:
            st_val = s.status.value.upper() if hasattr(s.status, "value") else str(s.status).upper()
            start_val = s.startup_type.value.upper() if hasattr(s.startup_type, "value") else str(s.startup_type).upper()

            if stat_filter != "ALL STATUSES" and stat_filter not in st_val:
                continue
            if start_filter != "ALL STARTUP TYPES" and start_filter not in start_val:
                continue

            if query:
                haystack = f"{s.name} {s.display_name} {s.description} {s.user}".lower()
                if query not in haystack:
                    continue

            self.filtered_services.append(s)

        self._render_table()

    def _render_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.filtered_services))
        self.count_label.setText(f"{len(self.filtered_services)} of {len(self.all_services)} services")

        for row, svc in enumerate(self.filtered_services):
            st_val = svc.status.value if hasattr(svc.status, "value") else str(svc.status)
            start_val = svc.startup_type.value if hasattr(svc.startup_type, "value") else str(svc.startup_type)

            name_item = QTableWidgetItem(svc.name)
            disp_item = QTableWidgetItem(svc.display_name or svc.name)

            stat_item = QTableWidgetItem(st_val)
            stat_item.setTextAlignment(Qt.AlignCenter)
            if "RUN" in st_val.upper():
                stat_item.setForeground(Qt.GlobalColor(Qt.green))
            elif "STOP" in st_val.upper() or "DEAD" in st_val.upper():
                stat_item.setForeground(Qt.GlobalColor(Qt.red))

            start_item = QTableWidgetItem(start_val)
            start_item.setTextAlignment(Qt.AlignCenter)

            user_item = QTableWidgetItem(svc.user or "system")
            desc_item = QTableWidgetItem(svc.description or "No description available")

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, disp_item)
            self.table.setItem(row, 2, stat_item)
            self.table.setItem(row, 3, start_item)
            self.table.setItem(row, 4, user_item)
            self.table.setItem(row, 5, desc_item)

        self.table.setSortingEnabled(True)
