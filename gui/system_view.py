"""System information view displaying hardware, OS, runtime, and privilege metrics."""

from __future__ import annotations

from typing import Optional
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.models import AuditResult, SystemInfo


class SystemView(QWidget):
    """View displaying comprehensive hardware, OS, privilege, and runtime metadata in styled cards."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("💻 Host System Information")
        title.setObjectName("viewTitle")
        layout.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(14)
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        self.labels: dict[str, QLabel] = {}

    def _add_card(self, row: int, col: int, title: str, key: str, default_val: str = "Unavailable", icon: str = "💻") -> None:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMinimumHeight(85)
        vbox = QVBoxLayout(frame)
        vbox.setSpacing(6)

        header = QLabel(f"{icon}  {title}")
        header.setObjectName("cardHeader")
        vbox.addWidget(header)

        val_label = QLabel(default_val)
        val_label.setObjectName("cardValue")
        val_label.setWordWrap(True)
        vbox.addWidget(val_label)

        self.labels[key] = val_label
        self.grid.addWidget(frame, row, col)

    def update_data(self, audit_result: Optional[AuditResult]) -> None:
        # Clear existing widgets
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.labels.clear()

        sys_info: SystemInfo = getattr(audit_result, "system_info", None) if audit_result else None

        # Row 0: Operating System
        self._add_card(0, 0, "Operating System", "os_name", getattr(sys_info, "os_name", "N/A"), "🖥️")
        self._add_card(0, 1, "OS Version", "os_version", getattr(sys_info, "os_version", "N/A"), "🏷️")
        self._add_card(0, 2, "Kernel Version", "kernel_version", getattr(sys_info, "kernel_version", "N/A"), "⚙️")

        # Row 1: Identity & Privileges
        self._add_card(1, 0, "Hostname", "hostname", getattr(sys_info, "hostname", "N/A"), "🌐")
        self._add_card(1, 1, "Current User", "current_user", getattr(sys_info, "current_user", "N/A"), "👤")
        self._add_card(1, 2, "Privilege Level", "privilege_level", getattr(sys_info, "privilege_level", "N/A"), "🛡️")

        # Row 2: Architecture & Processor
        self._add_card(2, 0, "Hardware Architecture", "architecture", getattr(sys_info, "architecture", "N/A"), "📐")
        self._add_card(2, 1, "CPU Model", "cpu_info", getattr(sys_info, "cpu_info", "N/A"), "⚡")
        self._add_card(2, 2, "Logical CPU Cores", "cpu_count", str(getattr(sys_info, "cpu_count", "0")), "🎛️")

        # Row 3: Memory, Storage & Runtime (Balanced 4x3 Grid)
        mem_str = f"{getattr(sys_info, 'available_memory_gb', 0.0)} GB avail / {getattr(sys_info, 'total_memory_gb', 0.0)} GB total"
        self._add_card(3, 0, "System RAM", "memory", mem_str, "💾")

        disk_str = f"{getattr(sys_info, 'disk_used_gb', 0.0)} GB used / {getattr(sys_info, 'disk_total_gb', 0.0)} GB ({getattr(sys_info, 'disk_free_gb', 0.0)} GB free)"
        self._add_card(3, 1, "Primary Storage Volume", "disk", disk_str, "💽")

        boot = getattr(sys_info, "boot_time", "N/A")
        uptime = getattr(sys_info, "uptime", "N/A")
        uptime_str = f"{uptime}\n(Booted: {boot})" if boot != "N/A" else str(uptime)
        self._add_card(3, 2, "System Uptime & Boot", "uptime", uptime_str, "⏱️")

        # Ensure top row is immediately visible upon data load
        self.scroll.verticalScrollBar().setValue(0)
