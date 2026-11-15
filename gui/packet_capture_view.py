"""Packet Capture and Network Threat Analysis View.

Integrates with Wireshark / tshark and provides native PCAP file inspection,
dissection, threat detection, and live network traffic auditing.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.models import AuditResult, PacketCaptureAudit, PacketThreat, Severity
from gui.widgets.stat_card import StatCard
from platforms.packet_capture import (
    audit_pcap_file,
    capture_live,
    find_tshark_path,
    get_best_default_interface,
    get_capture_interfaces,
    get_tshark_version,
)

logger = logging.getLogger(__name__)


class LiveCaptureWorker(QObject):
    """Background worker for live packet capture to avoid blocking the GUI."""
    finished = Signal(object)  # PacketCaptureAudit
    error = Signal(str)

    def __init__(
        self,
        duration: int,
        max_packets: int,
        interface: Optional[str],
        capture_filter: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.duration = duration
        self.max_packets = max_packets
        self.interface = interface
        self.capture_filter = capture_filter

    def run(self) -> None:
        try:
            audit = capture_live(
                duration_seconds=self.duration,
                max_packets=self.max_packets,
                interface=self.interface,
                capture_filter=self.capture_filter,
            )
            self.finished.emit(audit)
        except Exception as exc:
            logger.error("Live capture worker error: %s", exc)
            self.error.emit(str(exc))


class PacketCaptureView(QWidget):
    """View displaying packet capture status, live captures, and threat analysis."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.current_audit: Optional[PacketCaptureAudit] = None
        self.all_threats: List[PacketThreat] = []
        self.filtered_threats: List[PacketThreat] = []
        self._thread: Optional[QThread] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # ── Header ───────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("🦈 Network Packet Capture & Threat Analysis")
        title.setObjectName("viewTitle")
        header.addWidget(title)
        header.addStretch()

        self.tshark_badge = QLabel("Checking Wireshark...")
        self.tshark_badge.setStyleSheet(
            "padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 11px; background-color: #333; color: #aaa;"
        )
        header.addWidget(self.tshark_badge)
        layout.addLayout(header)

        subtitle = QLabel("Analyzes live packets or PCAP files for cleartext credentials, legacy protocols, weak TLS handshakes, and broadcast poisoning.")
        subtitle.setObjectName("viewSubtitle")
        layout.addWidget(subtitle)

        # ── Toolbar Controls ─────────────────────────────────
        toolbar = QFrame()
        toolbar.setObjectName("filterBar")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 8, 10, 8)
        tb_layout.setSpacing(10)

        # Interface Selector
        tb_layout.addWidget(QLabel("Interface:"))
        self.iface_combo = QComboBox()
        self._populate_interfaces()
        tb_layout.addWidget(self.iface_combo, 2)

        self.btn_refresh_ifaces = QPushButton("🔄")
        self.btn_refresh_ifaces.setToolTip("Refresh network interfaces")
        self.btn_refresh_ifaces.setFixedWidth(36)
        self.btn_refresh_ifaces.clicked.connect(self._populate_interfaces)
        tb_layout.addWidget(self.btn_refresh_ifaces)

        # Duration Selector
        tb_layout.addWidget(QLabel("Duration (s):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 30)
        self.duration_spin.setValue(5)
        self.duration_spin.setFixedWidth(65)
        tb_layout.addWidget(self.duration_spin)

        # BPF Filter
        self.bpf_filter_input = QLineEdit()
        self.bpf_filter_input.setPlaceholderText("BPF Filter (e.g. 'tcp', 'port 80 or 443')")
        self.bpf_filter_input.setToolTip("Optional Berkeley Packet Filter passed directly to tshark -f")
        tb_layout.addWidget(self.bpf_filter_input, 2)

        # Capture Button
        self.btn_capture = QPushButton("▶️  Capture Live (tshark)")
        self.btn_capture.setObjectName("accent")
        self.btn_capture.clicked.connect(self._start_live_capture)
        tb_layout.addWidget(self.btn_capture)

        # Load PCAP Button
        self.btn_load_pcap = QPushButton("📂  Open PCAP / PCAPNG")
        self.btn_load_pcap.clicked.connect(self._open_pcap_dialog)
        tb_layout.addWidget(self.btn_load_pcap)

        layout.addWidget(toolbar)

        # ── Stat Cards ───────────────────────────────────────
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_total_packets = StatCard("Packets Inspected", "0", "📡")
        self.card_critical = StatCard("Critical Threats", "0", "🚨")
        self.card_cleartext = StatCard("Insecure Protocols", "0", "🔓")
        self.card_weak_tls = StatCard("Weak TLS / Crypto", "0", "⚠️")

        cards_layout.addWidget(self.card_total_packets)
        cards_layout.addWidget(self.card_critical)
        cards_layout.addWidget(self.card_cleartext)
        cards_layout.addWidget(self.card_weak_tls)
        layout.addLayout(cards_layout)

        # ── Source & Protocols Banner ─────────────────────────
        self.source_banner = QLabel("Source: None loaded")
        self.source_banner.setStyleSheet("color: #88d49e; font-weight: 600; font-size: 12px; padding: 2px 4px;")
        layout.addWidget(self.source_banner)

        # ── Filters Bar ───────────────────────────────────────
        filter_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search threat, protocol, IP address, or recommendation...")
        self.search_input.textChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.search_input, 3)

        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["All Severities", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.severity_combo.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.severity_combo, 1)

        layout.addLayout(filter_bar)

        # ── Main Splitter: Threats Table + Detail Drawer ──────
        splitter = QSplitter(Qt.Vertical)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Severity", "Threat Type", "Protocol", "Endpoints", "Summary", "Recommendation"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_threat_selected)
        splitter.addWidget(self.table)

        # Detail Box
        detail_container = QFrame()
        detail_container.setObjectName("card")
        detail_layout = QVBoxLayout(detail_container)
        detail_layout.setContentsMargins(10, 8, 10, 8)

        detail_lbl = QLabel("📋 Threat Evidence & Dissection Details")
        detail_lbl.setObjectName("cardHeader")
        detail_layout.addWidget(detail_lbl)

        self.detail_text = QTextEdit()
        self.detail_text.setObjectName("codeBox")
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlaceholderText("Select a threat from the table above to view technical evidence, captured headers, and mitigation details.")
        self.detail_text.setFixedHeight(120)
        detail_layout.addWidget(self.detail_text)

        splitter.addWidget(detail_container)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # Check tshark status initially
        self._update_tshark_status()

    # ── Initialization & Interfaces ───────────────────────────

    def _update_tshark_status(self) -> None:
        tshark_bin = find_tshark_path()
        if tshark_bin:
            tshark_ver = get_tshark_version(tshark_bin)
            badge_text = f"🦈 tshark Active ({tshark_ver or tshark_bin})"
            self.tshark_badge.setText(badge_text)
            self.tshark_badge.setStyleSheet(
                "padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 11px; background-color: #00796B; color: #E0F2F1;"
            )
            self.btn_capture.setEnabled(True)
        else:
            self.tshark_badge.setText("⚠️ Wireshark CLI (tshark) Not Found (PCAP File Mode)")
            self.tshark_badge.setStyleSheet(
                "padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 11px; background-color: #E65100; color: #FFE0B2;"
            )
            self.btn_capture.setEnabled(False)
            self.btn_capture.setToolTip("Install Wireshark (tshark) to enable live network packet capturing.")

    def _populate_interfaces(self) -> None:
        self.iface_combo.clear()
        ifaces = get_capture_interfaces()
        best = get_best_default_interface()
        best_idx = 0

        if not ifaces:
            self.iface_combo.addItem("Default Interface", None)
            return

        for idx, (num, label) in enumerate(ifaces):
            self.iface_combo.addItem(f"{num}. {label}", num)
            if best and num == best:
                best_idx = idx

        self.iface_combo.setCurrentIndex(best_idx)

    # ── Live Capture Background Execution ─────────────────────

    def _start_live_capture(self) -> None:
        if self._thread and self._thread.isRunning():
            return

        duration = self.duration_spin.value()
        iface = self.iface_combo.currentData()
        bpf_filter = self.bpf_filter_input.text().strip() or None

        self.btn_capture.setEnabled(False)
        self.btn_capture.setText("⏳ Capturing...")
        filter_msg = f" (filter: {bpf_filter})" if bpf_filter else ""
        self.source_banner.setText(f"Capturing live network traffic via tshark for {duration} seconds{filter_msg}...")

        self._thread = QThread()
        self._worker = LiveCaptureWorker(
            duration=duration,
            max_packets=200,
            interface=iface,
            capture_filter=bpf_filter,
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_capture_finished)
        self._worker.error.connect(self._on_capture_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)

        self._thread.start()

    def _on_capture_finished(self, audit: PacketCaptureAudit) -> None:
        self.btn_capture.setEnabled(True)
        self.btn_capture.setText("▶️  Capture Live")
        self.current_audit = audit
        self._display_audit(audit)

    def _on_capture_error(self, err_msg: str) -> None:
        self.btn_capture.setEnabled(True)
        self.btn_capture.setText("▶️  Capture Live")
        self.source_banner.setText(f"⚠️ Capture error: {err_msg}")

    # ── PCAP File Dialog ──────────────────────────────────────

    def _open_pcap_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Packet Capture File",
            "",
            "Packet Capture (*.pcap *.pcapng *.cap);;All Files (*)",
        )
        if file_path:
            audit = audit_pcap_file(file_path)
            self.current_audit = audit
            self._display_audit(audit)

    # ── Data Presentation ─────────────────────────────────────

    def update_data(self, audit_result: Optional[AuditResult]) -> None:
        """Called by main window when a full audit finishes or mode changes."""
        self._update_tshark_status()
        if not audit_result or not hasattr(audit_result, "packet_capture"):
            return

        self.current_audit = audit_result.packet_capture
        self._display_audit(self.current_audit)

    def _display_audit(self, audit: PacketCaptureAudit) -> None:
        self.all_threats = list(audit.threats)

        # Update cards
        crit_count = sum(1 for t in self.all_threats if t.severity == Severity.CRITICAL)
        plain_count = sum(1 for t in self.all_threats if t.threat_type == "CLEARTEXT_PROTOCOL")
        tls_count = sum(1 for t in self.all_threats if t.threat_type == "WEAK_TLS")

        self.card_total_packets.set_value(str(audit.total_packets_captured))
        self.card_critical.set_value(str(crit_count))
        self.card_cleartext.set_value(str(plain_count))
        self.card_weak_tls.set_value(str(tls_count))

        # Update source banner
        protos_str = " | ".join(f"{k}: {v}" for k, v in sorted(audit.protocols_seen.items())) if audit.protocols_seen else "None"
        source_txt = f"Source: {audit.capture_source}  |  Packets: {audit.total_packets_captured}  |  Protocols: [{protos_str}]"
        if not audit.capture_available:
            source_txt += f"  (Status: {audit.details})"
        self.source_banner.setText(source_txt)

        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search_input.text().strip().lower()
        sev_filter = self.severity_combo.currentText().upper()

        self.filtered_threats = []
        for t in self.all_threats:
            sev_str = t.severity.value if hasattr(t.severity, "value") else str(t.severity)
            if sev_filter != "ALL SEVERITIES" and sev_str != sev_filter:
                continue

            if query:
                haystack = f"{t.threat_type} {t.protocol} {t.source_ip} {t.dest_ip} {t.description} {t.recommendation}".lower()
                if query not in haystack:
                    continue

            self.filtered_threats.append(t)

        self._render_table()

    def _render_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.filtered_threats))

        for row, t in enumerate(self.filtered_threats):
            sev_str = t.severity.value if hasattr(t.severity, "value") else str(t.severity)
            sev_item = QTableWidgetItem(sev_str)
            sev_item.setTextAlignment(Qt.AlignCenter)
            if sev_str == "CRITICAL":
                sev_item.setForeground(Qt.GlobalColor(Qt.red))
            elif sev_str == "HIGH":
                sev_item.setForeground(Qt.GlobalColor(Qt.yellow))
            elif sev_str == "MEDIUM":
                sev_item.setForeground(Qt.GlobalColor(Qt.cyan))
            else:
                sev_item.setForeground(Qt.GlobalColor(Qt.gray))

            type_item = QTableWidgetItem(t.threat_type)
            proto_item = QTableWidgetItem(t.protocol)
            proto_item.setTextAlignment(Qt.AlignCenter)

            endpoints_str = f"{t.source_ip}:{t.source_port} -> {t.dest_ip}:{t.dest_port}"
            endpoints_item = QTableWidgetItem(endpoints_str)

            desc_item = QTableWidgetItem(t.description)
            rec_item = QTableWidgetItem(t.recommendation)

            self.table.setItem(row, 0, sev_item)
            self.table.setItem(row, 1, type_item)
            self.table.setItem(row, 2, proto_item)
            self.table.setItem(row, 3, endpoints_item)
            self.table.setItem(row, 4, desc_item)
            self.table.setItem(row, 5, rec_item)

        self.table.setSortingEnabled(True)

    def _on_threat_selected(self) -> None:
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        if 0 <= row < len(self.filtered_threats):
            t = self.filtered_threats[row]
            detail_content = (
                f"Threat: {t.threat_type} [{t.severity.value}]\n"
                f"Protocol: {t.protocol} | Endpoints: {t.source_ip}:{t.source_port} -> {t.dest_ip}:{t.dest_port}\n"
                f"Timestamp: {t.timestamp or 'N/A'}\n"
                f"Summary: {t.packet_summary or 'N/A'}\n\n"
                f"Description: {t.description}\n"
                f"Evidence: {t.evidence or 'None'}\n\n"
                f"Recommendation: {t.recommendation}"
            )
            self.detail_text.setPlainText(detail_content)
