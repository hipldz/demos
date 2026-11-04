"""Build a Windows GUI one-file EXE: py -3 build_exe.py (run on Windows)."""

from __future__ import annotations

import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent


def _make_icon(destination: Path) -> None:
    """Convert the existing branded SVG to a Windows multi-resolution ICO."""
    from PIL import Image
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QImage, QPainter
    from PyQt5.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(str(ROOT / "assets" / "brand.svg"))
    if not renderer.isValid():
        raise RuntimeError("assets/brand.svg 无效，无法生成 EXE 图标")
    image = QImage(256, 256, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    png_path = destination.with_suffix(".png")
    if not image.save(str(png_path)):
        raise RuntimeError("无法生成 PNG 图标")
    with Image.open(png_path) as icon:
        icon.save(destination, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def main() -> int:
    if sys.platform != "win32":
        print("必须在 Windows 10/11 上运行此构建脚本；PyInstaller 不能跨系统生成 Windows EXE。")
        return 1
    try:
        from PyInstaller.__main__ import run
        import PIL  # noqa: F401  — required for ICO export
    except ImportError:
        print("请先安装构建依赖：py -3 -m pip install pyinstaller pillow")
        return 1

    work = ROOT / "build"
    work.mkdir(parents=True, exist_ok=True)
    icon = work / "LLM Translator.ico"
    _make_icon(icon)
    run([
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "LLM Translator",
        "--icon", str(icon),
        "--add-data", str(ROOT / "assets") + os.pathsep + "assets",
        "--hidden-import", "keyring.backends.Windows",
        "--hidden-import", "win32cred",
        "--collect-submodules", "keyring.backends",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(work / "pyinstaller"),
        "--specpath", str(work),
        str(ROOT / "app.py"),
    ])
    print("构建完成：", ROOT / "dist" / "LLM Translator.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
