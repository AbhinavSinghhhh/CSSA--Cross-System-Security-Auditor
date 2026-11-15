from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout,
    QFrame, QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from gui.widgets.score_widget import ScoreWidget
from gui.widgets.stat_card import StatCard

class Dashboard(QWidget):
    run_audit_requested = Signal()
    export_report_requested = Signal()

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
        layout.setSpacing(18)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🛡️ Security Dashboard")
        title_label.setObjectName("viewTitle")
        header_layout.addWidget(title_label)

        self.os_info_label = QLabel("OS: Unavailable | Host: Unavailable | User: Unavailable | Privilege: Standard")
        self.os_info_label.setObjectName("viewSubtitle")
        header_layout.addWidget(self.os_info_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addLayout(header_layout)

        # Empty State Banner
        self.empty_banner = QFrame()
        self.empty_banner.setObjectName("infoBanner")
        eb_layout = QHBoxLayout(self.empty_banner)
        eb_layout.setContentsMargins(12, 8, 12, 8)
        self.banner_icon = QLabel("💡")
        self.banner_icon.setStyleSheet("font-size: 20px;")
        eb_layout.addWidget(self.banner_icon)
        self.banner_text = QLabel(
            "No audit data loaded. Select an audit mode (Real System or Demo) in the top bar "
            "and click 'RUN SECURITY AUDIT' to evaluate host security posture."
        )
        self.banner_text.setObjectName("infoBannerText")
        eb_layout.addWidget(self.banner_text, 1)
        layout.addWidget(self.empty_banner)

        # Main metrics row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)

        # Score gauge
        score_container = QFrame()
        score_container.setObjectName("card")
        score_layout = QVBoxLayout(score_container)
        score_layout.setAlignment(Qt.AlignCenter)
        gauge_title = QLabel("Overall Security Score")
        gauge_title.setObjectName("cardHeader")
        gauge_title.setAlignment(Qt.AlignCenter)
        score_layout.addWidget(gauge_title)

        self.score_widget = ScoreWidget()
        score_layout.addWidget(self.score_widget)
        metrics_layout.addWidget(score_container, 1)

        # Stat cards grid
        stats_container = QFrame()
        stats_container.setObjectName("card")
        stats_vbox = QVBoxLayout(stats_container)
        stats_title = QLabel("Finding Severity Breakdown")
        stats_title.setObjectName("cardHeader")
        stats_vbox.addWidget(stats_title)

        stats_layout = QGridLayout()
        stats_layout.setSpacing(12)
        self.crit_card = StatCard("Critical", "0", "🔴", "#FF1744")
        self.high_card = StatCard("High", "0", "🟠", "#FF6D00")
        self.med_card = StatCard("Medium", "0", "🟡", "#FFD600")
        self.low_card = StatCard("Low", "0", "🟢", "#00C853")

        stats_layout.addWidget(self.crit_card, 0, 0)
        stats_layout.addWidget(self.high_card, 0, 1)
        stats_layout.addWidget(self.med_card, 1, 0)
        stats_layout.addWidget(self.low_card, 1, 1)
        stats_vbox.addLayout(stats_layout)

        metrics_layout.addWidget(stats_container, 2)
        layout.addLayout(metrics_layout)

        # Category Breakdown Section
        self.cat_frame = QFrame()
        self.cat_frame.setObjectName("card")
        cat_box = QVBoxLayout(self.cat_frame)
        cat_box.setSpacing(12)

        cat_hdr = QHBoxLayout()
        cat_title = QLabel("📊 Category Security Breakdown")
        cat_title.setObjectName("cardHeader")
        cat_hdr.addWidget(cat_title)
        cat_hdr.addStretch()
        cat_box.addLayout(cat_hdr)

        self.categories_layout = QVBoxLayout()
        self.categories_layout.setSpacing(10)
        cat_box.addLayout(self.categories_layout)

        self.no_cat_label = QLabel("Run an audit to view category posture and progress bars.")
        self.no_cat_label.setStyleSheet("color: #888; font-style: italic; padding: 10px 0;")
        self.categories_layout.addWidget(self.no_cat_label)

        layout.addWidget(self.cat_frame)

        # Actions
        actions_layout = QHBoxLayout()
        self.btn_run_audit = QPushButton("🚀 RUN SECURITY AUDIT")
        self.btn_run_audit.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                font-weight: bold;
                font-size: 15px;
                padding: 14px 28px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #ff5c77;
            }
        """)
        self.btn_run_audit.clicked.connect(self.run_audit_requested.emit)

        self.btn_export = QPushButton("📄 EXPORT REPORT")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: white;
                font-weight: bold;
                font-size: 15px;
                padding: 14px 28px;
                border-radius: 8px;
                border: 1px solid #1a4f8b;
            }
            QPushButton:hover {
                background-color: #1a4f8b;
            }
            QPushButton:disabled {
                background-color: #22223b;
                color: #666;
                border-color: #333344;
            }
        """)
        self.btn_export.clicked.connect(self.export_report_requested.emit)
        self.btn_export.setEnabled(False)

        actions_layout.addWidget(self.btn_run_audit)
        actions_layout.addWidget(self.btn_export)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        self._is_dark = True
        self._last_score_obj = None

    def update_data(self, audit_result):
        if not audit_result:
            return

        self.empty_banner.hide()

        sys_info = getattr(audit_result, 'system_info', None)
        if sys_info:
            os_name = getattr(sys_info, 'os_name', 'Unknown')
            hostname = getattr(sys_info, 'hostname', 'Unknown')
            user = getattr(sys_info, 'current_user', 'Unknown')
            privilege = getattr(sys_info, 'privilege_level', 'Standard')
            self.os_info_label.setText(f"OS: {os_name}  |  Host: {hostname}  |  User: {user}  |  Privilege: {privilege}")

        score_obj = getattr(audit_result, 'score', None)
        self._last_score_obj = score_obj
        if score_obj:
            score_val = getattr(score_obj, 'overall_score', 0.0)
            risk = getattr(score_obj, 'risk_level', "UNKNOWN")
            self.score_widget.set_score(score_val, str(risk))
            self._update_category_bars(score_obj)

        if score_obj:
            crit = getattr(score_obj, 'critical_count', 0)
            high = getattr(score_obj, 'high_count', 0)
            med = getattr(score_obj, 'medium_count', 0)
            low = getattr(score_obj, 'low_count', 0)
        else:
            findings = getattr(audit_result, 'findings', [])
            active_findings = [
                f for f in findings
                if str(getattr(f, 'status', '')).upper() in ("FAIL", "WARNING", "FINDINGSTATUS.FAIL", "FINDINGSTATUS.WARNING")
            ]
            crit = sum(1 for f in active_findings if "CRITICAL" in str(getattr(f, 'severity', '')).upper())
            high = sum(1 for f in active_findings if "HIGH" in str(getattr(f, 'severity', '')).upper())
            med = sum(1 for f in active_findings if "MEDIUM" in str(getattr(f, 'severity', '')).upper())
            low = sum(1 for f in active_findings if "LOW" in str(getattr(f, 'severity', '')).upper())

        self.crit_card.set_value(str(crit))
        self.high_card.set_value(str(high))
        self.med_card.set_value(str(med))
        self.low_card.set_value(str(low))

        self.btn_export.setEnabled(True)

    def _update_category_bars(self, score_obj):
        while self.categories_layout.count():
            item = self.categories_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        cat_scores = getattr(score_obj, 'category_scores', [])
        if not cat_scores:
            lbl = QLabel("No category scoring data available.")
            lbl.setStyleSheet("color: #888; font-style: italic;")
            self.categories_layout.addWidget(lbl)
            return

        name_color = "#eeeeee" if self._is_dark else "#212121"
        pbar_bg = "#1a1a2e" if self._is_dark else "#f0f2f5"
        pbar_border = "#0f3460" if self._is_dark else "#d0d5dd"

        for cs in cat_scores:
            cat_name = getattr(cs, 'category', 'Unknown')
            val = getattr(cs, 'score', 100)
            max_val = getattr(cs, 'max_score', 100)
            f_count = getattr(cs, 'findings_count', 0)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 4, 0, 4)
            row_layout.setSpacing(14)

            name_lbl = QLabel(cat_name)
            name_lbl.setFixedWidth(200)
            name_lbl.setStyleSheet(f"color: {name_color}; font-weight: bold; font-size: 13px;")
            row_layout.addWidget(name_lbl)

            pbar = QProgressBar()
            pbar.setRange(0, max_val)
            pbar.setValue(int(val))
            pbar.setTextVisible(False)
            pbar.setFixedHeight(12)

            if val >= 85:
                chunk_color = "#00C853"
            elif val >= 70:
                chunk_color = "#FFD600"
            elif val >= 50:
                chunk_color = "#FF6D00"
            else:
                chunk_color = "#FF1744"

            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {pbar_bg};
                    border: 1px solid {pbar_border};
                    border-radius: 6px;
                }}
                QProgressBar::chunk {{
                    background-color: {chunk_color};
                    border-radius: 5px;
                }}
            """)
            row_layout.addWidget(pbar, 1)

            score_lbl = QLabel(f"{int(val)}/{max_val}")
            score_lbl.setFixedWidth(60)
            score_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            score_lbl.setStyleSheet(f"color: {chunk_color}; font-weight: bold; font-size: 13px;")
            row_layout.addWidget(score_lbl)

            f_badge = QLabel(f"{f_count} findings" if f_count != 1 else "1 finding")
            f_badge.setFixedWidth(90)
            f_badge.setAlignment(Qt.AlignCenter)
            if f_count > 0:
                if self._is_dark:
                    f_badge.setStyleSheet(
                        "background-color: #2a1525; color: #ff5c77; border: 1px solid #e94560; "
                        "border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;"
                    )
                else:
                    f_badge.setStyleSheet(
                        "background-color: #ffebee; color: #d32f2f; border: 1px solid #ffcdd2; "
                        "border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;"
                    )
            else:
                if self._is_dark:
                    f_badge.setStyleSheet(
                        "background-color: #0f2a1a; color: #00C853; border: 1px solid #00C853; "
                        "border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;"
                    )
                else:
                    f_badge.setStyleSheet(
                        "background-color: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; "
                        "border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;"
                    )
            row_layout.addWidget(f_badge)

            self.categories_layout.addWidget(row_widget)

    def set_theme(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        self.score_widget.set_theme(is_dark)
        if self._last_score_obj:
            self._update_category_bars(self._last_score_obj)
