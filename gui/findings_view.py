"""Interactive security findings viewer with multi-criteria filtering and detailed inspector panel."""

from __future__ import annotations

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.models import AuditResult, Finding, FindingStatus, Severity


SEVERITY_COLORS = {
    "CRITICAL": "#FF1744",
    "HIGH": "#FF6D00",
    "MEDIUM": "#FFD600",
    "LOW": "#00C853",
    "INFO": "#2979FF",
}

STATUS_COLORS = {
    "FAIL": "#FF1744",
    "WARNING": "#FFD600",
    "PASS": "#00C853",
    "UNAVAILABLE": "#888888",
    "NOT_APPLICABLE": "#888888",
}


class FindingsView(QWidget):
    """Interactive security findings explorer."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.all_findings: List[Finding] = []
        self.filtered_findings: List[Finding] = []
        self._is_dark: bool = True
        self._selected_finding: Optional[Finding] = None

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(14)

        # ── Header ───────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("🔍 Security Findings & Policy Inspector")
        title.setObjectName("viewTitle")
        header.addWidget(title)

        self.count_label = QLabel("0 findings")
        self.count_label.setObjectName("viewSubtitle")
        header.addWidget(self.count_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        root_layout.addLayout(header)

        # ── Filters Bar ───────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setObjectName("filterBar")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(8)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search title, description, evidence...")
        self.search_bar.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_bar, 3)

        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["All Severities", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"])
        self.severity_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.severity_combo, 2)

        self.category_combo = QComboBox()
        self.category_combo.addItems(["All Categories"])
        self.category_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.category_combo, 2)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Statuses", "FAIL", "WARNING", "PASS", "UNAVAILABLE"])
        self.status_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.status_combo, 2)

        root_layout.addWidget(filter_frame)

        # ── Main Splitter (Table + Inspector) ─────────────────
        splitter = QSplitter(Qt.Vertical)

        # Findings Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Severity", "Status", "Category", "Title", "Platform"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        splitter.addWidget(self.table)

        # Detail Inspector Panel
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("card")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(12, 12, 12, 12)
        detail_layout.setSpacing(8)

        det_header = QHBoxLayout()
        self.det_title = QLabel("Select a finding above to inspect details")
        self.det_title.setObjectName("cardHeader")
        det_header.addWidget(self.det_title)

        self.det_badge = QLabel("")
        self.det_badge.setStyleSheet("font-weight: bold; padding: 3px 8px; border-radius: 4px;")
        det_header.addWidget(self.det_badge, alignment=Qt.AlignRight)
        detail_layout.addLayout(det_header)

        self.det_meta = QLabel("")
        self.det_meta.setObjectName("viewSubtitle")
        detail_layout.addWidget(self.det_meta)

        self.det_text = QTextEdit()
        self.det_text.setReadOnly(True)
        detail_layout.addWidget(self.det_text)

        splitter.addWidget(self.detail_frame)
        splitter.setSizes([320, 220])
        root_layout.addWidget(splitter)

    def update_data(self, audit_result: Optional[AuditResult]) -> None:
        if not audit_result or not hasattr(audit_result, "findings"):
            self.all_findings = []
        else:
            self.all_findings = list(audit_result.findings)

        # Update category dropdown choices
        cats = sorted({f.category for f in self.all_findings if f.category})
        cur_cat = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("All Categories")
        for c in cats:
            self.category_combo.addItem(c)
        idx = self.category_combo.findText(cur_cat)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        self.category_combo.blockSignals(False)

        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search_bar.text().lower().strip()
        sev_filter = self.severity_combo.currentText()
        cat_filter = self.category_combo.currentText()
        stat_filter = self.status_combo.currentText()

        self.filtered_findings = []
        for f in self.all_findings:
            f_sev = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            f_stat = f.status.value if hasattr(f.status, "value") else str(f.status)

            if sev_filter != "All Severities" and f_sev.upper() != sev_filter.upper():
                continue
            if cat_filter != "All Categories" and f.category != cat_filter:
                continue
            if stat_filter != "All Statuses" and f_stat.upper() != stat_filter.upper():
                continue

            if query:
                haystack = f"{f.title} {f.description} {f.evidence} {f.rationale} {f.recommendation} {f.category}".lower()
                if query not in haystack:
                    continue

            self.filtered_findings.append(f)

        self._render_table()

    def _render_table(self) -> None:
        self.table.setRowCount(len(self.filtered_findings))
        self.count_label.setText(f"{len(self.filtered_findings)} of {len(self.all_findings)} findings")

        for row, f in enumerate(self.filtered_findings):
            sev_str = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            stat_str = f.status.value if hasattr(f.status, "value") else str(f.status)

            sev_item = QTableWidgetItem(sev_str)
            sev_color = SEVERITY_COLORS.get(sev_str.upper(), "#ffffff")
            sev_item.setForeground(QColor(sev_color))
            sev_item.setBackground(QColor(0, 0, 0, 0))
            sev_item.setTextAlignment(Qt.AlignCenter)

            stat_item = QTableWidgetItem(stat_str)
            stat_item.setTextAlignment(Qt.AlignCenter)
            if stat_str == "FAIL":
                stat_item.setForeground(Qt.GlobalColor(Qt.red))
            elif stat_str == "WARNING":
                stat_item.setForeground(Qt.GlobalColor(Qt.yellow))
            elif stat_str == "PASS":
                stat_item.setForeground(Qt.GlobalColor(Qt.green))
            else:
                stat_item.setForeground(Qt.GlobalColor(Qt.gray))

            cat_item = QTableWidgetItem(f.category)
            title_item = QTableWidgetItem(f.title)
            plat_item = QTableWidgetItem(f.platform or "host")

            self.table.setItem(row, 0, sev_item)
            self.table.setItem(row, 1, stat_item)
            self.table.setItem(row, 2, cat_item)
            self.table.setItem(row, 3, title_item)
            self.table.setItem(row, 4, plat_item)

        if self.filtered_findings:
            self.table.selectRow(0)
        else:
            self._clear_detail()

    def _on_row_selected(self) -> None:
        sel_rows = self.table.selectionModel().selectedRows()
        if not sel_rows:
            return
        row = sel_rows[0].row()
        if 0 <= row < len(self.filtered_findings):
            f = self.filtered_findings[row]
            self._show_detail(f)

    def set_theme(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        if self._selected_finding:
            self._show_detail(self._selected_finding)

    def _show_detail(self, f: Finding) -> None:
        self._selected_finding = f
        sev_str = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
        stat_str = f.status.value if hasattr(f.status, "value") else str(f.status)
        sev_color = SEVERITY_COLORS.get(sev_str.upper(), "#ffffff")

        self.det_title.setText(f.title)
        self.det_badge.setText(f" {sev_str} | {stat_str} ")
        self.det_badge.setStyleSheet(f"background-color: {sev_color}; color: black; font-weight: bold; border-radius: 4px; padding: 4px 8px;")

        self.det_meta.setText(f"Rule ID: {f.rule_id}  •  Category: {f.category}  •  Platform: {f.platform}")

        if self._is_dark:
            rat_color = "#FFD600"
            rec_color = "#00C853"
            pre_style = "background: #0d1117; padding: 10px; border: 1px solid #30363d; border-radius: 6px; color: #79c0ff; font-family: monospace;"
        else:
            rat_color = "#b45309"
            rec_color = "#15803d"
            pre_style = "background: #f8fafc; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; color: #0f172a; font-family: monospace;"

        html_content = f"""
        <p><strong>Description:</strong><br>{f.description}</p>
        <p><strong>Rationale / Why it matters:</strong><br><span style="color: {rat_color}; font-weight: 500;">{f.rationale or 'N/A'}</span></p>
        <p><strong>Evidence Collected:</strong><br><pre style="{pre_style}">{f.evidence or 'None'}</pre></p>
        <p><strong>Remediation Recommendation:</strong><br><span style="color: {rec_color}; font-weight: 500;">{f.recommendation or 'None'}</span></p>
        """
        self.det_text.setHtml(html_content)

    def _clear_detail(self) -> None:
        self._selected_finding = None
        self.det_title.setText("No finding selected")
        self.det_badge.setText("")
        self.det_badge.setStyleSheet("")
        self.det_meta.setText("")
        self.det_text.setHtml("<p style='color: #888;'>No findings match the current filter criteria.</p>")
