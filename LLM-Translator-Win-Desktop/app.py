"""LLM Translator: a focused Windows text processor."""

from __future__ import annotations

from datetime import datetime
from copy import deepcopy
import sys

from PyQt5.QtCore import Qt, QPoint, QRectF, QPointF, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QFont, QFontDatabase, QPainter, QPalette, QPen
from PyQt5.QtWidgets import (
    QAbstractSpinBox, QApplication, QCheckBox, QFrame,
    QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel, QLayout, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMenu, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea,
    QSpinBox, QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from desktop import HotkeyListener, TranslationWorker
from floating_result import FloatingResult
from hotkeys import parse_hotkey
from modes import current_mode, new_mode
from secret_store import SecretStorageError, get_saved_api_key
from settings_store import DEFAULTS, read_config, save_config
from translator import TranslationError, load_settings
from vector_icons import ASSETS, brand_icon, tray_icon, nav_icon, theme_icon
from windows_titlebar import set_native_titlebar_theme


COLORS = {
    "accent": "#326bc6", "success": "#23835b", "warning": "#b27621",
    "error": "#c3484c", "muted": "#7b8494", "idle": "#346eb9",
    "busy": "#94641f",
}
DARK_COLORS = {
    "accent": "#91b9ff", "success": "#67c9a3", "warning": "#f1b966",
    "error": "#f18d94", "muted": "#a0afc3", "idle": "#91b9ff",
    "busy": "#e7b568",
}

STYLE = """
QWidget { color: #202124; font-size: 14px; }
QMainWindow, QWidget#root { background: #f8fafc; }
QLabel { background: transparent; }
QFrame#sidebar { background: #f1f4f9; border-right: 1px solid #e6eaf1; }
QFrame#card { background: #ffffff; border: 1px solid #e4e8ef; border-radius: 16px; }
QLabel#brand { font-size: 16px; font-weight: 600; color: #202124; }
QLabel#pageTitle { font-size: 25px; font-weight: 600; color: #202124; }
QLabel#sectionTitle { font-size: 16px; font-weight: 600; color: #293241; }
QLabel#muted { color: #697386; font-size: 13px; }
QLabel#eyebrow { color: #68758a; font-size: 12px; font-weight: 500; }
QLabel#fieldLabel { color: #465165; font-size: 14px; font-weight: 500; }
QLabel#modeTag { color: #4c6688; background: #f0f5fc; border: 1px solid #e1eaf5; border-radius: 9px; font-size: 12px; padding: 6px 8px; }
QLabel#statusText { font-size: 13px; font-weight: 600; }
QPushButton { min-height: 23px; padding: 9px 15px; background: #ffffff; color: #334155; border: 1px solid #dde3ed; border-radius: 10px; font-weight: 500; }
QPushButton:hover { background: #f3f6fb; border-color: #c8d4e6; }
QPushButton:pressed { background: #e9eff9; }
QPushButton:focus { border-color: #6b95e1; }
QPushButton#primary { background: #3575dc; color: #ffffff; border: 1px solid #3575dc; }
QPushButton#primary:hover { background: #2b65c4; border-color: #2b65c4; }
QPushButton#themeToggle { background: transparent; border: 1px solid transparent; border-radius: 11px; padding: 6px; min-height: 0; }
QPushButton#themeToggle:hover { background: #e9eef6; border-color: #dae2ef; }
QPushButton#nav { border: 1px solid transparent; background: transparent; text-align: left; padding: 12px 14px; color: #5f6b7c; border-radius: 12px; font-size: 14px; font-weight: 500; }
QPushButton#nav:hover { background: #e8edf5; color: #243347; }
QPushButton#nav:checked { background: #e0ebff; color: #2465bc; border: 1px solid transparent; }
QWidget#segmented { background: #f0f3f8; border: 1px solid #e1e6ee; border-radius: 11px; }
QPushButton#segment { background: transparent; border: 1px solid transparent; border-radius: 8px; color: #69768a; padding: 7px 10px; }
QPushButton#segment:hover { background: #e8edf6; color: #31435d; }
QPushButton#segment:checked { background: #ffffff; color: #2c67bb; border-color: #dde5f0; }
QLineEdit, QSpinBox { background: #ffffff; color: #253247; border: 1px solid #dbe1e9; border-radius: 10px; padding: 9px 12px; min-height: 24px; selection-background-color: #c9ddff; }
QLineEdit:hover, QSpinBox:hover { border-color: #bbc9da; }
QLineEdit:focus, QSpinBox:focus { border: 1px solid #6d99e3; }
QLineEdit:disabled, QSpinBox:disabled { color: #9aa3af; background: #f5f7fa; }
QPlainTextEdit { background: #ffffff; color: #293241; border: 1px solid #dfe5ee; border-radius: 11px; padding: 13px; font-size: 14px; selection-background-color: #c9ddff; }
QPlainTextEdit:focus { border: 1px solid #6d99e3; }
QPlainTextEdit#resultBox { background: #f7f9fc; border-color: #eef1f5; }
QListWidget { background: #f9fafc; border: 1px solid #e5eaf1; border-radius: 12px; padding: 6px; outline: none; }
QListWidget::item { padding: 13px 12px; border-radius: 9px; color: #4d5a6d; }
QListWidget::item:hover { background: #eef3fa; }
QListWidget::item:selected { background: #e1ebff; color: #2465bc; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { width: 8px; margin: 3px 0; background: transparent; }
QScrollBar::handle:vertical { background: #cdd6e3; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QCheckBox { spacing: 11px; color: #334155; font-size: 14px; }
QCheckBox::indicator { width: 19px; height: 19px; }
QCheckBox::indicator:unchecked { image: url("__CHECK_OFF_PATH__"); }
QCheckBox::indicator:checked { image: url("__CHECK_ON_PATH__"); }
QMenu { background: #ffffff; color: #293241; border: 1px solid #e4e8f1; border-radius: 10px; padding: 7px; }
QMenu::item { padding: 8px 23px; border-radius: 6px; }
QMenu::item:selected { background: #e8f0fe; }
QMenu::separator { height: 1px; background: #e7ebf2; margin: 6px 10px; }
QMenu#selectMenu { border: 1px solid #dfe5ed; padding: 6px; border-radius: 11px; }
QMenu#selectMenu::item { padding: 10px 12px; margin: 2px; border-radius: 7px; }
QMenu#selectMenu::item:selected { background: #eaf2ff; color: #285fab; }
QToolTip { background: #ffffff; color: #293241; border: 1px solid #ccd6e3; padding: 7px; }
"""

DARK_STYLE = """
QWidget { color: #e7ecf5; }
QMainWindow, QWidget#root { background: #10151f; }
QFrame#sidebar { background: #151d29; border-right: 1px solid #273446; }
QFrame#card { background: #1b2533; border: 1px solid #303d50; }
QLabel#brand, QLabel#pageTitle, QLabel#sectionTitle { color: #eef3fb; }
QLabel#muted, QLabel#eyebrow { color: #9ba9bd; }
QLabel#fieldLabel { color: #c8d2e2; }
QLabel#modeTag { color: #b8cffa; background: #273c56; border: 1px solid #3a526e; }
QPushButton { background: #263348; color: #e4eaf4; border: 1px solid #3c4b61; }
QPushButton:hover { background: #31425b; border-color: #526886; }
QPushButton:pressed { background: #202c3e; }
QPushButton:focus { border-color: #7aa0e6; }
QPushButton#primary { background: #4a81e6; border-color: #4a81e6; color: #fff; }
QPushButton#primary:hover { background: #6092ef; border-color: #6092ef; }
QPushButton#themeToggle { background: transparent; border-color: transparent; }
QPushButton#themeToggle:hover { background: #293a51; border-color: #40536d; }
QPushButton#nav { background: transparent; color: #a2afc0; border-color: transparent; }
QPushButton#nav:hover { background: #233147; color: #eef3fa; }
QPushButton#nav:checked { background: #293b59; color: #a7c5ff; border-color: transparent; }
QWidget#segmented { background: #172231; border-color: #39495e; }
QPushButton#segment { background: transparent; border-color: transparent; color: #a1aec2; }
QPushButton#segment:hover { background: #283a51; color: #e3efff; }
QPushButton#segment:checked { background: #3a5476; color: #e6f1ff; border-color: #506b8e; }
QLineEdit, QSpinBox { background: #202b3b; color: #e6edf7; border-color: #3a485b; selection-background-color: #3e639d; }
QLineEdit:hover, QSpinBox:hover { border-color: #647791; }
QLineEdit:focus, QSpinBox:focus { border-color: #82a5e8; }
QLineEdit:disabled, QSpinBox:disabled { background: #1a2532; color: #7e8da3; }
QPlainTextEdit { background: #192333; color: #e4eaf3; border-color: #38475a; selection-background-color: #3e639d; }
QPlainTextEdit:focus { border-color: #82a5e8; }
QPlainTextEdit#resultBox { background: #17202d; border-color: #2b3748; }
QListWidget { background: #192333; border-color: #344357; }
QListWidget::item { color: #c4cfdf; }
QListWidget::item:hover { background: #25364d; }
QListWidget::item:selected { background: #2c4264; color: #e7f1ff; }
QScrollBar::handle:vertical { background: #526078; }
QCheckBox { color: #c8d2e1; }
QCheckBox::indicator:unchecked { image: url("__DARK_CHECK_OFF_PATH__"); }
QMenu, QMenu#selectMenu { background: #202b3b; color: #e5ecf7; border: 1px solid #435169; }
QMenu::item:selected, QMenu#selectMenu::item:selected { background: #2f4564; color: #d9e9ff; }
QMenu::separator { background: #3c4b61; }
QToolTip { background: #283648; color: #edf3fa; border-color: #4c607b; }
"""


def theme_stylesheet(mode: str) -> str:
    sheet = (STYLE + (DARK_STYLE if mode == "dark" else ""))
    paths = {
        "__CHECK_ON_PATH__": "check-on.svg",
        "__CHECK_OFF_PATH__": "check-off.svg",
        "__DARK_CHECK_OFF_PATH__": "check-off-dark.svg",
    }
    for token, filename in paths.items():
        sheet = sheet.replace(token, (ASSETS / filename).as_posix())
    return sheet


def text_label(value: str, style: str = "", selectable: bool = False, wrap: bool = False) -> QLabel:
    label = QLabel(value)
    if style:
        label.setObjectName(style)
    # Functional labels stay on one line; only explanatory copy opts into wrapping.
    label.setWordWrap(wrap)
    if selectable:
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return label


def make_card(parent_layout, *, name="card", padding=22) -> tuple[QFrame, QVBoxLayout]:
    card = QFrame()
    card.setObjectName(name)
    contents = QVBoxLayout(card)
    contents.setContentsMargins(padding, padding, padding, padding)
    contents.setSpacing(14)
    parent_layout.addWidget(card)
    return card, contents


class SimpleSelect(QPushButton):
    """Stable popup selector: no native QComboBox popup frame or clipping quirks."""

    currentIndexChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hovered = False
        self._options: list[tuple[str, object]] = []
        self._index = -1
        self.setMinimumHeight(42)
        self.setCursor(Qt.PointingHandCursor)
        self._menu = QMenu(self)
        self._menu.setObjectName("selectMenu")
        self.clicked.connect(self._show_options)

    def addItem(self, label: str, data: object = None):
        self._options.append((label, data))
        if self._index == -1:
            self.setCurrentIndex(0)

    def clear(self):
        self._options.clear()
        self._index = -1
        self.update()

    def currentIndex(self) -> int:
        return self._index

    def setCurrentIndex(self, index: int):
        if not 0 <= index < len(self._options) or index == self._index:
            return
        self._index = index
        self.update()
        self.currentIndexChanged.emit(index)

    def findData(self, value: object) -> int:
        return next((i for i, (_, data) in enumerate(self._options) if data == value), -1)

    def itemData(self, index: int):
        return self._options[index][1] if 0 <= index < len(self._options) else None

    def currentData(self):
        return self.itemData(self._index)

    def currentText(self) -> str:
        return self._options[self._index][0] if self._index >= 0 else ""

    def _show_options(self):
        self._menu.clear()
        for i, (label, _) in enumerate(self._options):
            action = self._menu.addAction(label)
            action.triggered.connect(lambda checked=False, idx=i: self.setCurrentIndex(idx))
        if self._options:
            self._menu.setFixedWidth(self.width())
            self._menu.popup(self.mapToGlobal(QPoint(0, self.height() + 4)))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Down) and self._options:
            step = 1 if event.key() == Qt.Key_Down else -1
            self.setCurrentIndex((self._index + step) % len(self._options))
            return
        super().keyPressEvent(event)

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(max(42, hint.height()))
        return hint

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        dark = QApplication.instance().property("ui_theme") == "dark"
        border = ("#657fa7" if self.hasFocus() else "#4d586c" if self._hovered else "#384357") if dark else ("#87a9e2" if self.hasFocus() else "#c5cfdd" if self._hovered else "#dee4ed")
        fill = "#202b3c" if dark else "#f4f6fa" if not self.isEnabled() else "#ffffff"
        painter.setPen(QPen(QColor(border), 1))
        painter.setBrush(QColor(fill))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 10, 10)
        painter.setPen(QColor("#dfe6f5" if dark else "#9aa4b3" if not self.isEnabled() else "#344054"))
        label = self.fontMetrics().elidedText(self.currentText(), Qt.ElideRight, max(1, self.width() - 55))
        painter.drawText(QRectF(14, 0, self.width() - 52, self.height()), Qt.AlignVCenter | Qt.AlignLeft, label)
        cx, cy = self.width() - 21, self.height() / 2
        arrow_pen = QPen(QColor("#8491a4"))
        arrow_pen.setWidthF(1.7)
        arrow_pen.setCapStyle(Qt.RoundCap)
        arrow_pen.setJoinStyle(Qt.RoundJoin)
        arrow_pen.setColor(QColor("#9eacc1" if dark else "#8491a4"))
        painter.setPen(arrow_pen)
        painter.drawLine(QPointF(cx - 5, cy - 2), QPointF(cx, cy + 3))
        painter.drawLine(QPointF(cx, cy + 3), QPointF(cx + 5, cy - 2))
        painter.end()


