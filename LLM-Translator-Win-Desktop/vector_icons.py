"""Vector icons rendered with Qt SVG; no font glyphs or raster assets needed."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer


ASSETS = Path(__file__).with_name("assets")


def svg_pixmap(svg_data: bytes, size: int) -> QPixmap:
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    renderer = QSvgRenderer(QByteArray(svg_data))
    if not renderer.isValid():
        raise ValueError("SVG 图标无效")
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return result


def brand_icon(mode: str = "light") -> QIcon:
    asset = "brand-dark.svg" if mode == "dark" else "brand.svg"
    svg_data = (ASSETS / asset).read_bytes()
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128):
        icon.addPixmap(svg_pixmap(svg_data, size))
    return icon


def tray_icon(color: str) -> QIcon:
    svg_data = (ASSETS / "tray.svg").read_bytes().replace(b"__STATUS_COLOR__", color.encode("ascii"))
    icon = QIcon()
    for size in (16, 24, 32, 48):
        icon.addPixmap(svg_pixmap(svg_data, size))
    return icon


def theme_icon(mode: str) -> QIcon:
    """Own SVG sun/moon marks, shared by the header and tray theme picker."""
    name = "theme-moon.svg" if mode == "dark" else "theme-sun.svg"
    svg_data = (ASSETS / name).read_bytes()
    icon = QIcon()
    for size in (16, 20, 24, 32, 48):
        icon.addPixmap(svg_pixmap(svg_data, size))
    return icon


_NAV_PATHS = {
    "overview": '<rect x="3.5" y="3.5" width="7" height="7" rx="1.8"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.8"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.8"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.8"/>',
    "manual": '<rect x="3.5" y="3.5" width="17" height="17" rx="4"/><path d="m7 9 3 3-3 3M12.5 15h4.5"/>',
    "modes": '<rect x="3.5" y="3" width="17" height="18" rx="3"/><path d="M7.5 8h9M7.5 12h9M7.5 16h5"/>',
    "settings": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2.2" fill="__FILL__"/><circle cx="15.5" cy="12" r="2.2" fill="__FILL__"/><circle cx="9" cy="18" r="2.2" fill="__FILL__"/>',
    "history": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3.5 2.5"/>',
}


def nav_icon(name: str, active: bool = False) -> QIcon:
    shapes = _NAV_PATHS[name].replace("__FILL__", "#e0ebff" if active else "#f1f4f9")
    stroke = "#2d6cc4" if active else "#64748b"
    markup = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{stroke}" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">' + shapes + '</svg>'
    ).encode("utf-8")
    icon = QIcon()
    for size in (16, 20, 24, 32, 48):
        icon.addPixmap(svg_pixmap(markup, size))
    return icon
