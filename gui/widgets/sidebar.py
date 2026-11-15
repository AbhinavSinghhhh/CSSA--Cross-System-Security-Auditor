"""Navigation sidebar with icons and hover effects."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, Signal


NAV_ITEMS = [
    ("Dashboard",            "🏠"),
    ("System Information",   "💻"),
    ("Users & Privileges",   "👤"),
    ("Processes",            "⚙️"),
    ("Services",             "🔧"),
    ("Firewall",             "🛡️"),
    ("Network",              "🌐"),
    ("Packet Capture",       "🦈"),
    ("File Permissions",     "📁"),
    ("Startup & Persistence","🚀"),
    ("Findings",             "🔍"),
    ("History",              "📊"),
    ("Baseline",             "📋"),
    ("Reports",              "📄"),
    ("Settings",             "⚙️"),
]


class Sidebar(QWidget):
    """Vertical sidebar navigation emitting the selected view name."""

    item_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("sidebarList")
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.list_widget)

        for text, icon in NAV_ITEMS:
            item = QListWidgetItem(f"{icon}  {text}")
            item.setData(Qt.UserRole, text)
            self.list_widget.addItem(item)

        self.list_widget.currentItemChanged.connect(self._on_item_changed)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_item_changed(self, current, _previous):
        if current:
            self.item_selected.emit(current.data(Qt.UserRole))

    def set_current_item(self, name: str) -> None:
        """Select a navigation item by view name."""
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item.data(Qt.UserRole) == name:
                self.list_widget.setCurrentRow(row)
                break