class SegmentedChoice(QWidget):
    """Compact direct choice for two-option settings; no popup needed."""

    currentIndexChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("segmented")
        self._options: list[tuple[str, object]] = []
        self._buttons: list[QPushButton] = []
        self._index = -1
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(3, 3, 3, 3)
        self._layout.setSpacing(3)

    def addItem(self, label: str, data: object = None):
        index = len(self._options)
        self._options.append((label, data))
        button = QPushButton(label)
        button.setObjectName("segment")
        button.setCheckable(True)
        button.clicked.connect(lambda checked=False, idx=index: self.setCurrentIndex(idx))
        self._layout.addWidget(button, 1)
        self._buttons.append(button)
        if self._index == -1:
            self.setCurrentIndex(0)

    def clear(self):
        for button in self._buttons:
            self._layout.removeWidget(button)
            button.deleteLater()
        self._buttons.clear()
        self._options.clear()
        self._index = -1

    def setCurrentIndex(self, index: int):
        if not 0 <= index < len(self._options):
            return
        self._index = index
        for i, button in enumerate(self._buttons):
            button.setChecked(i == index)
        self.currentIndexChanged.emit(index)

    def findData(self, value: object) -> int:
        return next((i for i, (_, data) in enumerate(self._options) if data == value), -1)

    def itemData(self, index: int):
        return self._options[index][1] if 0 <= index < len(self._options) else None

    def currentData(self):
        return self.itemData(self._index)


