"""Windows Ctrl+Shift+X: translate selected text and replace it in-place.

Uses the standard library for hotkeys/copy; optionally uses ``uiautomation``.
Run in the signed-in user's interactive desktop session.
"""

from __future__ import annotations

import atexit
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import sys
import time

from translator import TranslationError, load_settings, translate_text


HOTKEY_READ = 1
HOTKEY_QUIT = 2
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
VK_X = 0x58
VK_Q = 0x51
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_C = 0x43
VK_V = 0x56

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

LOG_PATH = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "AltTSelection" / "selected_text.log"
CLIPBOARD_OWNER_HWND = None


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class MOUSEINPUT(ctypes.Structure):
    # INPUT's union must have the size of its largest Win32 member.
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]


@dataclass
class SelectionSnapshot:
    text: str
    method: str
    window: int
    focus_hwnd: int | None
    control: object | None


class SelectionCaptureError(TranslationError):
    """An actionable failure to capture text from the foreground selection."""


def configure_win32():
    global CLIPBOARD_OWNER_HWND
    expected_input_size = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
    if ctypes.sizeof(INPUT) != expected_input_size:
        raise RuntimeError("Windows INPUT 结构体大小不匹配，无法安全模拟按键。")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = ctypes.c_int
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = wintypes.SHORT
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
    user32.GetGUIThreadInfo.restype = wintypes.BOOL
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
    user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.GetClipboardSequenceNumber.restype = wintypes.DWORD

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL

    # EmptyClipboard needs a real owner HWND; passing NULL makes SetClipboardData fail.
    # A message-only STATIC window is invisible and belongs to this Python thread.
    owner = user32.CreateWindowExW(
        0, "STATIC", "AltTSelectionClipboard", 0, 0, 0, 0, 0,
        wintypes.HWND(-3), None, None, None,  # HWND_MESSAGE
    )
    if not owner:
        raise RuntimeError("无法创建剪贴板所有者窗口。")
    CLIPBOARD_OWNER_HWND = owner
    atexit.register(user32.DestroyWindow, owner)
    return user32, kernel32


def log(message: str, *, selected: bool = False, method: str = "") -> None:
    if sys.stdout is not None:
        print(message, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        label = "选中文本" if selected else "状态"
        if method:
            label += f" ({method})"
        f.write(f"[{stamp}] {label}\n{message}\n\n")


def open_clipboard(user32) -> bool:
    for _ in range(12):
        if user32.OpenClipboard(CLIPBOARD_OWNER_HWND):
            return True
        time.sleep(0.02)
    return False


def read_clipboard_text(user32, kernel32) -> str | None:
    if not open_clipboard(user32):
        return None
    try:
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return None
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            return None
        try:
            return ctypes.wstring_at(pointer)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def write_clipboard_text(user32, kernel32, text: str) -> bool:
    data = (text + "\0").encode("utf-16-le")
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not handle:
        return False
    pointer = kernel32.GlobalLock(handle)
    if not pointer:
        kernel32.GlobalFree(handle)
        return False
    ctypes.memmove(pointer, data, len(data))
    kernel32.GlobalUnlock(handle)

    if not open_clipboard(user32):
        kernel32.GlobalFree(handle)
        return False
    try:
        if user32.EmptyClipboard() and user32.SetClipboardData(CF_UNICODETEXT, handle):
            handle = None  # Windows owns the memory after SetClipboardData.
            return True
        return False
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)


def send_ctrl_key(user32, key: int) -> bool:
    events = (INPUT * 4)(
        INPUT(INPUT_KEYBOARD, INPUT_UNION(ki=KEYBDINPUT(VK_CONTROL, 0, 0, 0, 0))),
        INPUT(INPUT_KEYBOARD, INPUT_UNION(ki=KEYBDINPUT(key, 0, 0, 0, 0))),
        INPUT(INPUT_KEYBOARD, INPUT_UNION(ki=KEYBDINPUT(key, 0, KEYEVENTF_KEYUP, 0, 0))),
        INPUT(INPUT_KEYBOARD, INPUT_UNION(ki=KEYBDINPUT(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0, 0))),
    )
    return user32.SendInput(len(events), events, ctypes.sizeof(INPUT)) == len(events)


def send_ctrl_c(user32) -> bool:
    return send_ctrl_key(user32, VK_C)


def send_unicode_text(user32, value: str) -> bool:
    """Type UTF-16 code units with KEYEVENTF_UNICODE (avoids clipboard)."""
    raw = value.encode("utf-16-le")
    units = [int.from_bytes(raw[i : i + 2], "little") for i in range(0, len(raw), 2)]
    for start in range(0, len(units), 64):
        chunk = units[start : start + 64]
        events = []
        for unit in chunk:
            events.append(INPUT(INPUT_KEYBOARD, INPUT_UNION(ki=KEYBDINPUT(0, unit, KEYEVENTF_UNICODE, 0, 0))))
            events.append(INPUT(INPUT_KEYBOARD, INPUT_UNION(ki=KEYBDINPUT(0, unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0))))
        array = (INPUT * len(events))(*events)
        if user32.SendInput(len(events), array, ctypes.sizeof(INPUT)) != len(events):
            return False
    return True


