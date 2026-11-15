"""User accounts and privilege auditing view with real-time filtering."""

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

from core.models import AuditResult, UserAccount


class UsersView(QWidget):
    """View displaying local user accounts, administrative memberships, and login configurations."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.all_users: List[UserAccount] = []
        self.filtered_users: List[UserAccount] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("👥 Local Users & Privilege Escalation Surface")
        title.setObjectName("viewTitle")
        header.addWidget(title)

        self.count_label = QLabel("0 accounts")
        self.count_label.setObjectName("viewSubtitle")
        header.addWidget(self.count_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addLayout(header)

        # Filters
        filter_bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search username, UID, groups, home directory...")
        self.search.textChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.search, 3)

        self.role_filter = QComboBox()
        self.role_filter.addItems(["All Accounts", "Administrators Only", "Standard Users Only", "Disabled Accounts", "Guest Accounts"])
        self.role_filter.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.role_filter, 1)

        layout.addLayout(filter_bar)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Username", "UID", "Privileged (Admin)", "Disabled", "Guest", "Assigned Groups", "Home Directory"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def update_data(self, audit_result: Optional[AuditResult]) -> None:
        if not audit_result or not hasattr(audit_result, "users"):
            self.all_users = []
        else:
            self.all_users = list(audit_result.users)
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search.text().lower().strip()
        role = self.role_filter.currentText()

        self.filtered_users = []
        for u in self.all_users:
            if role == "Administrators Only" and not u.is_admin:
                continue
            if role == "Standard Users Only" and u.is_admin:
                continue
            if role == "Disabled Accounts" and not u.is_disabled:
                continue
            if role == "Guest Accounts" and not u.is_guest:
                continue

            if query:
                haystack = f"{u.username} {u.uid} {' '.join(u.groups)} {u.home_directory} {u.description}".lower()
                if query not in haystack:
                    continue

            self.filtered_users.append(u)

        self._render_table()

    def _render_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.filtered_users))
        self.count_label.setText(f"{len(self.filtered_users)} of {len(self.all_users)} accounts")

        for row, u in enumerate(self.filtered_users):
            uname_item = QTableWidgetItem(u.username)
            if u.description:
                uname_item.setToolTip(u.description)

            uid_item = QTableWidgetItem(str(u.uid))
            uid_item.setTextAlignment(Qt.AlignCenter)

            admin_item = QTableWidgetItem("YES" if u.is_admin else "No")
            admin_item.setTextAlignment(Qt.AlignCenter)
            if u.is_admin:
                admin_item.setForeground(Qt.GlobalColor(Qt.red))
                uname_item.setForeground(Qt.GlobalColor(Qt.red))

            dis_item = QTableWidgetItem("YES" if u.is_disabled else "No")
            dis_item.setTextAlignment(Qt.AlignCenter)

            guest_item = QTableWidgetItem("YES" if u.is_guest else "No")
            guest_item.setTextAlignment(Qt.AlignCenter)

            groups_item = QTableWidgetItem(", ".join(u.groups))
            home_item = QTableWidgetItem(u.home_directory)

            self.table.setItem(row, 0, uname_item)
            self.table.setItem(row, 1, uid_item)
            self.table.setItem(row, 2, admin_item)
            self.table.setItem(row, 3, dis_item)
            self.table.setItem(row, 4, guest_item)
            self.table.setItem(row, 5, groups_item)
            self.table.setItem(row, 6, home_item)

        self.table.setSortingEnabled(True)
