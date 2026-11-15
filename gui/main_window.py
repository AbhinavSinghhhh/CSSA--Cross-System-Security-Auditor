"""Main application window — sidebar, stacked views, audit controller."""

from __future__ import annotations

import logging
import traceback
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt, QObject
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QComboBox, QLabel, QStatusBar,
    QMessageBox, QApplication,
)

from core.auditor import Auditor
from core.models import AuditMode, AuditResult
from database.db import DatabaseManager
from utils.paths import get_rules_dir, get_fixtures_dir, get_db_path

logger = logging.getLogger(__name__)

# ── Stylesheet ───────────────────────────────────────────────

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #eeeeee;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}
QLabel { color: #eeeeee; }
QLabel#viewTitle {
    font-size: 24px;
    font-weight: bold;
    color: #eeeeee;
}
QLabel#viewSubtitle {
    font-size: 13px;
    color: #aaaaaa;
}
QWidget#topBar {
    background-color: #0f0f23;
    border-bottom: 2px solid #0f3460;
}
QLabel#appTitle {
    font-size: 18px;
    font-weight: bold;
    color: #e94560;
}
QLabel#modeLabel {
    color: #aaaaaa;
    font-size: 12px;
    font-weight: bold;
}
Sidebar#sidebar {
    background-color: #0f0f23;
    border-right: 2px solid #0f3460;
}
QListWidget#sidebarList {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget#sidebarList::item {
    color: #aaaaaa;
    padding: 10px 14px;
    font-size: 13px;
    border-radius: 6px;
    margin: 2px 8px;
}
QListWidget#sidebarList::item:hover {
    background-color: #1a1a2e;
    color: #eeeeee;
}
QListWidget#sidebarList::item:selected {
    background-color: #0f3460;
    color: #ffffff;
    font-weight: bold;
}
QFrame#card, QGroupBox {
    background-color: #16213e;
    color: #eeeeee;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 12px;
}
QGroupBox::title {
    color: #e94560;
    font-weight: bold;
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QLabel#cardHeader {
    color: #aaaaaa;
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
}
QLabel#cardValue {
    color: #ffffff;
    font-size: 16px;
    font-weight: 600;
}
QFrame#filterBar {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 6px;
    padding: 6px;
}
QFrame#infoBanner {
    background-color: #0f3460;
    border: 1px solid #1a4f8b;
    border-radius: 8px;
    padding: 12px 18px;
}
QLabel#infoBannerText {
    color: #eeeeee;
    font-size: 13px;
}
QPushButton {
    background-color: #0f3460;
    color: #eeeeee;
    border: 1px solid #16213e;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
}
QPushButton:hover { background-color: #1a4a8a; }
QPushButton:pressed { background-color: #0a2540; }
QPushButton:disabled { background-color: #333; color: #777; }
QPushButton#accent {
    background-color: #e94560;
    border: none;
}
QPushButton#accent:hover { background-color: #ff5a78; }
QComboBox, QLineEdit, QSpinBox {
    background-color: #16213e;
    color: #eeeeee;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 24px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #eeeeee;
    selection-background-color: #0f3460;
    selection-color: #ffffff;
}
QTableWidget {
    background-color: #16213e;
    alternate-background-color: #1a1a2e;
    color: #eeeeee;
    gridline-color: #0f3460;
    border: 1px solid #0f3460;
    border-radius: 6px;
    selection-background-color: #0f3460;
    selection-color: #ffffff;
}
QTableWidget::item { padding: 4px; }
QHeaderView::section {
    background-color: #0f0f23;
    color: #aaaaaa;
    border: 1px solid #0f3460;
    padding: 6px;
    font-weight: bold;
}
QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar:horizontal {
    background-color: #1a1a2e;
    height: 10px;
}
QScrollBar::handle:horizontal {
    background-color: #0f3460;
    border-radius: 5px;
}
QProgressBar {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 4px;
    text-align: center;
    color: #eeeeee;
}
QProgressBar::chunk {
    background-color: #00C853;
    border-radius: 3px;
}
QStatusBar { background-color: #0f0f23; color: #aaaaaa; }
QScrollArea {
    background-color: transparent;
    border: none;
}
QTextEdit {
    background-color: #16213e;
    color: #eeeeee;
    border: 1px solid #0f3460;
    border-radius: 6px;
}
QTextEdit#codeBox {
    background-color: #101528;
    color: #88d49e;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    border: 1px solid #0f3460;
    border-radius: 6px;
    padding: 10px;
}
QListWidget {
    background-color: #16213e;
    alternate-background-color: #1a2744;
    color: #eeeeee;
    border: 1px solid #0f3460;
    border-radius: 6px;
}
QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #1a2744;
}
QListWidget::item:hover {
    background-color: #0f3460;
}
QListWidget::item:selected {
    background-color: #0f3460;
    color: #ffffff;
}
QTabWidget::pane { border: 1px solid #0f3460; }
QTabBar::tab {
    background-color: #16213e;
    color: #aaaaaa;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #0f3460;
    color: #eeeeee;
}
"""

LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #f5f7fa;
    color: #212121;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}
QLabel { color: #212121; }
QLabel#viewTitle {
    font-size: 24px;
    font-weight: bold;
    color: #0d47a1;
}
QLabel#viewSubtitle {
    font-size: 13px;
    color: #555555;
}
QWidget#topBar {
    background-color: #ffffff;
    border-bottom: 2px solid #e0e0e0;
}
QLabel#appTitle {
    font-size: 18px;
    font-weight: bold;
    color: #d32f2f;
}
QLabel#modeLabel {
    color: #424242;
    font-size: 12px;
    font-weight: bold;
}
Sidebar#sidebar {
    background-color: #ffffff;
    border-right: 2px solid #e0e0e0;
}
QListWidget#sidebarList {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget#sidebarList::item {
    color: #424242;
    padding: 10px 14px;
    font-size: 13px;
    border-radius: 6px;
    margin: 2px 8px;
}
QListWidget#sidebarList::item:hover {
    background-color: #e3f2fd;
    color: #1565c0;
}
QListWidget#sidebarList::item:selected {
    background-color: #1565c0;
    color: #ffffff;
    font-weight: bold;
}
QFrame#card, QGroupBox {
    background-color: #ffffff;
    color: #212121;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px;
}
QGroupBox::title {
    color: #1565c0;
    font-weight: bold;
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QLabel#cardHeader {
    color: #616161;
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
}
QLabel#cardValue {
    color: #111111;
    font-size: 16px;
    font-weight: 600;
}
QFrame#filterBar {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px;
}
QFrame#infoBanner {
    background-color: #e3f2fd;
    border: 1px solid #90caf9;
    border-radius: 8px;
    padding: 12px 18px;
}
QLabel#infoBannerText {
    color: #0d47a1;
    font-size: 13px;
}
QPushButton {
    background-color: #1565c0;
    color: #ffffff;
    border: 1px solid #1565c0;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1976d2;
    border: 1px solid #1976d2;
}
QPushButton:pressed {
    background-color: #0d47a1;
    border: 1px solid #0d47a1;
}
QPushButton:disabled {
    background-color: #e0e0e0;
    color: #9e9e9e;
    border: 1px solid #e0e0e0;
}
QPushButton#accent {
    background-color: #d32f2f;
    color: #ffffff;
    border: 1px solid #d32f2f;
}
QPushButton#accent:hover {
    background-color: #e53935;
    border: 1px solid #e53935;
}
QComboBox, QLineEdit, QSpinBox {
    background-color: #ffffff;
    color: #212121;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 24px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #212121;
    selection-background-color: #e3f2fd;
    selection-color: #1565c0;
}
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f9fbfd;
    color: #212121;
    gridline-color: #e0e0e0;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    selection-background-color: #bbdefb;
    selection-color: #0d47a1;
}
QTableWidget::item { padding: 4px; }
QHeaderView::section {
    background-color: #f0f4f8;
    color: #333333;
    border: 1px solid #e0e0e0;
    padding: 6px;
    font-weight: bold;
}
QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #bdbdbd;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar:horizontal {
    background-color: #f0f0f0;
    height: 10px;
}
QScrollBar::handle:horizontal {
    background-color: #bdbdbd;
    border-radius: 5px;
}
QProgressBar {
    background-color: #e0e0e0;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    text-align: center;
    color: #212121;
}
QProgressBar::chunk {
    background-color: #2e7d32;
    border-radius: 3px;
}
QStatusBar { background-color: #e0e0e0; color: #424242; }
QScrollArea {
    background-color: transparent;
    border: none;
}
QTextEdit {
    background-color: #ffffff;
    color: #212121;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
}
QTextEdit#codeBox {
    background-color: #f4f6f8;
    color: #1b5e20;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 10px;
}
QListWidget {
    background-color: #ffffff;
    alternate-background-color: #f7f9fc;
    color: #212121;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
}
QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #eef2f6;
}
QListWidget::item:hover {
    background-color: #e3f2fd;
}
QListWidget::item:selected {
    background-color: #1976d2;
    color: #ffffff;
}
QTabWidget::pane { border: 1px solid #e0e0e0; }
QTabBar::tab {
    background-color: #e0e0e0;
    color: #616161;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #1565c0;
    color: #ffffff;
}
"""


# ── Audit Worker ──────────────────────────────────────────────

class AuditWorker(QObject):
    """Runs the audit in a background thread."""
    finished = Signal(object)  # AuditResult
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, auditor: Auditor, mode: AuditMode) -> None:
        super().__init__()
        self.auditor = auditor
        self.mode = mode

    def run(self) -> None:
        try:
            self.progress.emit("Running security audit...")
            result = self.auditor.run_audit(self.mode)
            self.finished.emit(result)
        except Exception as exc:
            logger.error("Audit failed: %s", exc, exc_info=True)
            self.error.emit(str(exc))


# ── Main Window ───────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Application main window with sidebar navigation and stacked views."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CSSA — Cross-Platform System Security Auditor")
        self.setMinimumSize(1280, 800)

        self.audit_result: AuditResult | None = None
        self._dark_theme = True
        self._thread: QThread | None = None

        # Core services
        self.auditor = Auditor(get_rules_dir(), get_fixtures_dir())
        self.db = DatabaseManager(get_db_path())
        self.db.initialize()
        self._build_ui()
        saved_theme = self.db.get_setting("theme", "dark")
        self._dark_theme = (saved_theme != "light")
        self._apply_theme()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──────────────────────────────
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(48)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("🛡️  CSSA")
        title.setObjectName("appTitle")
        top_layout.addWidget(title)
        top_layout.addStretch()

        mode_lbl = QLabel("Mode:")
        mode_lbl.setObjectName("modeLabel")
        top_layout.addWidget(mode_lbl)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("REAL SYSTEM", AuditMode.REAL)
        self.mode_combo.addItem("DEMO — WINDOWS", AuditMode.DEMO_WINDOWS)
        self.mode_combo.addItem("DEMO — LINUX", AuditMode.DEMO_LINUX)
        self.mode_combo.addItem("DEMO — MACOS", AuditMode.DEMO_MACOS)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        top_layout.addWidget(self.mode_combo)

        root.addWidget(top_bar)

        # ── Demo banner ──────────────────────────
        self.demo_banner = QLabel("⚠️  DEMO MODE — SIMULATED DATA  ⚠️")
        self.demo_banner.setAlignment(Qt.AlignCenter)
        self.demo_banner.setStyleSheet(
            "background-color: #FF6D00; color: white; font-weight: bold; "
            "font-size: 14px; padding: 6px;"
        )
        self.demo_banner.hide()
        root.addWidget(self.demo_banner)

        # ── Content area ─────────────────────────
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # Sidebar
        from gui.widgets.sidebar import Sidebar
        self.sidebar = Sidebar()
        self.sidebar.item_selected.connect(self._on_nav)
        content.addWidget(self.sidebar)

        # Stacked views
        self.stack = QStackedWidget()
        self._init_views()
        content.addWidget(self.stack, 1)

        root.addLayout(content, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — select a mode and run an audit")

    def _init_views(self) -> None:
        """Lazy-import and instantiate all views."""
        from gui.dashboard import Dashboard
        from gui.system_view import SystemView
        from gui.users_view import UsersView
        from gui.processes_view import ProcessesView
        from gui.services_view import ServicesView
        from gui.firewall_view import FirewallView
        from gui.network_view import NetworkView
        from gui.packet_capture_view import PacketCaptureView
        from gui.permissions_view import PermissionsView
        from gui.startup_view import StartupView
        from gui.findings_view import FindingsView
        from gui.history_view import HistoryView
        from gui.baseline_view import BaselineView
        from gui.reports_view import ReportsView
        from gui.settings_view import SettingsView

        self.dashboard = Dashboard()
        self.dashboard.run_audit_requested.connect(self.run_audit)
        self.dashboard.export_report_requested.connect(self._export_report)

        self._view_map: dict[str, QWidget] = {
            "Dashboard": self.dashboard,
            "System Information": SystemView(),
            "Users & Privileges": UsersView(),
            "Processes": ProcessesView(),
            "Services": ServicesView(),
            "Firewall": FirewallView(),
            "Network": NetworkView(),
            "Packet Capture": PacketCaptureView(),
            "File Permissions": PermissionsView(),
            "Startup & Persistence": StartupView(),
            "Findings": FindingsView(),
            "History": HistoryView(),
            "Baseline": BaselineView(),
            "Reports": ReportsView(),
            "Settings": SettingsView(),
        }

        for widget in self._view_map.values():
            self.stack.addWidget(widget)

        # Give views that need it a reference to shared state
        if hasattr(self._view_map.get("History"), "set_db"):
            self._view_map["History"].set_db(self.db, self)
        if hasattr(self._view_map.get("Baseline"), "set_db"):
            self._view_map["Baseline"].set_db(self.db, self)
        if hasattr(self._view_map.get("Reports"), "set_references"):
            self._view_map["Reports"].set_references(self.db, self.auditor, self)
        if hasattr(self._view_map.get("Settings"), "set_main_window"):
            self._view_map["Settings"].set_main_window(self, self.db, self.auditor)

    # ── navigation ────────────────────────────────────────────

    def _on_nav(self, name: str) -> None:
        widget = self._view_map.get(name)
        if widget:
            self.stack.setCurrentWidget(widget)

    def _on_mode_changed(self, index: int) -> None:
        raw_mode = self.mode_combo.currentData()
        mode = AuditMode(raw_mode) if isinstance(raw_mode, str) else raw_mode
        if mode == AuditMode.REAL:
            self.demo_banner.hide()
        else:
            self.demo_banner.show()

    # ── audit execution ───────────────────────────────────────

    def run_audit(self) -> None:
        if self._thread and self._thread.isRunning():
            self.status_bar.showMessage("Audit already in progress...")
            return

        raw_mode = self.mode_combo.currentData()
        mode = AuditMode(raw_mode) if isinstance(raw_mode, str) else raw_mode
        self.status_bar.showMessage(f"Starting audit ({mode.value})...")

        self._thread = QThread()
        self._worker = AuditWorker(self.auditor, mode)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_audit_complete)
        self._worker.error.connect(self._on_audit_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)

        self._thread.start()

    def _on_audit_complete(self, result: AuditResult) -> None:
        self.audit_result = result
        self.status_bar.showMessage(
            f"Audit complete — Score: {result.score.overall_score}/100  "
            f"({result.score.risk_level.value})  "
            f"Findings: {len(result.findings)}"
        )

        # Save to database
        try:
            self.db.save_audit(result)
        except Exception as exc:
            logger.error("Failed to save audit to database: %s", exc)

        # Update all views
        for view in self._view_map.values():
            if hasattr(view, "update_data"):
                try:
                    view.update_data(result)
                except Exception as exc:
                    logger.error("Error updating view %s: %s",
                                 view.__class__.__name__, exc)

    def _on_audit_error(self, msg: str) -> None:
        self.status_bar.showMessage(f"Audit failed: {msg}")
        QMessageBox.warning(self, "Audit Error",
                            f"The audit encountered an error:\n\n{msg}")

    def load_historical_audit(self, audit_id: str) -> None:
        """Load an audit from the SQLite database and display across all views."""
        audit = self.db.get_audit(audit_id)
        if not audit:
            QMessageBox.warning(self, "Load Error", f"Could not find audit {audit_id} in database.")
            return

        self.audit_result = audit
        score_val = audit.score.overall_score if audit.score else "N/A"
        risk_val = audit.score.risk_level.value if audit.score and hasattr(audit.score.risk_level, 'value') else "Unknown"
        self.status_bar.showMessage(
            f"Loaded historical audit {audit.timestamp} — Score: {score_val}/100 ({risk_val})"
        )

        # Update all views
        for view in self._view_map.values():
            if hasattr(view, "update_data"):
                try:
                    view.update_data(audit)
                except Exception as exc:
                    logger.error("Error updating view %s: %s", view.__class__.__name__, exc)

        # Switch to Dashboard view
        self.stack.setCurrentWidget(self.dashboard)
        self.sidebar.set_current_item("Dashboard")
        QMessageBox.information(
            self,
            "Historical Audit Loaded",
            f"Successfully loaded audit from {audit.timestamp} into all views.\n"
            f"Score: {score_val}/100  |  Findings: {len(audit.findings)}"
        )

    # ── reports ───────────────────────────────────────────────

    def _export_report(self) -> None:
        if not self.audit_result:
            QMessageBox.information(self, "No Data",
                                    "Run an audit first before exporting a report.")
            return
        reports = self._view_map.get("Reports")
        if reports:
            self.stack.setCurrentWidget(reports)
            self.sidebar.set_current_item("Reports")
            if hasattr(reports, "_on_save_as"):
                reports._on_save_as()
            elif hasattr(reports, "generate_report"):
                reports.generate_report(self.audit_result)
        else:
            from reports.html_report import HTMLReportGenerator
            from utils.paths import get_reports_dir
            gen = HTMLReportGenerator()
            path = gen.generate(self.audit_result, get_reports_dir() / "audit_report.html")
            QMessageBox.information(self, "Report Generated", f"Report saved to:\n{path}")

    # ── theme ─────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        app = QApplication.instance()
        if app:
            app.setStyleSheet(DARK_STYLE if self._dark_theme else LIGHT_STYLE)
        for view in getattr(self, "_view_map", {}).values():
            if hasattr(view, "set_theme"):
                try:
                    view.set_theme(self._dark_theme)
                except Exception:
                    pass

    def toggle_theme(self) -> None:
        self._dark_theme = not self._dark_theme
        self._apply_theme()