def focused_hwnd(user32) -> int | None:
    info = GUITHREADINFO()
    info.cbSize = ctypes.sizeof(GUITHREADINFO)
    if user32.GetGUIThreadInfo(0, ctypes.byref(info)):
        return info.hwndFocus
    return None


def wait_hotkey_release(user32, keys: tuple[int, ...] = (VK_CONTROL, VK_SHIFT, VK_X)) -> bool:
    deadline = time.monotonic() + 2.0
    while any(user32.GetAsyncKeyState(key) & 0x8000 for key in keys):
        if time.monotonic() >= deadline:
            log("请先松开快捷键组合，再试一次。")
            return False
        time.sleep(0.015)
    return True


def get_uia_selection() -> tuple[str | None, object | None]:
    """Read focused control's TextPattern selection, without changing clipboard.

    UI Automation is optional; an unsupported provider returns (None, control).
    """
    try:
        import uiautomation as auto
    except Exception:
        return None, None

    try:
        control = auto.GetFocusedControl()
    except Exception:
        return None, None

    try:
        pattern = control.GetTextPattern()
        if not pattern:
            return None, control
        fragments = [selection.GetText(-1) for selection in pattern.GetSelection()]
        text = "".join(fragment for fragment in fragments if fragment)
        return (text or None), control
    except Exception:
        return None, control


def _check_capture_target(user32, window: int, focus: int | None) -> None:
    """Never inject a retry into a different window or focused input."""
    if user32.GetForegroundWindow() != window:
        raise SelectionCaptureError("读取期间前台窗口已改变；为避免复制其他窗口的内容，已取消。")
    current_focus = focused_hwnd(user32)
    if focus and current_focus and focus != current_focus:
        raise SelectionCaptureError("读取期间输入焦点已改变；为避免复制错误的内容，已取消。")


def read_selection(user32, kernel32, release_keys: tuple[int, ...] | None = None) -> SelectionSnapshot:
    active_window = user32.GetForegroundWindow()
    original_focus = focused_hwnd(user32)

    # Ctrl+A immediately followed by the hotkey is common.  Do not query UIA
    # (or inject Ctrl+C) until the hotkey's *entire* key chord is released.
    if not wait_hotkey_release(user32, release_keys or (VK_CONTROL, VK_SHIFT, VK_X)):
        raise SelectionCaptureError("快捷键尚未完全松开（等待超过 2 秒）；请松开按键后重试。")
    time.sleep(0.06)
    _check_capture_target(user32, active_window, original_focus)

    selected_text, focused_control = get_uia_selection()
    _check_capture_target(user32, active_window, original_focus)
    if selected_text:
        return SelectionSnapshot(selected_text, "UI Automation", active_window, original_focus, focused_control)

    # The browser may not implement UIA TextPattern.  The clipboard sequence
    # number alone does not guarantee that CF_UNICODETEXT is already readable.
    # Allow the copy to settle, and retry the shortcut once if no copy happened.
    # No clipboard marker is written: this preserves pre-existing rich formats
    # until the target app actually handles Ctrl+C.
    old_text = read_clipboard_text(user32, kernel32)
    previous_version = user32.GetClipboardSequenceNumber()
    copied_version = None
    try:
        # First copy gets ~0.6s, the retry ~1.4s; no artificial cooldown
        # is imposed between successful translations.
        for attempt, polls in enumerate((24, 56)):
            _check_capture_target(user32, active_window, original_focus)
            if attempt:
                # A web editor may expose its selection to UIA after a delay.
                selected_text, new_control = get_uia_selection()
                _check_capture_target(user32, active_window, original_focus)
                if selected_text:
                    return SelectionSnapshot(selected_text, "UI Automation", active_window, original_focus, new_control)
            if not send_ctrl_c(user32):
                raise SelectionCaptureError("Windows 无法模拟 Ctrl+C；请检查目标应用权限。")
            for _ in range(polls):
                time.sleep(0.025)
                _check_capture_target(user32, active_window, original_focus)
                version = user32.GetClipboardSequenceNumber()
                if version == previous_version:
                    continue
                if copied_version is None:
                    copied_version = version
                selected_text = read_clipboard_text(user32, kernel32)
                # A changed sequence may precede readable text or a temporary
                # clipboard lock; accept only a stable, nonempty text read.
                if version == user32.GetClipboardSequenceNumber() and selected_text:
                    return SelectionSnapshot(selected_text, "Ctrl+C", active_window, original_focus, focused_control)
            if copied_version is not None:
                # Copy did occur, but data is not available; sending another
                # Ctrl+C could race with the first copy and corrupt the result.
                break

        if copied_version is None:
            raise SelectionCaptureError(
                "快捷键已触发，但模拟 Ctrl+C 两次均未更新剪贴板（约 2 秒）。"
                "请确认目标输入框仍保持选中状态。"
            )
        raise SelectionCaptureError("剪贴板发生变化，但仍未读到纯文本；可能被浏览器或其他程序短暂占用。")
    finally:
        # Do not overwrite any clipboard update made by another app in the
        # meantime.  Restore only if the clipboard still contains our copy.
        if old_text is not None and copied_version is not None:
            if user32.GetClipboardSequenceNumber() == copied_version:
                if not write_clipboard_text(user32, kernel32, old_text):
                    log("警告：原有剪贴板文本未能恢复。")


