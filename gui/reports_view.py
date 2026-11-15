"""Reports view allowing generation, inspection, and multi-format exporting of audit reports."""

from __future__ import annotations

import logging
import os
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.baseline import BaselineManager
from core.models import AuditResult
from reports import (
    CSVReportGenerator,
    HTMLReportGenerator,
    JSONReportGenerator,
    MarkdownReportGenerator,
    PDFReportGenerator,
)
from utils.paths import get_reports_dir

logger = logging.getLogger(__name__)


class ReportsView(QWidget):
    """View managing security audit report generation, multi-format export, and archive history."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.audit_result: Optional[AuditResult] = None
        self.db = None
        self.auditor = None
        self.main_window = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("📄 Security Audit Reports & Export")
        title.setObjectName("viewTitle")
        layout.addWidget(title)

        subtitle = QLabel("Generate comprehensive executive reports in HTML, PDF, JSON, CSV, and Markdown.")
        subtitle.setObjectName("viewSubtitle")
        layout.addWidget(subtitle)

        # ── Generation Panel ──────────────────────────────────
        frame = QFrame()
        frame.setObjectName("card")
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(16, 16, 16, 16)
        f_layout.setSpacing(12)

        self.status_label = QLabel("No audit loaded. Run an audit first to generate reports.")
        self.status_label.setStyleSheet("color: #e94560; font-weight: bold;")
        f_layout.addWidget(self.status_label)

        self.diff_check = QCheckBox("Include Baseline Diff (Configuration Drift) in exported reports")
        f_layout.addWidget(self.diff_check)

        # Action Buttons Row 1: Primary Export
        btns_row1 = QHBoxLayout()
        btns_row1.setSpacing(10)

        self.btn_save_as = QPushButton("💾 Save Report As... (Choose Format & Location)")
        self.btn_save_as.setObjectName("accent")
        self.btn_save_as.setEnabled(False)
        self.btn_save_as.clicked.connect(self._on_save_as)
        btns_row1.addWidget(self.btn_save_as)

        self.btn_html = QPushButton("🌐 HTML Report")
        self.btn_html.setEnabled(False)
        self.btn_html.clicked.connect(self._on_generate_html)
        btns_row1.addWidget(self.btn_html)

        self.btn_pdf = QPushButton("📑 PDF Report")
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self._on_generate_pdf)
        btns_row1.addWidget(self.btn_pdf)

        btns_row1.addStretch()
        f_layout.addLayout(btns_row1)

        # Action Buttons Row 2: Secondary Data Exports
        btns_row2 = QHBoxLayout()
        btns_row2.setSpacing(10)

        self.btn_json = QPushButton("📦 Export JSON Data")
        self.btn_json.setEnabled(False)
        self.btn_json.clicked.connect(self._on_generate_json)
        btns_row2.addWidget(self.btn_json)

        self.btn_csv = QPushButton("📊 Export CSV Findings")
        self.btn_csv.setEnabled(False)
        self.btn_csv.clicked.connect(self._on_generate_csv)
        btns_row2.addWidget(self.btn_csv)

        self.btn_md = QPushButton("📝 Export Markdown Summary")
        self.btn_md.setEnabled(False)
        self.btn_md.clicked.connect(self._on_generate_markdown)
        btns_row2.addWidget(self.btn_md)

        btns_row2.addStretch()
        f_layout.addLayout(btns_row2)

        layout.addWidget(frame)

        # ── History Panel ─────────────────────────────────────
        hist_title = QLabel("Report Archive & Export History")
        hist_title.setObjectName("cardHeader")
        layout.addWidget(hist_title)

        self.list = QListWidget()
        self.list.setAlternatingRowColors(True)
        self.list.itemDoubleClicked.connect(self._on_open_selected)
        layout.addWidget(self.list)

        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        self.open_btn = QPushButton("📂 Open Selected Report")
        self.open_btn.clicked.connect(self._on_open_selected)
        action_bar.addWidget(self.open_btn)

        self.reveal_btn = QPushButton("🔍 Reveal in Folder")
        self.reveal_btn.clicked.connect(self._on_reveal_selected)
        action_bar.addWidget(self.reveal_btn)

        self.refresh_btn = QPushButton("🔄 Refresh List")
        self.refresh_btn.clicked.connect(self._refresh_report_list)
        action_bar.addWidget(self.refresh_btn)

        action_bar.addStretch()
        layout.addLayout(action_bar)

        self._refresh_report_list()

    def set_references(self, db, auditor, main_window=None) -> None:
        self.db = db
        self.auditor = auditor
        self.main_window = main_window

    def update_data(self, audit_result: AuditResult) -> None:
        self.audit_result = audit_result
        if audit_result:
            score = audit_result.score.overall_score if audit_result.score else 0
            mode = audit_result.mode.value if audit_result.mode else "REAL"
            self.status_label.setText(
                f"Active Audit Loaded: {mode} (Score: {score}/100, Findings: {len(audit_result.findings)})"
            )
            self.status_label.setStyleSheet("color: #00C853; font-weight: bold;")
            self.btn_save_as.setEnabled(True)
            self.btn_html.setEnabled(True)
            self.btn_pdf.setEnabled(True)
            self.btn_json.setEnabled(True)
            self.btn_csv.setEnabled(True)
            self.btn_md.setEnabled(True)
        self._refresh_report_list()

    def _get_baseline_diff(self, res: AuditResult) -> Optional[Any]:
        if self.diff_check.isChecked() and self.db:
            try:
                baselines = self.db.get_baselines()
                if baselines:
                    items = self.db.get_baseline_items(baselines[0]["id"])
                    current_items = BaselineManager.create_baseline(res)
                    return BaselineManager.compare_baseline(items, current_items)
            except Exception as e:
                logger.warning("Could not compute baseline diff for report: %s", e)
        return None

    def export_to_file(
        self,
        audit_result: AuditResult,
        out_path: Path,
        fmt: str = "html",
    ) -> Optional[Path]:
        """Export audit result to a specific target file path."""
        baseline_diff = self._get_baseline_diff(audit_result)
        out_path = Path(out_path)

        if fmt == "html":
            gen = HTMLReportGenerator()
            return gen.generate(audit_result, out_path, baseline_diff=baseline_diff)
        elif fmt == "pdf":
            gen = PDFReportGenerator()
            res = gen.generate(audit_result, out_path, baseline_diff=baseline_diff)
            if res and res.exists():
                return res
            # Fallback to HTML if PDF libraries are missing
            html_fallback = out_path.with_suffix(".html")
            gen_html = HTMLReportGenerator()
            return gen_html.generate(audit_result, html_fallback, baseline_diff=baseline_diff)
        elif fmt == "json":
            gen = JSONReportGenerator()
            return gen.generate(audit_result, out_path, baseline_diff=baseline_diff)
        elif fmt == "csv":
            gen = CSVReportGenerator()
            return gen.generate(audit_result, out_path, baseline_diff=baseline_diff)
        elif fmt in ("md", "markdown"):
            gen = MarkdownReportGenerator()
            return gen.generate(audit_result, out_path, baseline_diff=baseline_diff)
        return None

    def generate_report(
        self,
        audit_result: Optional[AuditResult] = None,
        fmt: str = "html",
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Generate a report saved to the default archive directory."""
        res = audit_result or self.audit_result
        if not res:
            QMessageBox.warning(self, "No Audit Data", "Please execute an audit first before generating reports.")
            return None

        reports_dir = output_dir or get_reports_dir()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        plat = res.system_info.platform.value if res.system_info else "host"

        ext_map = {"html": "html", "pdf": "pdf", "json": "json", "csv": "csv", "md": "md"}
        ext = ext_map.get(fmt, "html")
        out_path = reports_dir / f"CSSA_Audit_{plat}_{ts}.{ext}"

        saved = self.export_to_file(res, out_path, fmt=fmt)
        self._refresh_report_list()

        if saved and saved.exists():
            format_names = {
                "html": "HTML Security Report",
                "pdf": "PDF Security Report",
                "json": "JSON Data Export",
                "csv": "CSV Findings Export",
                "md": "Markdown Report",
            }
            f_title = format_names.get(fmt, "Security Report")
            reply = QMessageBox.question(
                self,
                f"{f_title} Generated",
                f"{f_title} successfully saved at:\n{saved}\n\nWould you like to open it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                webbrowser.open(saved.as_uri())
            return saved
        return None

    def _on_save_as(self) -> None:
        res = self.audit_result
        if not res:
            QMessageBox.warning(self, "No Audit Data", "Please execute an audit first before exporting.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        plat = res.system_info.platform.value if res.system_info else "host"
        default_name = f"CSSA_Audit_{plat}_{ts}"

        filter_str = (
            "HTML Report (*.html);;"
            "PDF Report (*.pdf);;"
            "JSON Security Data (*.json);;"
            "CSV Findings Table (*.csv);;"
            "Markdown Report (*.md)"
        )
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Security Audit Report As",
            str(Path.home() / f"{default_name}.html"),
            filter_str,
        )
        if not file_path:
            return

        path = Path(file_path)
        ext = path.suffix.lower()
        if "html" in selected_filter.lower() or ext == ".html":
            fmt = "html"
        elif "pdf" in selected_filter.lower() or ext == ".pdf":
            fmt = "pdf"
        elif "json" in selected_filter.lower() or ext == ".json":
            fmt = "json"
        elif "csv" in selected_filter.lower() or ext == ".csv":
            fmt = "csv"
        elif "markdown" in selected_filter.lower() or ext in (".md", ".markdown"):
            fmt = "md"
        else:
            fmt = "html"

        saved = self.export_to_file(res, path, fmt=fmt)
        if saved and saved.exists():
            reply = QMessageBox.question(
                self,
                "Report Exported Successfully",
                f"Security report successfully saved to:\n{saved}\n\nWould you like to open it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                webbrowser.open(saved.as_uri())

    def _on_generate_html(self) -> None:
        self.generate_report(fmt="html")

    def _on_generate_pdf(self) -> None:
        self.generate_report(fmt="pdf")

    def _on_generate_json(self) -> None:
        self.generate_report(fmt="json")

    def _on_generate_csv(self) -> None:
        self.generate_report(fmt="csv")

    def _on_generate_markdown(self) -> None:
        self.generate_report(fmt="md")

    def _on_open_selected(self) -> None:
        current_item = self.list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Select Report", "Please select a report file from the archive list first.")
            return
        file_path = current_item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            webbrowser.open(Path(file_path).as_uri())
        else:
            QMessageBox.warning(self, "File Not Found", f"Report file no longer exists:\n{file_path}")

    def _on_reveal_selected(self) -> None:
        current_item = self.list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Select Report", "Please select a report file to reveal.")
            return
        file_path = current_item.data(Qt.UserRole)
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"File does not exist:\n{file_path}")
            return

        try:
            if os.name == "nt":
                subprocess.run(["explorer", f"/select,{file_path}"], check=False)
            elif os.uname().sysname == "Darwin":
                subprocess.run(["open", "-R", file_path], check=False)
            else:
                subprocess.run(["xdg-open", str(Path(file_path).parent)], check=False)
        except Exception as exc:
            logger.warning("Could not reveal file: %s", exc)

    def _refresh_report_list(self) -> None:
        self.list.clear()
        try:
            reports_dir = get_reports_dir()
            if not reports_dir.exists():
                return

            valid_exts = (".html", ".pdf", ".json", ".csv", ".md")
            files = sorted(
                [f for f in reports_dir.iterdir() if f.suffix.lower() in valid_exts],
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            icon_map = {
                ".html": "🌐",
                ".pdf": "📑",
                ".json": "📦",
                ".csv": "📊",
                ".md": "📝",
            }

            for f in files:
                size_kb = round(f.stat().st_size / 1024, 1)
                dt_str = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                icon = icon_map.get(f.suffix.lower(), "📄")
                item = QListWidgetItem(f"{icon}  {f.name}   ({size_kb} KB, {dt_str})")
                item.setData(Qt.UserRole, str(f.resolve()))
                self.list.addItem(item)
        except (PermissionError, OSError) as exc:
            logger.warning("Could not access reports directory: %s", exc)
