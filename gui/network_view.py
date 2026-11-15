"""Network connections view with exposure classification and multi-filtering."""

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

from core.models import AuditResult, NetworkConnection, NetworkExposure


class NetworkView(QWidget):
    """View displaying local listening sockets, exposure levels, and associated processes."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.all_connections: List[NetworkConnection] = []
        self.filtered_connections: List[NetworkConnection] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("🌐 Network Sockets & Boundary Exposure")
        title.setObjectName("viewTitle")
        header.addWidget(title)

        self.count_label = QLabel("0 connections")
        self.count_label.setObjectName("viewSubtitle")
        header.addWidget(self.count_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addLayout(header)

        # Filters
        filter_bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search address, port, process name, PID...")
        self.search.textChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.search, 3)

        self.exposure_filter = QComboBox()
        self.exposure_filter.addItems(["All Exposure", "LOCAL ONLY", "NETWORK EXPOSED", "UNKNOWN"])
        self.exposure_filter.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.exposure_filter, 1)

        self.proto_filter = QComboBox()
        self.proto_filter.addItems(["All Protocols", "TCP", "UDP"])
        self.proto_filter.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.proto_filter, 1)

        layout.addLayout(filter_bar)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Local Address", "Port", "Protocol", "Process Name", "PID", "State", "Exposure"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def update_data(self, audit_result: Optional[AuditResult]) -> None:
        if not audit_result or not hasattr(audit_result, "network_connections"):
            self.all_connections = []
        else:
            self.all_connections = list(audit_result.network_connections)
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search.text().lower().strip()
        exp_filter = self.exposure_filter.currentText().upper()
        proto_filter = self.proto_filter.currentText().upper()

        self.filtered_connections = []
        for c in self.all_connections:
            exp_val = c.exposure.value.upper() if hasattr(c.exposure, "value") else str(c.exposure).upper()
            proto_val = (c.protocol or "").upper()

            if exp_filter != "ALL EXPOSURE" and exp_filter not in exp_val:
                continue
            if proto_filter != "ALL PROTOCOLS" and proto_filter not in proto_val:
                continue

            if query:
                haystack = f"{c.local_address} {c.local_port} {c.process_name} {c.pid} {c.protocol}".lower()
                if query not in haystack:
                    continue

            self.filtered_connections.append(c)

        self._render_table()

    def _render_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.filtered_connections))
        self.count_label.setText(f"{len(self.filtered_connections)} of {len(self.all_connections)} connections")

        for row, conn in enumerate(self.filtered_connections):
            exp_val = conn.exposure.value if hasattr(conn.exposure, "value") else str(conn.exposure)

            addr_item = QTableWidgetItem(conn.local_address)
            port_item = QTableWidgetItem()
            port_item.setData(Qt.DisplayRole, conn.local_port)

            proto_item = QTableWidgetItem(conn.protocol)
            proc_item = QTableWidgetItem(conn.process_name or "unknown")

            pid_item = QTableWidgetItem()
            pid_item.setData(Qt.DisplayRole, conn.pid)

            state_item = QTableWidgetItem(conn.state or "LISTEN")

            exp_item = QTableWidgetItem(exp_val)
            exp_item.setTextAlignment(Qt.AlignCenter)
            if "LOCAL" in exp_val.upper():
                exp_item.setForeground(Qt.GlobalColor(Qt.green))
            elif "EXPOSED" in exp_val.upper():
                exp_item.setForeground(Qt.GlobalColor(Qt.yellow))
            else:
                exp_item.setForeground(Qt.GlobalColor(Qt.gray))

            self.table.setItem(row, 0, addr_item)
            self.table.setItem(row, 1, port_item)
            self.table.setItem(row, 2, proto_item)
            self.table.setItem(row, 3, proc_item)
            self.table.setItem(row, 4, pid_item)
            self.table.setItem(row, 5, state_item)
            self.table.setItem(row, 6, exp_item)

        self.table.setSortingEnabled(True)
