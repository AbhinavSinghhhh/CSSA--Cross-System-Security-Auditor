"""Firewall inspection view displaying packet filter status, profiles, and diagnostics."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class FirewallView(QWidget):
    """View presenting host firewall status, profiles, and detailed configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Header ───────────────────────────────────────────
        title = QLabel("🛡️ Host Firewall Status")
        title.setObjectName("viewTitle")
        layout.addWidget(title)

        subtitle = QLabel("Monitors host packet filters, network boundary enforcement, and zone profiles.")
        subtitle.setObjectName("viewSubtitle")
        layout.addWidget(subtitle)

        # ── Status Hero Card ─────────────────────────────────
        self.status_frame = QFrame()
        self.status_frame.setObjectName("card")
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setSpacing(8)

        self.indicator = QLabel("UNKNOWN")
        self.indicator.setAlignment(Qt.AlignCenter)
        self.indicator.setStyleSheet("font-size: 28px; font-weight: bold; color: #888888; padding: 6px;")
        status_layout.addWidget(self.indicator)

        info_row = QHBoxLayout()
        self.provider_label = QLabel("Provider: Unavailable")
        self.provider_label.setAlignment(Qt.AlignCenter)
        self.provider_label.setObjectName("cardHeader")
        info_row.addWidget(self.provider_label)

        self.rules_label = QLabel("Rules Count: Unavailable")
        self.rules_label.setAlignment(Qt.AlignCenter)
        self.rules_label.setObjectName("cardHeader")
        info_row.addWidget(self.rules_label)
        status_layout.addLayout(info_row)

        layout.addWidget(self.status_frame)

        # ── Profiles Section ─────────────────────────────────
        profiles_title = QLabel("Firewall Profiles & Zones")
        profiles_title.setObjectName("cardHeader")
        layout.addWidget(profiles_title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Profile / Zone Name", "Enforcement State", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setMinimumHeight(120)
        layout.addWidget(self.table)

        # ── Raw Diagnostics / Details ────────────────────────
        details_title = QLabel("Configuration Details & Diagnostics")
        details_title.setObjectName("cardHeader")
        layout.addWidget(details_title)

        self.details_box = QTextEdit()
        self.details_box.setObjectName("codeBox")
        self.details_box.setReadOnly(True)
        self.details_box.setPlaceholderText("Detailed firewall daemon diagnostic output will appear here after an audit run.")
        self.details_box.setMinimumHeight(140)
        layout.addWidget(self.details_box)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def update_data(self, audit_result):
        if not audit_result or not hasattr(audit_result, 'firewall'):
            return
        fw = audit_result.firewall
        if not fw:
            return

        enabled = getattr(fw, 'enabled', False)
        if enabled:
            self.indicator.setText("🛡️ ACTIVE (PROTECTED)")
            self.indicator.setStyleSheet("font-size: 28px; font-weight: bold; color: #00C853; padding: 6px;")
        else:
            self.indicator.setText("⚠️ INACTIVE (EXPOSED)")
            self.indicator.setStyleSheet("font-size: 28px; font-weight: bold; color: #FF1744; padding: 6px;")

        provider = getattr(fw, 'provider', 'Unknown')
        self.provider_label.setText(f"Provider: {provider}")

        rules_count = getattr(fw, 'rules_count', 0)
        self.rules_label.setText(f"Filter Rules: {rules_count}")

        profiles = getattr(fw, 'profiles', {})
        self.table.setRowCount(len(profiles))
        for row, (name, status) in enumerate(profiles.items()):
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row, 0, name_item)

            is_active = bool(status)
            desc_text = "Traffic filtered according to profile rules" if is_active else "Profile inactive or bypassed"
            desc_item = QTableWidgetItem(desc_text)
            self.table.setItem(row, 1, desc_item)

            status_item = QTableWidgetItem("✅ Enabled" if is_active else "❌ Disabled")
            status_item.setTextAlignment(Qt.AlignCenter)
            if is_active:
                status_item.setForeground(Qt.GlobalColor(Qt.green))
            else:
                status_item.setForeground(Qt.GlobalColor(Qt.red))
            self.table.setItem(row, 2, status_item)

        details = getattr(fw, 'details', '')
        if details:
            self.details_box.setPlainText(details)
        else:
            self.details_box.setPlainText("No additional diagnostic details returned by firewall provider.")