class TrayPopup(QWidget):
    """A compact, theme-aware tray panel instead of a native Windows menu."""

    def __init__(self, owner):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint)
        self.owner = owner
        self.setObjectName("trayPopup")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedWidth(314)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(13, 13, 13, 13)
        self.surface = QFrame()
        self.surface.setObjectName("traySurface")
        outer.addWidget(self.surface)
        content = QVBoxLayout(self.surface)
        content.setContentsMargins(18, 18, 18, 14)
        content.setSpacing(10)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(26)
        shadow.setOffset(0, 7)
        shadow.setColor(QColor(10, 30, 60, 45))
        self.surface.setGraphicsEffect(shadow)

        title_row = QHBoxLayout()
        self.logo = QLabel()
        self.logo.setPixmap(brand_icon().pixmap(27, 27))
        self.logo.setFixedSize(27, 27)
        title_row.addWidget(self.logo)
        title = QLabel("LLM Translator")
        title.setObjectName("trayName")
        title_row.addWidget(title, 1)
        content.addLayout(title_row)

        self.status = QLabel("●  就绪")
        self.status.setObjectName("trayStatus")
        self.status.setWordWrap(False)
        content.addWidget(self.status)
        self._add_divider(content)

        content.addWidget(self._section("Prompt"))
        self.mode_scroller = QScrollArea()
        self.mode_scroller.setObjectName("trayModeScroll")
        self.mode_scroller.setWidgetResizable(True)
        self.mode_scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mode_scroller.viewport().setAutoFillBackground(False)
        mode_host = QWidget()
        mode_host.setObjectName("trayModeHost")
        mode_host.setAutoFillBackground(False)
        self.mode_rows = QVBoxLayout(mode_host)
        self.mode_rows.setContentsMargins(0, 0, 0, 0)
        self.mode_rows.setSpacing(4)
        self.mode_scroller.setWidget(mode_host)
        content.addWidget(self.mode_scroller)
        self.mode_buttons = {}

        content.addWidget(self._section("输出方式"))
        self.output_choice = SegmentedChoice()
        self.output_choice.addItem("替换", "replace")
        self.output_choice.addItem("悬浮", "float")
        self.output_choice.currentIndexChanged.connect(
            lambda index: self.owner._set_output_mode(self.output_choice.itemData(index))
        )
        content.addWidget(self.output_choice)

        content.addWidget(self._section("外观"))
        self.theme_choice = SegmentedChoice()
        self.theme_choice.addItem("浅色", "light")
        self.theme_choice.addItem("深色", "dark")
        for mode, button in zip(("light", "dark"), self.theme_choice._buttons):
            button.setIcon(theme_icon(mode))
            button.setIconSize(QSize(17, 17))
        self.theme_choice.currentIndexChanged.connect(
            lambda index: self.owner.theme_field.setCurrentIndex(
                self.owner.theme_field.findData(self.theme_choice.itemData(index))
            )
        )
        content.addWidget(self.theme_choice)
        self._add_divider(content)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.open_button = QPushButton("打开主窗口")
        self.open_button.setObjectName("trayAction")
        self.open_button.clicked.connect(self._open_main)
        action_row.addWidget(self.open_button, 1)
        self.pause_button = QPushButton("暂停监听")
        self.pause_button.setObjectName("trayAction")
        self.pause_button.clicked.connect(self._pause)
        action_row.addWidget(self.pause_button, 1)
        content.addLayout(action_row)
        self.exit_button = QPushButton("退出 LLM Translator")
        self.exit_button.setObjectName("trayExit")
        self.exit_button.clicked.connect(self._exit)
        content.addWidget(self.exit_button)
        self.set_theme("light")

    @staticmethod
    def _section(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("traySection")
        return label

    @staticmethod
    def _add_divider(layout):
        line = QFrame()
        line.setObjectName("trayDivider")
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)

    def sync_modes(self, modes: list[dict], active_id: str):
        while self.mode_rows.count():
            item = self.mode_rows.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.mode_buttons.clear()
        for profile in modes:
            button = QPushButton()
            button.setObjectName("trayMode")
            button.setCursor(Qt.PointingHandCursor)
            button.setCheckable(True)
            button.setToolTip(profile["name"])
            self.mode_rows.addWidget(button)
            self.mode_buttons[profile["id"]] = (button, profile["name"])
            button.clicked.connect(lambda checked, uid=profile["id"]: self._choose_mode(uid))
        self.mode_scroller.setFixedHeight(min(len(modes), 4) * 38 + max(0, min(len(modes), 4) - 1) * 4 + 2)
        self.sync_mode(active_id)

    def sync_mode(self, active_id: str):
        for mode_id, (button, name) in self.mode_buttons.items():
            selected = mode_id == active_id
            button.setChecked(selected)
            name = button.fontMetrics().elidedText(name, Qt.ElideRight, 206)
            button.setText(name)

    def sync_output(self, selected: str):
        previous = self.output_choice.blockSignals(True)
        self.output_choice.setCurrentIndex(self.output_choice.findData(selected))
        self.output_choice.blockSignals(previous)

    def sync_theme(self, selected: str):
        previous = self.theme_choice.blockSignals(True)
        self.theme_choice.setCurrentIndex(self.theme_choice.findData(selected))
        self.theme_choice.blockSignals(previous)

    def set_status(self, status: str, message: str, color: str):
        self.status.setText(f"●  {status}")
        self.status.setToolTip(message)
        self.status.setStyleSheet(f"color:{color}; font-size:12px; font-weight:600;")

    def set_theme(self, mode: str):
        dark = mode == "dark"
        self.logo.setPixmap(brand_icon(mode).pixmap(27, 27))
        surface = "#202b3a" if dark else "#ffffff"
        border = "#3c4c63" if dark else "#dde4ee"
        main = "#edf2fc" if dark else "#263448"
        muted = "#a5b3c8" if dark else "#78869a"
        hover = "#2e415a" if dark else "#f0f5fc"
        active = "#304866" if dark else "#eaf2ff"
        accent = "#a7c6ff" if dark else "#326bc6"
        self.setStyleSheet(
            f"QFrame#traySurface {{background:{surface}; border:1px solid {border}; border-radius:18px;}}"
            f"QLabel#trayName {{color:{main}; font-size:15px; font-weight:600;}}"
            f"QLabel#traySection {{color:{muted}; font-size:11px; font-weight:600;}}"
            f"QFrame#trayDivider {{border:0; background:{border}; max-height:1px; min-height:1px;}}"
            "QScrollArea#trayModeScroll {background:transparent; border:none;}"
            "QWidget#trayModeHost {background:transparent;}"
            f"QPushButton#trayMode {{background:transparent; color:{main}; text-align:left;"
            "border:1px solid transparent; border-radius:9px; font-size:13px; min-height:0px; padding:8px 10px;}"
            f"QPushButton#trayMode:hover {{background:{hover};}}"
            f"QPushButton#trayMode:checked {{background:{active}; color:{accent}; font-weight:600;}}"
            f"QPushButton#trayAction {{background:{hover}; color:{main}; border:1px solid {border};"
            "border-radius:9px; padding:9px 5px; min-height:0px; font-size:12px;}"
            f"QPushButton#trayAction:hover {{background:{active}; color:{accent};}}"
            f"QPushButton#trayExit {{background:transparent; color:{muted}; border:0;"
            "border-radius:9px; padding:6px; min-height:0px; font-size:12px;}"
            f"QPushButton#trayExit:hover {{background:{hover}; color:{main};}}"
        )
        self.sync_theme(mode)

    def show_at_cursor(self):
        self.adjustSize()
        cursor = QCursor.pos()
        available = QApplication.desktop().availableGeometry(cursor)
        x = min(max(cursor.x() - self.width() + 18, available.left()), available.right() - self.width() + 1)
        y = cursor.y() - self.height() - 8
        if y < available.top():
            y = min(cursor.y() + 18, available.bottom() - self.height() + 1)
        self.move(max(x, available.left()), max(y, available.top()))
        self.show()
        self.raise_()

    def _choose_mode(self, mode_id: str):
        self.hide()
        self.owner._activate_mode(mode_id)

    def _open_main(self):
        self.hide()
        self.owner._show_window()

    def _pause(self):
        self.hide()
        self.owner._toggle_pause()

    def _exit(self):
        self.hide()
        self.owner._shutdown()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Translator")
        self.resize(1080, 780)
        self.setMinimumSize(900, 620)
        self.setWindowIcon(brand_icon())
        self.paused = False
        self.busy = False
        self.worker_available = False
        self.exiting = False
        self.hidden_notice_sent = False
        self.today_count = 0
        self.failed_count = 0
        self.history = []
        self.listener: HotkeyListener | None = None
        self.registered = {"auto": False}
        self.mode_dirty = False
        self._changing_modes = False
        self._selected_mode_row = -1
        self.configuration_valid = False
        self.initial_config_error = ""
        try:
            self.config = read_config()
        except ValueError as exc:
            self.config = dict(DEFAULTS)
            self.initial_config_error = str(exc)

        self._build_ui()
        self._build_tray()
        self.result_overlay = FloatingResult()
        self._fill_settings()
        self._refresh_mode_widgets()
        self._apply_theme(self.config.get("theme", "light"))
        self._set_status("idle", "正在启动热键监听…")

        self.worker = TranslationWorker()
        self.worker.signals.ready.connect(self._worker_ready)
        self.worker.signals.phase.connect(self._phase)
        self.worker.signals.done.connect(self._done)
        self.worker.start()
        self._restart_hotkeys()

        if self.initial_config_error:
            self._set_status("error", self.initial_config_error)
            self._select_page(3)
        else:
            try:
                load_settings()
                self.configuration_valid = True
            except TranslationError as exc:
                self._set_status("warning", str(exc))
                self._select_page(3)

    def _apply_theme(self, mode: str):
        self.theme = "dark" if mode == "dark" else "light"
        app = QApplication.instance()
        app.setProperty("ui_theme", self.theme)
        palette = QPalette()
        if self.theme == "dark":
            palette.setColor(QPalette.Window, QColor("#10151f"))
            palette.setColor(QPalette.Base, QColor("#192333"))
            palette.setColor(QPalette.Text, QColor("#e7ecf5"))
            palette.setColor(QPalette.WindowText, QColor("#e7ecf5"))
            palette.setColor(QPalette.ButtonText, QColor("#e7ecf5"))
            palette.setColor(QPalette.Highlight, QColor("#3e639d"))
        else:
            palette.setColor(QPalette.Window, QColor("#f8fafc"))
            palette.setColor(QPalette.Base, QColor("#ffffff"))
            palette.setColor(QPalette.Text, QColor("#202124"))
            palette.setColor(QPalette.WindowText, QColor("#202124"))
            palette.setColor(QPalette.ButtonText, QColor("#202124"))
            palette.setColor(QPalette.Highlight, QColor("#c9ddff"))
        app.setPalette(palette)
        app.setStyleSheet(theme_stylesheet(self.theme))
        self.setWindowIcon(brand_icon(self.theme))
        self.brand_logo.setPixmap(brand_icon(self.theme).pixmap(30, 30))
        self._sync_native_titlebar()
        self.side_auto.setStyleSheet(
            "font-weight:600; color:#dbe4f2;" if self.theme == "dark"
            else "font-weight:600; color:#344054;"
        )
        self.side_mode.setStyleSheet(
            "color:#a1afc3; font-size:12px;" if self.theme == "dark"
            else "color:#7b8494; font-size:12px;"
        )
        for selector in self.findChildren(SimpleSelect):
            selector.update()
        self.theme_toggle.setIcon(theme_icon("dark" if self.theme == "light" else "light"))
        self.theme_toggle.setToolTip("切换到深色模式" if self.theme == "light" else "切换到浅色模式")
        if hasattr(self, "tray_popup"):
            self.tray_popup.set_theme(self.theme)
        self.result_overlay.set_theme(self.theme)
        if hasattr(self, "_status_tone"):
            self._set_status(self._status_tone, self._status_message)

    def _sync_native_titlebar(self):
        set_native_titlebar_theme(int(self.winId()), self.theme)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._sync_native_titlebar)

    def _theme_changed(self, index: int):
        if index < 0:
            return
        selected = self.theme_field.itemData(index)
        self._apply_theme(selected)
        try:
            self.config = save_config({"theme": selected}, validate_api=False)
        except ValueError as exc:
            QMessageBox.warning(self, "主题未保存", str(exc))

    def _toggle_theme(self):
        next_theme = "dark" if self.theme == "light" else "light"
        self.theme_field.setCurrentIndex(self.theme_field.findData(next_theme))

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(204)
        layout.addWidget(sidebar)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(17, 25, 17, 23)
        sl.setSpacing(9)

        logo_line = QHBoxLayout()
        logo_line.setSpacing(7)
        self.brand_logo = QLabel()
        self.brand_logo.setFixedSize(30, 30)
        self.brand_logo.setAlignment(Qt.AlignCenter)
        self.brand_logo.setPixmap(self.windowIcon().pixmap(30, 30))
        logo_line.addWidget(self.brand_logo)
        logo_line.addWidget(text_label("LLM Translator", "brand"))
        logo_line.addStretch(1)
        sl.addLayout(logo_line)
        sl.addSpacing(32)

        self.nav_buttons = []
        self.nav_keys = ("overview", "manual", "modes", "settings")
        for label, key, index in (("概览", "overview", 0), ("翻译", "manual", 1),
                                  ("Prompt", "modes", 2), ("设置", "settings", 3)):
            button = QPushButton(label)
            button.setObjectName("nav")
            button.setIcon(nav_icon(key))
            button.setIconSize(QSize(20, 20))
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=index: self._select_page(idx))
            sl.addWidget(button)
            self.nav_buttons.append(button)

        sl.addStretch(1)
        sl.addWidget(text_label("快捷键", "eyebrow"))
        self.side_auto = text_label("Ctrl + Shift + X")
        self.side_auto.setStyleSheet("font-weight:600; color:#344054;")
        sl.addWidget(self.side_auto)
        self.side_mode = text_label("中英互译")
        self.side_mode.setStyleSheet("color:#7b8494; font-size:12px;")
        sl.addWidget(self.side_mode)

        right = QWidget()
        layout.addWidget(right, 1)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(30, 24, 30, 25)
        right_layout.setSpacing(16)
        bar = QHBoxLayout()
        self.top_status = text_label("●  启动中", "statusText")
        self.top_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.top_status.setWordWrap(False)
        bar.addWidget(self.top_status)
        bar.addStretch(1)
        self.theme_toggle = QPushButton()
        self.theme_toggle.setObjectName("themeToggle")
        self.theme_toggle.setFixedSize(38, 38)
        self.theme_toggle.setIconSize(QSize(20, 20))
        self.theme_toggle.clicked.connect(self._toggle_theme)
        bar.addWidget(self.theme_toggle)
        right_layout.addLayout(bar)
        self.pages = QStackedWidget()
        right_layout.addWidget(self.pages, 1)
        self._build_dashboard()
        self._build_manual()
        self._build_mode_editor()
        self._build_settings()
        self._select_page(0)

    def _build_dashboard(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        scroll.setWidget(page)
        self.pages.addWidget(scroll)
        vl = QVBoxLayout(page)
        vl.setContentsMargins(0, 1, 8, 0)
        vl.setSpacing(16)

        title_bar = QHBoxLayout()
        title_bar.addWidget(text_label("概览", "pageTitle"))
        title_bar.addStretch(1)
        self.session_summary = text_label("本次会话 · 0 条", "muted")
        title_bar.addWidget(self.session_summary)
        vl.addLayout(title_bar)

        _, controls = make_card(vl, padding=21)
        controls_row = QHBoxLayout()
        controls_row.setSpacing(12)
        prompt_col = QVBoxLayout()
        prompt_col.setSpacing(7)
        prompt_col.addWidget(text_label("Prompt", "fieldLabel"))
        self.active_mode_combo = SimpleSelect()
        self.active_mode_combo.currentIndexChanged.connect(self._mode_combo_changed)
        prompt_col.addWidget(self.active_mode_combo)
        controls_row.addLayout(prompt_col, 1)

        output_col = QVBoxLayout()
        output_col.setSpacing(7)
        output_col.addWidget(text_label("输出", "fieldLabel"))
        self.output_quick = SegmentedChoice()
        self.output_quick.addItem("替换", "replace")
        self.output_quick.addItem("悬浮", "float")
        self.output_quick.currentIndexChanged.connect(self._quick_output_changed)
        output_col.addWidget(self.output_quick)
        controls_row.addLayout(output_col, 1)
        controls.addLayout(controls_row)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        self.hint_auto = text_label("选中文字 · Ctrl+Shift+X", "muted")
        status_row.addWidget(self.hint_auto, 1)
        self.pause_button = QPushButton("暂停")
        self.pause_button.clicked.connect(self._toggle_pause)
        status_row.addWidget(self.pause_button)
        controls.addLayout(status_row)
        self.hero_stage = text_label("等待操作", "muted")
        controls.addWidget(self.hero_stage)

        history_header = QHBoxLayout()
        history_header.addWidget(text_label("最近记录", "sectionTitle"))
        history_header.addStretch(1)
        clear = QPushButton("清空")
        clear.clicked.connect(self._clear_history)
        history_header.addWidget(clear)
        vl.addLayout(history_header)

        body = QHBoxLayout()
        body.setSpacing(14)
        history_card, history_layout = make_card(body, padding=12)
        history_card.setFixedWidth(232)
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(280)
        self.history_list.currentRowChanged.connect(self._show_history)
        history_layout.addWidget(self.history_list, 1)

        detail = QVBoxLayout()
        detail.setSpacing(14)
        _, source_layout = make_card(detail, padding=17)
        source_layout.addWidget(text_label("原文", "fieldLabel"))
        self.history_source = QPlainTextEdit()
        self.history_source.setReadOnly(True)
        self.history_source.setPlaceholderText("选择一条记录查看原文")
        self.history_source.setMinimumHeight(118)
        source_layout.addWidget(self.history_source, 1)

        _, result_layout = make_card(detail, padding=17)
        result_layout.addWidget(text_label("处理结果", "fieldLabel"))
        self.history_target = QPlainTextEdit()
        self.history_target.setObjectName("resultBox")
        self.history_target.setReadOnly(True)
        self.history_target.setPlaceholderText("选择一条记录查看结果")
        result_layout.addWidget(self.history_target, 1)
        body.addLayout(detail, 1)
        vl.addLayout(body, 1)

    def _build_manual(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        scroll.setWidget(page)
        self.pages.addWidget(scroll)
        vl = QVBoxLayout(page)
        vl.setContentsMargins(0, 4, 8, 10)
        vl.setSpacing(16)
        vl.setSizeConstraint(QLayout.SetMinimumSize)
        vl.addWidget(text_label("翻译", "pageTitle"))
        vl.addWidget(text_label("输入文本并执行当前 Prompt。", "muted", wrap=True))

        input_card, input_layout = make_card(vl, padding=20)
        header = QHBoxLayout()
        header.addWidget(text_label("输入", "sectionTitle"))
        header.addStretch(1)
        self.manual_mode_label = text_label("中英互译", "modeTag")
        self.manual_mode_label.setWordWrap(False)
        self.manual_mode_label.setFixedSize(146, 34)
        self.manual_mode_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.manual_mode_label)
        self.run_button = QPushButton("执行")
        self.run_button.setObjectName("primary")
        self.run_button.clicked.connect(self._manual_run)
        header.addWidget(self.run_button)
        input_layout.addLayout(header)
        self.source_preview = QPlainTextEdit()
        self.source_preview.setPlaceholderText("在此输入需要处理的文本…")
        self.source_preview.setMinimumHeight(88)
        input_layout.addWidget(self.source_preview, 1)

        result_card, result_layout = make_card(vl, padding=20)
        result_header = QHBoxLayout()
        result_header.addWidget(text_label("结果", "sectionTitle"))
        result_header.addStretch(1)
        self.copy_manual_button = QPushButton("复制结果")
        self.copy_manual_button.setEnabled(False)
        self.copy_manual_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.target_preview.toPlainText())
        )
        result_header.addWidget(self.copy_manual_button)
        result_layout.addLayout(result_header)
        self.target_preview = QPlainTextEdit()
        self.target_preview.setObjectName("resultBox")
        self.target_preview.setReadOnly(True)
        self.target_preview.setMinimumHeight(88)
        self.target_preview.setPlaceholderText("处理结果将在这里显示")
        result_layout.addWidget(self.target_preview, 1)
        vl.setStretch(vl.indexOf(input_card), 1)
        vl.setStretch(vl.indexOf(result_card), 1)

    def _build_mode_editor(self):
        page = QWidget()
        self.pages.addWidget(page)
        vl = QVBoxLayout(page)
        vl.setContentsMargins(0, 4, 0, 10)
        vl.setSpacing(15)
        vl.addWidget(text_label("Prompt", "pageTitle"))
        vl.addWidget(text_label("选择或编辑文字处理规则。", "muted", wrap=True))

        body = QHBoxLayout()
        body.setSpacing(15)
        left, ll = make_card(body)
        left.setFixedWidth(224)
        ll.addWidget(text_label("模式", "sectionTitle"))
        self.mode_list = QListWidget()
        self.mode_list.currentRowChanged.connect(self._mode_editor_selected)
        ll.addWidget(self.mode_list, 1)
        add = QPushButton("＋ 新建模式")
        add.clicked.connect(self._add_mode)
        ll.addWidget(add)
        duplicate = QPushButton("复制模式")
        duplicate.clicked.connect(self._duplicate_mode)
        ll.addWidget(duplicate)
        delete = QPushButton("删除模式")
        delete.clicked.connect(self._delete_mode)
        ll.addWidget(delete)

        right, rl = make_card(body)
        rl.addWidget(text_label("编辑", "sectionTitle"))
        rl.addWidget(text_label("名称", "fieldLabel"))
        self.mode_name_field = QLineEdit()
        self.mode_name_field.setPlaceholderText("例如：微生物论文润色")
        self.mode_name_field.textChanged.connect(self._mark_mode_dirty)
        rl.addWidget(self.mode_name_field)
        rl.addWidget(text_label("系统 Prompt", "fieldLabel"))
        self.mode_prompt_field = QPlainTextEdit()
        self.mode_prompt_field.setPlaceholderText("描述你希望如何处理文本，例如翻译、学术润色或专业改写。")
        self.mode_prompt_field.textChanged.connect(self._mark_mode_dirty)
        rl.addWidget(self.mode_prompt_field, 1)
        rl.addWidget(text_label("原文会单独作为 user 消息发送，无需在 Prompt 中插入 {text}。", "muted", wrap=True))
        action_row = QHBoxLayout()
        self.mode_edit_status = text_label("")
        action_row.addWidget(self.mode_edit_status, 1)
        self.activate_mode_button = QPushButton("设为当前模式")
        self.activate_mode_button.clicked.connect(self._activate_editor_mode)
        action_row.addWidget(self.activate_mode_button)
        save = QPushButton("保存 Prompt")
        save.setObjectName("primary")
        save.clicked.connect(self._save_mode)
        action_row.addWidget(save)
        rl.addLayout(action_row)
        vl.addLayout(body, 1)

    def _mark_mode_dirty(self):
        if not self._changing_modes:
            self.mode_dirty = True
            self.mode_edit_status.setText("●  尚未保存")
            self.mode_edit_status.setStyleSheet("color:#b27621;")

    def _confirm_discard_mode(self) -> bool:
        if not self.mode_dirty:
            return True
        return QMessageBox.question(
            self, "尚未保存", "当前 Prompt 有未保存的修改，确定放弃修改吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) == QMessageBox.Yes

    def _mode_editor_selected(self, row: int):
        if self._changing_modes or row < 0 or row >= len(self.config["modes"]):
            return
        if row != self._selected_mode_row and not self._confirm_discard_mode():
            self._changing_modes = True
            self.mode_list.setCurrentRow(self._selected_mode_row)
            self._changing_modes = False
            return
        self._changing_modes = True
        mode = self.config["modes"][row]
        self._selected_mode_row = row
        self.mode_name_field.setText(mode["name"])
        self.mode_prompt_field.setPlainText(mode["prompt"])
        self.mode_dirty = False
        self.mode_edit_status.setText("当前使用" if mode["id"] == self.config["active_mode_id"] else "可设为当前")
        self.mode_edit_status.setStyleSheet("color:#23835b;" if mode["id"] == self.config["active_mode_id"] else "color:#7b8494;")
        self._changing_modes = False

    def _persist_modes(self, values: dict, selected_id: str | None = None) -> bool:
        try:
            self.config = save_config(values, validate_api=False)
        except ValueError as exc:
            QMessageBox.warning(self, "无法保存模式", str(exc))
            return False
        self.mode_dirty = False
        self._refresh_mode_widgets(selected_id)
        return True

    def _save_mode(self):
        row = self._selected_mode_row
        if row < 0:
            return
        modes = deepcopy(self.config["modes"])
        modes[row]["name"] = self.mode_name_field.text().strip()
        modes[row]["prompt"] = self.mode_prompt_field.toPlainText().strip()
        if self._persist_modes({"modes": modes}, modes[row]["id"]):
            self.mode_edit_status.setText("✓  已保存")
            self.mode_edit_status.setStyleSheet("color:#23835b;")

    def _add_mode(self):
        if not self._confirm_discard_mode():
            return
        mode = new_mode()
        modes = deepcopy(self.config["modes"]) + [mode]
        self._persist_modes({"modes": modes}, mode["id"])

    def _duplicate_mode(self):
        if self._selected_mode_row < 0 or not self._confirm_discard_mode():
            return
        mode = {**new_mode(), **deepcopy(self.config["modes"][self._selected_mode_row])}
        mode["id"] = new_mode()["id"]
        mode["name"] += "（副本）"
        modes = deepcopy(self.config["modes"]) + [mode]
        self._persist_modes({"modes": modes}, mode["id"])

    def _delete_mode(self):
        if self._selected_mode_row < 0 or not self._confirm_discard_mode():
            return
        modes = deepcopy(self.config["modes"])
        if len(modes) <= 1:
            QMessageBox.information(self, "无法删除", "至少需要保留一个模式。")
            return
        name = modes[self._selected_mode_row]["name"]
        if QMessageBox.question(self, "删除模式", f"确定删除「{name}」吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        deleted = modes.pop(self._selected_mode_row)
        active = self.config["active_mode_id"]
        if active == deleted["id"]:
            active = modes[0]["id"]
        self._persist_modes({"modes": modes, "active_mode_id": active}, active)

    def _activate_editor_mode(self):
        if self._selected_mode_row < 0:
            return
        if self.mode_dirty:
            QMessageBox.information(self, "请先保存", "先保存修改过的 Prompt，再切换到此模式。")
            return
        self._activate_mode(self.config["modes"][self._selected_mode_row]["id"])

    def _mode_combo_changed(self, index: int):
        if not self._changing_modes and index >= 0:
            chosen = self.active_mode_combo.itemData(index)
            if chosen and chosen != self.config["active_mode_id"]:
                self._activate_mode(chosen)

    def _activate_mode(self, mode_id: str):
        if mode_id == self.config["active_mode_id"]:
            return
        if not self._confirm_discard_mode():
            self._changing_modes = True
            self.active_mode_combo.setCurrentIndex(self.active_mode_combo.findData(self.config["active_mode_id"]))
            self.tray_popup.sync_mode(self.config["active_mode_id"])
            self._changing_modes = False
            return
        if self._persist_modes({"active_mode_id": mode_id}, self.config["modes"][max(self._selected_mode_row, 0)]["id"]):
            tone = "muted" if self.paused else "busy" if self.busy else "idle"
            self._set_status(tone, f"{'已暂停 · ' if self.paused else ''}已切换模式：{current_mode(self.config)['name']}")

    def _refresh_mode_widgets(self, selected_id: str | None = None):
        self._changing_modes = True
        self.active_mode_combo.clear()
        self.mode_list.clear()
        selected_row = 0
        for idx, mode in enumerate(self.config["modes"]):
            self.active_mode_combo.addItem(mode["name"], mode["id"])
            self.mode_list.addItem(("●  " if mode["id"] == self.config["active_mode_id"] else "     ") + mode["name"])
            if mode["id"] == (selected_id or self.config["active_mode_id"]):
                selected_row = idx
        index = self.active_mode_combo.findData(self.config["active_mode_id"])
        self.active_mode_combo.setCurrentIndex(max(0, index))
        self.mode_list.setCurrentRow(selected_row)
        self._selected_mode_row = -1
        self._changing_modes = False
        self._mode_editor_selected(selected_row)
        mode_name = current_mode(self.config)["name"]
        self.side_mode.setText(self.side_mode.fontMetrics().elidedText(mode_name, Qt.ElideRight, 165))
        self.side_mode.setToolTip(mode_name)
        self.manual_mode_label.setText(
            self.manual_mode_label.fontMetrics().elidedText(mode_name, Qt.ElideRight, 118)
        )
        self.manual_mode_label.setToolTip(f"当前 Prompt · {mode_name}")
        if hasattr(self, "tray_popup"):
            self.tray_popup.sync_modes(self.config["modes"], self.config["active_mode_id"])

    def _build_settings(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        scroll.setWidget(widget)
        self.pages.addWidget(scroll)
        vl = QVBoxLayout(widget)
        vl.setContentsMargins(0, 4, 8, 8)
        vl.setSpacing(18)
        vl.addWidget(text_label("设置", "pageTitle"))

        _, appearance = make_card(vl)
        appearance.addWidget(text_label("外观", "sectionTitle"))
        theme_row = QHBoxLayout()
        theme_row.addWidget(text_label("界面主题", "fieldLabel"))
        theme_row.addStretch(1)
        self.theme_field = SegmentedChoice()
        self.theme_field.setMinimumWidth(190)
        self.theme_field.addItem("浅色", "light")
        self.theme_field.addItem("深色", "dark")
        self.theme_field.currentIndexChanged.connect(self._theme_changed)
        theme_row.addWidget(self.theme_field)
        appearance.addLayout(theme_row)

        _, api = make_card(vl)
        api.addWidget(text_label("API", "sectionTitle"))
        api.addWidget(text_label("兼容 Chat Completions 接口", "muted"))
        api.addWidget(text_label("API Key", "fieldLabel"))
        secret_row = QHBoxLayout()
        self.key_field = QLineEdit()
        self.key_field.setEchoMode(QLineEdit.Password)
        self.key_field.setPlaceholderText("输入新 API Key；留空保持已保存的密钥")
        secret_row.addWidget(self.key_field, 1)
        self.reveal_btn = QPushButton("显示")
        self.reveal_btn.setFixedWidth(70)
        self.reveal_btn.clicked.connect(self._toggle_key_visibility)
        secret_row.addWidget(self.reveal_btn)
        api.addLayout(secret_row)
        api.addWidget(text_label("密钥保存在 Windows 凭据管理器中。留空则不修改。", "muted", wrap=True))
        api.addWidget(text_label("Base URL", "fieldLabel"))
        self.base_field = QLineEdit()
        self.base_field.setPlaceholderText("https://api.openai.com/v1")
        api.addWidget(self.base_field)
        api.addWidget(text_label("模型", "fieldLabel"))
        self.model_field = QLineEdit()
        self.model_field.setPlaceholderText("gpt-4o-mini")
        api.addWidget(self.model_field)

        _, processing = make_card(vl)
        processing.addWidget(text_label("输出", "sectionTitle"))
        processing.addWidget(text_label("翻译方向与风格由 Prompt 决定。", "muted"))
        processing_grid = QGridLayout()
        processing_grid.setHorizontalSpacing(24)
        processing_grid.setVerticalSpacing(15)
        processing_grid.addWidget(text_label("结果呈现", "fieldLabel"), 0, 0)
        self.output_field = SegmentedChoice()
        self.output_field.addItem("替换选中文字", "replace")
        self.output_field.addItem("悬浮显示结果（保留原文）", "float")
        processing_grid.addWidget(self.output_field, 0, 1)
        processing_grid.addWidget(text_label("写回方式", "fieldLabel"), 1, 0)
        self.replace_field = SegmentedChoice()
        self.replace_field.addItem("粘贴", "paste")
        self.replace_field.addItem("模拟输入", "type")
        self.replace_field.setToolTip("粘贴使用 Ctrl+V；模拟输入使用 Unicode 逐字输入")
        processing_grid.addWidget(self.replace_field, 1, 1)
        processing_grid.addWidget(text_label("请求超时", "fieldLabel"), 2, 0)
        self.timeout_field = QSpinBox()
        self.timeout_field.setRange(1, 120)
        self.timeout_field.setSuffix(" 秒")
        self.timeout_field.setButtonSymbols(QAbstractSpinBox.NoButtons)
        processing_grid.addWidget(self.timeout_field, 2, 1)
        processing_grid.addWidget(text_label("文本长度上限", "fieldLabel"), 3, 0)
        self.max_chars_field = QSpinBox()
        self.max_chars_field.setRange(1, 100000)
        self.max_chars_field.setSingleStep(1000)
        self.max_chars_field.setSuffix(" 字符")
        self.max_chars_field.setButtonSymbols(QAbstractSpinBox.NoButtons)
        processing_grid.addWidget(self.max_chars_field, 3, 1)
        processing_grid.setColumnMinimumWidth(0, 112)
        processing_grid.setColumnStretch(1, 1)
        processing.addLayout(processing_grid)

        _, shortcuts = make_card(vl)
        shortcuts.addWidget(text_label("快捷键", "sectionTitle"))
        shortcuts.addWidget(text_label("支持 Ctrl、Alt、Shift、Win 与字母、数字、F1–F12 组合。", "muted", wrap=True))
        shortcuts.addWidget(text_label("处理所选文字", "fieldLabel"))
        self.auto_field = QLineEdit()
        self.auto_field.setPlaceholderText("Ctrl+Shift+X")
        shortcuts.addWidget(self.auto_field)
        self.minimized_field = QCheckBox("启动时隐藏到托盘")
        shortcuts.addWidget(self.minimized_field)
        self.notify_field = QCheckBox("完成或失败时通知")
        shortcuts.addWidget(self.notify_field)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.save_status = text_label("")
        bottom.addWidget(self.save_status)
        self.save_button = QPushButton("保存设置")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self._save_settings)
        bottom.addWidget(self.save_button)
        vl.addLayout(bottom)
        vl.addStretch(1)

    def _build_tray(self):
        self.tray = QSystemTrayIcon(tray_icon(COLORS["idle"]), self)
        self.tray.setToolTip("LLM Translator · 就绪")
        self.tray_popup = TrayPopup(self)
        self.tray.activated.connect(self._tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.Context:
            # Defer opening until Windows has finished delivering the right-click.
            QTimer.singleShot(60, self.tray_popup.show_at_cursor)
        elif reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.tray_popup.hide()
            self._show_window()

    def _select_page(self, index: int):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            btn.setIcon(nav_icon(self.nav_keys[i], active=i == index))

    def _fill_settings(self):
        cfg = self.config
        previous = self.theme_field.blockSignals(True)
        self.theme_field.setCurrentIndex(max(0, self.theme_field.findData(cfg.get("theme", "light"))))
        self.theme_field.blockSignals(previous)
        # Never pre-fill or persist the actual API Key in UI configuration.
        self.key_field.clear()
        try:
            if get_saved_api_key():
                self.key_field.setPlaceholderText("密钥已保存在 Windows 凭据管理器 · 留空保持不变")
        except SecretStorageError:
            self.key_field.setPlaceholderText("需要 Windows 凭据管理器 · 输入新 API Key")
        self.base_field.setText(str(cfg.get("base_url", "")))
        self.model_field.setText(str(cfg.get("model", "")))
        idx = self.replace_field.findData(cfg.get("replace_method", "paste"))
        self.replace_field.setCurrentIndex(max(0, idx))
        self._sync_output_widgets()
        try:
            self.timeout_field.setValue(int(cfg.get("timeout_seconds", 30)))
            self.max_chars_field.setValue(int(cfg.get("max_source_chars", 10000)))
        except (TypeError, ValueError):
            self.timeout_field.setValue(30)
            self.max_chars_field.setValue(10000)
        self.auto_field.setText(str(cfg.get("hotkey_auto", DEFAULTS["hotkey_auto"])))
        self.minimized_field.setChecked(bool(cfg.get("start_minimized", False)))
        self.notify_field.setChecked(bool(cfg.get("notify_on_finish", True)))
        self._update_shortcut_labels()

    def _update_shortcut_labels(self):
        automatic = self.config["hotkey_auto"]
        self.side_auto.setText(automatic)
        destination = "悬浮显示" if self.config.get("output_mode") == "float" else "原位替换"
        self.hint_auto.setText(f"选中文本 · {automatic} · {destination}")

    def _sync_output_widgets(self):
        selected = self.config.get("output_mode", "replace")
        for combo in (self.output_quick, self.output_field):
            previous = combo.blockSignals(True)
            combo.setCurrentIndex(max(0, combo.findData(selected)))
            combo.blockSignals(previous)
        self.tray_popup.sync_output(selected)
        self._update_shortcut_labels()

    def _quick_output_changed(self, index: int):
        if index >= 0:
            self._set_output_mode(self.output_quick.itemData(index))

    def _set_output_mode(self, selected: str):
        if selected == self.config.get("output_mode"):
            return
        try:
            self.config = save_config({"output_mode": selected}, validate_api=False)
        except ValueError as exc:
            QMessageBox.warning(self, "无法切换输出方式", str(exc))
        self._sync_output_widgets()

    def _toggle_key_visibility(self):
        visible = self.key_field.echoMode() == QLineEdit.Password
        self.key_field.setEchoMode(QLineEdit.Normal if visible else QLineEdit.Password)
        self.reveal_btn.setText("隐藏" if visible else "显示")

    def _save_settings(self):
        values = {
            "theme": self.theme_field.currentData(),
            "api_key": self.key_field.text().strip(),
            "base_url": self.base_field.text().strip(),
            "model": self.model_field.text().strip(),
            "replace_method": self.replace_field.currentData(),
            "output_mode": self.output_field.currentData(),
            "timeout_seconds": self.timeout_field.value(),
            "max_source_chars": self.max_chars_field.value(),
            "hotkey_auto": self.auto_field.text().strip(),
            "start_minimized": self.minimized_field.isChecked(),
            "notify_on_finish": self.notify_field.isChecked(),
        }
        try:
            self.config = save_config(values)
        except ValueError as exc:
            self.save_status.setText("设置有误")
            self.save_status.setStyleSheet("color:#c3484c;")
            QMessageBox.warning(self, "无法保存设置", str(exc))
            return
        self._update_shortcut_labels()
        self._sync_output_widgets()
        self.key_field.clear()
        self.key_field.setPlaceholderText("密钥已保存在 Windows 凭据管理器 · 留空保持不变")
        self.configuration_valid = True
        self._restart_hotkeys()
        self.save_status.setText("已保存")
        self.save_status.setStyleSheet("color:#23835b;")
        if not self.busy:
            self._set_status("muted" if self.paused else "idle", "设置已保存 · " + ("已暂停" if self.paused else "等待快捷键"))

    def _restart_hotkeys(self):
        if self.listener is not None:
            self.listener.stop()
            if not self.listener.wait(1800):
                self._set_status("error", "旧热键监听未停止，无法安全重新注册")
                return
            self.listener = None
        try:
            automatic = parse_hotkey(self.config["hotkey_auto"])
        except ValueError as exc:
            self._set_status("error", str(exc))
            return
        self.combo_spec = automatic
        self.listener = HotkeyListener(automatic)
        self.listener.pressed.connect(self._hotkey)
        self.listener.registered.connect(self._registered)
        self.listener.start()

    def _registered(self, result: dict):
        self.registered = {"auto": bool(result.get("auto"))}
        num = int(self.registered["auto"])
        if result.get("error"):
            self._set_status("error", str(result["error"]))
        elif not num:
            self._set_status("error", "快捷键被占用；可去设置中修改")
        elif not self.configuration_valid:
            self._set_status("warning", "请先在设置中填写有效的 API 配置")
        elif not self.busy and not self.paused:
            self._set_status("idle", "监听已开启 · 等待快捷键")

    def _worker_ready(self, okay: bool, message: str):
        self.worker_available = okay
        if not okay:
            self._set_status("error", message)

    def _hotkey(self):
        if self.exiting or self.paused:
            return
        if self.isActiveWindow():
            self._set_status("warning", "主界面正在使用中；请切回需要翻译的程序")
            return
        if self.busy:
            self.hero_stage.setText("◉  正在处理上一条请求 · 本次按键未执行")
            return
        if not self.worker_available:
            self._set_status("error", "后台组件尚未就绪，请稍候")
            return
        self.busy = True
        profile = current_mode(self.config)
        self._set_status("busy", f"{profile['name']} · 正在读取文本…")
        if not self.worker.submit(
            self.combo_spec.release_keys, profile["name"], profile["prompt"],
            self.config.get("output_mode", "replace"),
        ):
            self.busy = False
            self._set_status("warning", "已有任务正在等待执行")

    def _manual_run(self):
        source = self.source_preview.toPlainText()
        if not source.strip():
            self.source_preview.setFocus()
            self._set_status("warning", "请先输入文本")
            return
        if self.busy:
            self._set_status("warning", "请等待当前任务完成")
            return
        if not self.worker_available:
            self._set_status("error", "后台组件尚未就绪")
            return
        profile = current_mode(self.config)
        self.busy = True
        self.run_button.setEnabled(False)
        self.run_button.setText("执行中…")
        self.source_preview.setReadOnly(True)
        self.target_preview.clear()
        self.copy_manual_button.setEnabled(False)
        self._set_status("busy", f"{profile['name']} · 正在处理文本…")
        if not self.worker.submit_text(source, profile["name"], profile["prompt"]):
            self.busy = False
            self.run_button.setEnabled(True)
            self.run_button.setText("执行")
            self.source_preview.setReadOnly(False)
            self._set_status("warning", "已有任务正在等待执行")

    def _phase(self, stage: str, message: str):
        if self.exiting:
            return
        self._set_status("busy", message)

    def _done(self, item: dict):
        if self.exiting:
            return
        self.busy = False
        self.run_button.setEnabled(True)
        self.run_button.setText("执行")
        self.source_preview.setReadOnly(False)
        if item.get("output_mode") == "manual":
            self.target_preview.setPlainText(item.get("target", "") if item["ok"] else item["message"])
            self.copy_manual_button.setEnabled(bool(self.target_preview.toPlainText()))
        self.history.insert(0, item)
        self.history = self.history[:60]
        when = datetime.fromtimestamp(item["time"]).strftime("%H:%M:%S")
        kind = item["mode"]
        status = "✓" if item["ok"] else "✕"
        row_item = QListWidgetItem(f"{status}  {when} · {kind}")
        row_item.setToolTip(item["message"])
        self.history_list.insertItem(0, row_item)
        while self.history_list.count() > 60:
            self.history_list.takeItem(60)
        self.history_list.setCurrentRow(0)
        if item["ok"]:
            if item.get("output_mode") == "float" and item.get("target"):
                self.result_overlay.show_result(item["target"], kind)
            self.today_count += 1
            self._set_status("muted" if self.paused else "success", "已暂停 · " + item["message"] if self.paused else item["message"])
        else:
            self.failed_count += 1
            self._set_status("muted" if self.paused else "error", "已暂停 · " + item["message"] if self.paused else item["message"])
        self.session_summary.setText(f"成功 {self.today_count} · 失败 {self.failed_count}")
        if self.tray.isVisible() and not self.isVisible() and self.config.get("notify_on_finish", True):
            self.tray.showMessage(
                "LLM Translator · " + ("处理成功" if item["ok"] else "处理失败"),
                f"{kind}：{item['message']}",
                QSystemTrayIcon.Information if item["ok"] else QSystemTrayIcon.Warning,
                4500,
            )

    def _show_history(self, row: int):
        if 0 <= row < len(self.history):
            item = self.history[row]
            self.history_source.setPlainText(item.get("source", ""))
            self.history_target.setPlainText(item.get("target", "") if item["ok"] else item["message"])
        else:
            self.history_source.clear()
            self.history_target.clear()

    def _clear_history(self):
        self.history.clear()
        self.history_list.clear()
        self._show_history(-1)
        self.today_count = 0
        self.failed_count = 0
        self.session_summary.setText("本次会话 · 0 条")

    def _set_status(self, tone: str, message: str):
        self._status_tone, self._status_message = tone, message
        palette = DARK_COLORS if getattr(self, "theme", "light") == "dark" else COLORS
        color = palette.get(tone, palette["idle"])
        short_status = {
            "idle": "就绪", "busy": "处理中", "success": "已完成",
            "warning": "注意", "error": "异常", "muted": "已暂停",
        }.get(tone, "就绪")
        self.top_status.setText(f"●  {short_status}")
        self.top_status.setToolTip(message)
        self.top_status.setStyleSheet(f"color:{color}; font-weight:600; font-size:13px;")
        self.hero_stage.setText(message)
        self.hero_stage.setStyleSheet(f"color:{color}; font-size:13px; font-weight:500;")
        status_icon = tray_icon(color)
        if hasattr(self, "tray"):
            self.tray.setIcon(status_icon)
            self.tray.setToolTip(f"LLM Translator · {current_mode(self.config)['name']}\n{message[:80]}")
            self.tray_popup.set_status(short_status, message, color)

    def _toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.setText("继续" if self.paused else "暂停")
        self.tray_popup.pause_button.setText("恢复监听" if self.paused else "暂停监听")
        if self.paused:
            self._set_status("muted", "已暂停 · 快捷键不会启动新任务")
        elif self.busy:
            self._set_status("busy", "处理当前任务中…")
        else:
            self._set_status("idle", "监听已恢复 · 等待快捷键")

    def _show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if self.exiting:
            event.accept()
            return
        if self.tray.isVisible():
            event.ignore()
            self.hide()
            if not self.hidden_notice_sent:
                self.tray.showMessage("LLM Translator 仍在后台运行", "在系统托盘中可以打开、暂停或退出。", QSystemTrayIcon.Information, 3000)
                self.hidden_notice_sent = True
        else:
            event.accept()
            self._shutdown()

    def _shutdown(self):
        if self.exiting:
            return
        self.exiting = True
        if self.listener is not None:
            self.listener.stop()
            self.listener.wait(2200)
        self.worker.stop()
        self.result_overlay.hide()
        self.tray.hide()
        QApplication.instance().quit()


def main() -> int:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName("LLM Translator")
    app.setOrganizationName("LLM Translator")
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f8fafc"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.Text, QColor("#202124"))
    palette.setColor(QPalette.WindowText, QColor("#202124"))
    palette.setColor(QPalette.ButtonText, QColor("#202124"))
    app.setPalette(palette)
    available = set(QFontDatabase().families())
    # Prefer a native Chinese UI font: Segoe UI alone renders CJK through an
    # inconsistent fallback on Windows, especially at small sizes.
    family = next((name for name in (
        "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC",
        "Noto Sans CJK SC", "Source Han Sans SC", "Segoe UI",
    ) if name in available), app.font().family())
    font = QFont(family, 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    app.setStyleSheet(theme_stylesheet("light"))
    window = MainWindow()
    hide_on_start = "--minimized" in sys.argv or window.config.get("start_minimized", False)
    if not hide_on_start or not window.tray.isVisible() or "--show" in sys.argv:
        window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
