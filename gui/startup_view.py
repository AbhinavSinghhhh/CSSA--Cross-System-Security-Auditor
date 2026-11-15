"""Startup and persistence mechanisms view with real-time filtering and risk classification."""

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import StartupEntry


class StartupDetailDialog(QDialog):
    """Detailed inspector for a startup / persistence item."""

    def __init__(self, entry: StartupEntry, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Startup Entry — {entry.name}")
        self.setMinimumSize(580, 440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel(f"🚀 {entry.name}")
        title.setObjectName("viewTitle")
        layout.addWidget(title)

        frame = QFrame()
        frame.setObjectName("card")
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(16, 16, 16, 16)
        f_layout.setSpacing(10)

        def add_field(label: str, val: str, is_highlight: bool = False, hl_color: str = ""):
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setFixedWidth(130)
            lbl.setObjectName("cardHeader")
            v = QLabel(str(val))
            v.setWordWrap(True)
            if hl_color:
                v.setStyleSheet(f"color: {hl_color}; font-weight: bold;")
            elif is_highlight:
                v.setObjectName("codeBox")
            else:
                v.setObjectName("cardValue")
            row.addWidget(lbl)
            row.addWidget(v, 1)
            f_layout.addLayout(row)

        add_field("Name", entry.name)
        risk_color = "#FF1744" if "HIGH" in str(entry.risk).upper() else ("#FFD600" if "MED" in str(entry.risk).upper() else "#00C853")
        add_field("Risk Level", entry.risk or "Standard", hl_color=risk_color)
        add_field("Enabled", "Yes" if entry.enabled else "No")
        add_field("User Scope", entry.user or "All Users / System")
        add_field("Source", entry.source or "Unknown")
        add_field("Location / Path", entry.location or "Unavailable", is_highlight=True)
        add_field("Command / Exec", entry.command or "Unavailable", is_highlight=True)
        if getattr(entry, "description", None):
            add_field("Description", entry.description)

        layout.addWidget(frame)

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)


class StartupView(QWidget):
    """View displaying host persistence and autostart entries with search and classification."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries: List[StartupEntry] = []
        self.filtered_entries: List[StartupEntry] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # ── Header ───────────────────────────────────────────
        title = QLabel("🚀 Startup & Persistence Mechanisms")
        title.setObjectName("viewTitle")
        layout.addWidget(title)

        disclaimer_frame = QFrame()
        disclaimer_frame.setObjectName("card")
        d_layout = QHBoxLayout(disclaimer_frame)
        d_layout.setContentsMargins(4, 4, 4, 4)
        d_icon = QLabel("ℹ️")
        d_layout.addWidget(d_icon)
        disclaimer = QLabel(
            "Disclaimer: Startup and persistence entries are not inherently malicious. "
            "Examine paths, launch daemons, and scheduled tasks for unquoted paths or unverified third-party binaries."
        )
        disclaimer.setObjectName("viewSubtitle")
        disclaimer.setWordWrap(True)
        d_layout.addWidget(disclaimer, 1)
        layout.addWidget(disclaimer_frame)

        # ── Search & Filter Controls ─────────────────────────
        controls = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search by name, executable, location, or source...")
        self.search_box.textChanged.connect(self._apply_filter)
        controls.addWidget(self.search_box, 1)

        self.count_label = QLabel("0 entries found")
        self.count_label.setObjectName("viewSubtitle")
        controls.addWidget(self.count_label)
        layout.addLayout(controls)

        # ── Table ─────────────────────────────────────────────
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Risk", "Location / Scope", "Command Line", "User", "Enabled", "Source"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.table)

    def update_data(self, audit_result):
        self.entries = getattr(audit_result, 'startup_entries', []) or []
        self._apply_filter()

    def _apply_filter(self):
        query = self.search_box.text().strip().lower()
        if not query:
            self.filtered_entries = list(self.entries)
        else:
            self.filtered_entries = [
                e for e in self.entries
                if query in str(getattr(e, 'name', '')).lower()
                or query in str(getattr(e, 'location', '')).lower()
                or query in str(getattr(e, 'command', '')).lower()
                or query in str(getattr(e, 'source', '')).lower()
                or query in str(getattr(e, 'user', '')).lower()
            ]

        self.count_label.setText(f"Showing {len(self.filtered_entries)} of {len(self.entries)} entries")

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.filtered_entries))

        for row, ent in enumerate(self.filtered_entries):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(getattr(ent, 'name', '')))

            # Risk badge
            risk_val = getattr(ent, 'risk', 'Low') or 'Low'
            risk_item = QTableWidgetItem(risk_val)
            risk_item.setTextAlignment(Qt.AlignCenter)
            if "HIGH" in risk_val.upper() or "CRITICAL" in risk_val.upper():
                risk_item.setForeground(Qt.GlobalColor(Qt.red))
            elif "MED" in risk_val.upper():
                risk_item.setForeground(Qt.GlobalColor(Qt.yellow))
            else:
                risk_item.setForeground(Qt.GlobalColor(Qt.green))
            self.table.setItem(row, 1, risk_item)

            # Location
            loc_val = getattr(ent, 'location', '') or 'Unavailable'
            self.table.setItem(row, 2, QTableWidgetItem(loc_val))

            # Command
            cmd_val = getattr(ent, 'command', '') or 'Unavailable'
            self.table.setItem(row, 3, QTableWidgetItem(cmd_val))

            # User
            user_val = getattr(ent, 'user', '') or 'System'
            self.table.setItem(row, 4, QTableWidgetItem(user_val))

            # Enabled
            is_en = getattr(ent, 'enabled', True)
            en_item = QTableWidgetItem("✅ Enabled" if is_en else "❌ Disabled")
            en_item.setTextAlignment(Qt.AlignCenter)
            if is_en:
                en_item.setForeground(Qt.GlobalColor(Qt.green))
            else:
                en_item.setForeground(Qt.GlobalColor(Qt.red))
            self.table.setItem(row, 5, en_item)

            # Source
            src_val = getattr(ent, 'source', 'Auto') or 'Auto'
            self.table.setItem(row, 6, QTableWidgetItem(src_val))

        self.table.setSortingEnabled(True)

    def _on_item_double_clicked(self, item):
        row = item.row()
        if 0 <= row < len(self.filtered_entries):
            entry = self.filtered_entries[row]
            dialog = StartupDetailDialog(entry, self)
            dialog.exec()
