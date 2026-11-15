from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPaintEvent
from PySide6.QtCore import Qt, QRectF, Property, QPropertyAnimation

from core.models import RiskLevel

class ScoreWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self._score = 0.0
        self._target_score = 0.0
        self._risk_level = "UNKNOWN"
        self._dark_theme = True
        self._animation = QPropertyAnimation(self, b"score_prop")
        self._animation.setDuration(1000)

    def set_theme(self, is_dark: bool):
        self._dark_theme = is_dark
        self.update()

    def get_score_prop(self):
        return self._score

    def set_score_prop(self, val):
        self._score = float(val)
        self.update()

    score_prop = Property(float, get_score_prop, set_score_prop)

    def set_score(self, score: float, risk_level: str):
        self._target_score = max(0.0, min(100.0, float(score)))
        self._risk_level = risk_level if risk_level is not None else "UNKNOWN"
        self._animation.setStartValue(self._score)
        self._animation.setEndValue(self._target_score)
        self._animation.start()

    def _risk_label(self) -> str:
        value = str(self._risk_level)
        if "." in value:
            value = value.split(".")[-1]
        return value.replace("_", " ").upper()

    def _get_color(self) -> QColor:
        risk_label = self._risk_label()
        if "CRITICAL" in risk_label:
            return QColor("#FF1744")
        if "HIGH" in risk_label:
            return QColor("#FF6D00")
        if "NEEDS IMPROVEMENT" in risk_label:
            return QColor("#FFD600")
        if "GOOD" in risk_label:
            return QColor("#00C853")
        if "EXCELLENT" in risk_label:
            return QColor("#00C853")

        # Fallback based on score
        if self._score >= 80:
            return QColor("#00C853")
        if self._score >= 60:
            return QColor("#FFD600")
        if self._score >= 40:
            return QColor("#FF6D00")
        return QColor("#FF1744")

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        size = min(rect.width(), rect.height()) - 40
        x = (rect.width() - size) / 2
        y = (rect.height() - size) / 2
        arc_rect = QRectF(x, y, size, size)

        pen_bg = QPen(QColor("#333344" if self._dark_theme else "#e0e0e0"))
        pen_bg.setWidth(15)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(arc_rect, -210 * 16, 240 * 16)

        pen_fg = QPen(self._get_color())
        pen_fg.setWidth(15)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)

        span_angle = int((max(0.0, min(self._score, 100.0)) / 100.0) * 240 * 16)
        painter.drawArc(arc_rect, -210 * 16, span_angle)

        cx = rect.width() / 2.0
        cy = rect.height() / 2.0

        score_color = QColor("#FFFFFF" if self._dark_theme else "#212121")
        painter.setPen(score_color)
        font = QFont("Segoe UI", 36, QFont.Bold)
        font.setStyleHint(QFont.SansSerif)
        painter.setFont(font)
        score_rect = QRectF(0, cy - 36, rect.width(), 44)
        painter.drawText(score_rect, Qt.AlignCenter, f"{int(round(self._score))}")

        font_risk = QFont("Segoe UI", 12, QFont.Bold)
        font_risk.setStyleHint(QFont.SansSerif)
        painter.setFont(font_risk)
        painter.setPen(self._get_color())
        risk_rect = QRectF(0, cy + 20, rect.width(), 26)
        painter.drawText(risk_rect, Qt.AlignCenter, self._risk_label())

        painter.end()
