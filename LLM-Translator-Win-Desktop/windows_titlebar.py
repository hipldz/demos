"""Best-effort Windows DWM styling for the native, non-client title bar."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys


DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36
DWMWA_COLOR_DEFAULT = 0xFFFFFFFF


def _colorref(rgb: str) -> int:
    """Convert #RRGGBB to the 0x00BBGGRR COLORREF used by Windows."""
    value = int(rgb.removeprefix("#"), 16)
    return ((value & 0xFF) << 16) | (value & 0xFF00) | ((value >> 16) & 0xFF)


def set_native_titlebar_theme(hwnd: int, theme: str) -> None:
    """Match the Qt theme when DWM supports it; older Windows remains usable."""
    if sys.platform != "win32" or not hwnd:
        return
    try:
        setter = ctypes.WinDLL("dwmapi").DwmSetWindowAttribute
        setter.argtypes = (wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD)
        setter.restype = ctypes.c_long

        def set_attribute(index: int, value: int) -> int:
            data = ctypes.c_uint32(value)
            return int(setter(wintypes.HWND(hwnd), index, ctypes.byref(data), ctypes.sizeof(data)))

        dark = theme == "dark"
        result = set_attribute(DWMWA_USE_IMMERSIVE_DARK_MODE, int(dark))
        if result != 0:
            # Older Windows 10 builds used 19 before the public enum stabilized.
            set_attribute(19, int(dark))

        if dark:
            set_attribute(DWMWA_CAPTION_COLOR, _colorref("#10151f"))
            set_attribute(DWMWA_TEXT_COLOR, _colorref("#eef3fb"))
        else:
            set_attribute(DWMWA_CAPTION_COLOR, DWMWA_COLOR_DEFAULT)
            set_attribute(DWMWA_TEXT_COLOR, DWMWA_COLOR_DEFAULT)
    except (OSError, AttributeError, TypeError, ValueError):
        # A custom title bar would remove native resize and caption controls;
        # leave those intact on Windows versions lacking the DWM attributes.
        return