def uia_control_id(control: object | None) -> tuple | None:
    if control is None:
        return None
    try:
        return tuple(control.Element.GetRuntimeId())
    except Exception:
        return None


def selection_is_still_active(user32, selection: SelectionSnapshot) -> bool:
    if user32.GetForegroundWindow() != selection.window:
        return False
    current_focus = focused_hwnd(user32)
    if selection.focus_hwnd and current_focus and current_focus != selection.focus_hwnd:
        return False
    current_text, current_control = get_uia_selection()
    if selection.method == "UI Automation" and current_text != selection.text:
        return False
    if current_text is not None and current_text != selection.text:
        return False
    before_id = uia_control_id(selection.control)
    after_id = uia_control_id(current_control)
    if before_id is not None and after_id is not None and before_id != after_id:
        return False
    return True


def replace_selection(user32, kernel32, translation: str, method: str) -> bool:
    if method == "type":
        return send_unicode_text(user32, translation)

    old_text = read_clipboard_text(user32, kernel32)
    if not write_clipboard_text(user32, kernel32, translation):
        return False
    pasted_version = user32.GetClipboardSequenceNumber()
    pasted = send_ctrl_key(user32, VK_V)
    # Clipboard paste may be consumed asynchronously by the destination app.
    time.sleep(0.25)
    if old_text is not None and user32.GetClipboardSequenceNumber() == pasted_version:
        if not write_clipboard_text(user32, kernel32, old_text):
            log("警告：原剪贴板纯文本恢复失败。")
    return pasted


def translate_and_replace(user32, kernel32) -> None:
    try:
        snapshot = read_selection(user32, kernel32)
    except SelectionCaptureError as error:
        log(f"读取选区失败：{error}")
        return

    log(snapshot.text, selected=True, method=f"原文 · {snapshot.method}")
    try:
        settings = load_settings()
        log("正在请求 Chat Completions 翻译，请暂时不要切换窗口或移动光标……")
        translated = translate_text(snapshot.text, settings)
    except TranslationError as error:
        log(f"翻译失败，原文未替换：{error}")
        return

    log(translated, selected=True, method="译文")
    if not selection_is_still_active(user32, snapshot):
        log("窗口、焦点或选区已改变：为了安全，没有把译文写回。")
        return
    if translated == snapshot.text:
        log("译文与原文相同，无需替换。")
        return
    if replace_selection(user32, kernel32, translated, settings.replace_method):
        log("已尝试替换原选区。")
    else:
        log("替换输入失败；请检查目标应用权限。若只发送了部分按键，可能需要手动撤销。")


def main() -> int:
    if sys.platform != "win32":
        print("本项目只能在 Windows 上运行。", file=sys.stderr)
        return 1

    user32, kernel32 = configure_win32()
    if not user32.RegisterHotKey(None, HOTKEY_QUIT, MOD_ALT | MOD_SHIFT | MOD_NOREPEAT, VK_Q):
        log("Alt+Shift+Q 注册失败，请更换退出快捷键。")
        return 1
    try:
        if not user32.RegisterHotKey(None, HOTKEY_READ, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_X):
            log("Ctrl+Shift+X 被其他程序占用：请先退出旧进程。")
            return 1
        try:
            return run_message_loop(user32, kernel32)
        finally:
            user32.UnregisterHotKey(None, HOTKEY_READ)
    finally:
        user32.UnregisterHotKey(None, HOTKEY_QUIT)


def run_message_loop(user32, kernel32) -> int:
    log("已启动：Ctrl+Shift+X 自动翻译替换；Alt+Shift+Q 退出。")
    try:
        settings = load_settings()
        log(f"处理配置就绪：模型 {settings.model}，写回方式 {settings.replace_method}；语言由 Prompt 决定。")
    except TranslationError as error:
        log(f"翻译配置尚未就绪：{error}")
    message = wintypes.MSG()
    while True:
        result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
        if result <= 0:
            return 0 if result == 0 else 1
        if message.message != WM_HOTKEY:
            continue
        if message.wParam == HOTKEY_QUIT:
            log("程序已退出。")
            return 0
        try:
            if message.wParam == HOTKEY_READ:
                translate_and_replace(user32, kernel32)
        except Exception as error:
            log(f"执行失败：{type(error).__name__}：{error}")


if __name__ == "__main__":
    raise SystemExit(main())
