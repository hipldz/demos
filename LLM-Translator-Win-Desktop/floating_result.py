"""Non-modal text processing result card that preserves the source text."""

from __future__ import annotations

from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QCursor, QTextCursor
from PyQt5.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget,
)


class FloatingResult(QWidget):
    """Show processed text near the pointer without activating on show."""

    def __init__(self):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("LLM Translator · 结果")
        self.setFixedWidth(470)
        self._drag_offset = None
        self._user_moved = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        card = QFrame()
        self.card = card
        card.setObjectName("floatingCard")
        outer.addWidget(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 19)
        layout.setSpacing(13)

        self.drag_handle = QWidget()
        self.drag_handle.setCursor(Qt.OpenHandCursor)
        header = QHBoxLayout(self.drag_handle)
        header.setContentsMargins(0, 0, 0, 0)
        self.heading = QLabel("处理结果")
        self.heading.setCursor(Qt.OpenHandCursor)
        header.addWidget(self.heading, 1)
        self.copy_button = QPushButton("复制")
        self.copy_button.setObjectName("copy")
        self.copy_button.setFocusPolicy(Qt.NoFocus)
        self.copy_button.clicked.connect(self.copy_text)
        header.addWidget(self.copy_button)
        close = QPushButton("关闭")
        close.setFocusPolicy(Qt.NoFocus)
        close.clicked.connect(self.hide)
        header.addWidget(close)
        layout.addWidget(self.drag_handle)

        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setMinimumHeight(120)
        self.editor.setMaximumHeight(240)
        layout.addWidget(self.editor)
        footer = QLabel("拖动标题可移动 · 原文保持不变")
        self.footer = footer
        layout.addWidget(footer)
        self.set_theme("light")
        # Install after all widgets exist: Qt can dispatch eventFilter during installation.
        self.drag_handle.installEventFilter(self)
        self.heading.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj in (getattr(self, "heading", None), getattr(self, "drag_handle", None)):
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
                obj.setCursor(Qt.ClosedHandCursor)
                return True
            if event.type() == QEvent.MouseMove and self._drag_offset is not None:
                if event.buttons() & Qt.LeftButton:
                    self.move(event.globalPos() - self._drag_offset)
                    self._user_moved = True
                return True
            if event.type() == QEvent.MouseButtonRelease and self._drag_offset is not None:
                self._drag_offset = None
                obj.setCursor(Qt.OpenHandCursor)
                return True
        return super().eventFilter(obj, event)

    def set_theme(self, mode: str):
        if mode == "dark":
            self.card.setStyleSheet(
                "QFrame#floatingCard {background:#1b2533; border:1px solid #3e4e64; border-radius:17px;}"
                "QLabel {background:transparent; color:#e7ecf5; font-size:13px;}"
                "QPlainTextEdit {background:#17202d; color:#e7ecf5; border:1px solid #34445b;"
                "border-radius:11px; font-size:14px; padding:13px;}"
                "QPushButton {background:#28384d; color:#e7ecf5; border:1px solid #465a75; border-radius:9px;"
                "padding:8px 13px; font-weight:500;}"
                "QPushButton:hover {background:#364a64;}"
                "QPushButton#copy {background:#4a81e6; border-color:#4a81e6; color:white;}"
                "QPushButton#copy:hover {background:#6092ef;}"
            )
            self.heading.setStyleSheet("font-size:16px; font-weight:600; color:#e7ecf5;")
            self.footer.setStyleSheet("color:#a0afc3; font-size:12px;")
        else:
            self.card.setStyleSheet(
                "QFrame#floatingCard {background:#fff; border:1px solid #dfe5ee; border-radius:17px;}"
                "QLabel {background:transparent; color:#293241; font-size:13px;}"
                "QPlainTextEdit {background:#f8fafc; color:#293241; border:1px solid #e2e8f0;"
                "border-radius:11px; font-size:14px; padding:13px;}"
                "QPushButton {background:#fff; color:#334155; border:1px solid #dbe3ee; border-radius:9px;"
                "padding:8px 13px; font-weight:500;}"
                "QPushButton:hover {background:#f1f5fb;}"
                "QPushButton#copy {background:#3575dc; border-color:#3575dc; color:white;}"
                "QPushButton#copy:hover {background:#2b65c4;}"
            )
            self.heading.setStyleSheet("font-size:16px; font-weight:600; color:#293241;")
            self.footer.setStyleSheet("color:#798699; font-size:12px;")

    def show_result(self, text: str, mode: str):
        self.heading.setText(mode + " · 结果")
        self.editor.setPlainText(text)
        self.editor.moveCursor(QTextCursor.Start)
        self.copy_button.setText("复制")
        self.adjustSize()

        desktop = QApplication.desktop()
        if self._user_moved:
            available = desktop.availableGeometry(self.pos())
            preferred_x, preferred_y = self.x(), self.y()
        else:
            cursor = QCursor.pos()
            available = desktop.availableGeometry(cursor)
            preferred_x, preferred_y = cursor.x() + 20, cursor.y() + 22
        x = min(max(preferred_x, available.left()), max(available.left(), available.right() - self.width() + 1))
        y = min(max(preferred_y, available.top()), max(available.top(), available.bottom() - self.height() + 1))
        self.move(x, y)
        self.show()  # WA_ShowWithoutActivating: don't steal the browser's focus.

    def copy_text(self):
        QApplication.clipboard().setText(self.editor.toPlainText())
        self.copy_button.setText("已复制")
        QTimer.singleShot(1200, lambda: self.copy_button.setText("复制"))
