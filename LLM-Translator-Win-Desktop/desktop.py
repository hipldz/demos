"""Windows hotkey message pump and non-blocking translation worker."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import queue
import sys
import threading
import time

from PyQt5.QtCore import QObject, QThread, pyqtSignal

import main as win
from hotkeys import HotkeySpec
from translator import TranslationError, load_settings, translate_text


WM_QUIT = 0x0012


class HotkeyListener(QThread):
    pressed = pyqtSignal()
    registered = pyqtSignal(object)

    def __init__(self, automatic: HotkeySpec):
        super().__init__()
        self.automatic = automatic
        self._thread_id = 0
        self._ready = threading.Event()
        self._stopping = threading.Event()

    def run(self):
        if sys.platform != "win32":
            self.registered.emit({"auto": False, "error": "仅支持 Windows"})
            return
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        user32.RegisterHotKey.restype = wintypes.BOOL
        user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        user32.GetMessageW.restype = ctypes.c_int
        user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostThreadMessageW.restype = wintypes.BOOL

        self._thread_id = kernel32.GetCurrentThreadId()
        successful = False
        try:
            successful = bool(user32.RegisterHotKey(None, 1, self.automatic.modifiers, self.automatic.key))
            self._ready.set()
            self.registered.emit({"auto": successful})
            message = wintypes.MSG()
            while not self._stopping.is_set():
                status = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if status <= 0:
                    break
                if message.message == win.WM_HOTKEY and message.wParam == 1:
                    self.pressed.emit()
        except Exception as exc:
            self.registered.emit({"auto": False, "error": str(exc)})
        finally:
            self._ready.set()
            if successful:
                user32.UnregisterHotKey(None, 1)
            self._thread_id = 0

    def stop(self):
        self._stopping.set()
        self._ready.wait(timeout=1.5)
        if self._thread_id:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)


class WorkerSignals(QObject):
    phase = pyqtSignal(str, str)
    done = pyqtSignal(object)
    ready = pyqtSignal(bool, str)


class TranslationWorker:
    """Single daemon worker: clipboard owner HWND stays on its creating thread."""

    def __init__(self):
        self.signals = WorkerSignals()
        self._jobs: queue.Queue[tuple | None] = queue.Queue(maxsize=1)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="SelectionTranslator", daemon=True)

    def start(self):
        self._thread.start()

    def submit(self, release_keys: tuple[int, ...], mode_name: str, prompt: str, output_mode: str) -> bool:
        if self._stop.is_set():
            return False
        try:
            self._jobs.put_nowait(("selection", release_keys, mode_name, prompt, output_mode))
            return True
        except queue.Full:
            return False

    def submit_text(self, source: str, mode_name: str, prompt: str) -> bool:
        """Use the same background worker, without touching Windows selection or clipboard."""
        if self._stop.is_set():
            return False
        try:
            self._jobs.put_nowait(("text", source, mode_name, prompt))
            return True
        except queue.Full:
            return False

    def stop(self):
        self._stop.set()
        try:
            self._jobs.put_nowait(None)
        except queue.Full:
            pass

    def _run(self):
        if sys.platform != "win32":
            self.signals.ready.emit(False, "翻译功能需要 Windows 交互式桌面")
            return
        ole32 = ctypes.WinDLL("ole32")
        ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
        ole32.CoInitializeEx.restype = ctypes.c_long
        ole32.CoUninitialize.argtypes = []
        hr = ole32.CoInitializeEx(None, 2)  # STA: UI Automation COM calls.
        com_initialized = hr in (0, 1)
        try:
            user32, kernel32 = win.configure_win32()
        except Exception as exc:
            self.signals.ready.emit(False, f"Windows 初始化失败：{exc}")
            if com_initialized:
                ole32.CoUninitialize()
            return

        self.signals.ready.emit(True, "就绪")
        try:
            while not self._stop.is_set():
                job = self._jobs.get()
                if job is None or self._stop.is_set():
                    break
                if job[0] == "text":
                    _, source, mode_name, prompt = job
                    self._perform_text(source, mode_name, prompt)
                else:
                    _, release_keys, mode_name, prompt, output_mode = job
                    self._perform(user32, kernel32, release_keys, mode_name, prompt, output_mode)
        finally:
            # Window handles must be destroyed by their owning thread.
            if win.CLIPBOARD_OWNER_HWND:
                user32.DestroyWindow(win.CLIPBOARD_OWNER_HWND)
                win.CLIPBOARD_OWNER_HWND = None
            if com_initialized:
                ole32.CoUninitialize()

    def _perform(self, user32, kernel32, release_keys: tuple[int, ...], mode_name: str, prompt: str, output_mode: str):
        source = ""
        target = ""
        capture_method = ""
        try:
            settings = load_settings()
            self.signals.phase.emit("capture", "正在读取选中的文字…")
            snapshot = win.read_selection(user32, kernel32, release_keys)
            if snapshot is None:
                raise TranslationError("未检测到有效选区。请先选中文字，并在目标应用中重试。")
            source, capture_method = snapshot.text, snapshot.method

            self.signals.phase.emit("translate", f"正在调用 {settings.model} · {mode_name}…")
            target = translate_text(source, settings, prompt)
            if self._stop.is_set():
                return

            if output_mode == "float":
                # Display only: do not re-focus the editor or inject Ctrl+V.
                message = f"{mode_name}完成 · 悬浮显示（原文未修改）"
            elif output_mode == "replace":
                self.signals.phase.emit("replace", "正在检查选区并回填结果…")
                if not win.selection_is_still_active(user32, snapshot):
                    raise TranslationError("处理完成，但窗口或选区已改变；为避免误覆盖，未自动写入。")
                if source == target:
                    message = "结果与原文相同，无需替换"
                elif win.replace_selection(user32, kernel32, target, settings.replace_method):
                    message = f"{mode_name}完成，已向原选区发送替换操作"
                else:
                    raise TranslationError("结果已生成，但写回失败。请检查目标程序权限。")
            else:
                raise TranslationError("未知的输出方式；没有修改选中文字。")
            self.signals.done.emit({
                "ok": True, "mode": mode_name, "source": source, "target": target,
                "method": capture_method, "message": message, "time": time.time(),
                "output_mode": output_mode,
            })
        except TranslationError as exc:
            self.signals.done.emit({
                "ok": False, "mode": mode_name, "source": source, "target": target,
                "method": capture_method, "message": str(exc), "time": time.time(),
            })
        except Exception as exc:
            self.signals.done.emit({
                "ok": False, "mode": mode_name, "source": source, "target": target,
                "method": capture_method, "message": f"执行异常：{type(exc).__name__}", "time": time.time(),
            })

    def _perform_text(self, source: str, mode_name: str, prompt: str):
        target = ""
        try:
            settings = load_settings()
            self.signals.phase.emit("translate", f"正在调用 {settings.model} · {mode_name}…")
            target = translate_text(source, settings, prompt)
            if self._stop.is_set():
                return
            self.signals.done.emit({
                "ok": True, "mode": mode_name, "source": source, "target": target,
                "method": "manual", "message": "已完成", "time": time.time(),
                "output_mode": "manual",
            })
        except TranslationError as exc:
            self.signals.done.emit({
                "ok": False, "mode": mode_name, "source": source, "target": target,
                "method": "manual", "message": str(exc), "time": time.time(),
                "output_mode": "manual",
            })
        except Exception as exc:
            self.signals.done.emit({
                "ok": False, "mode": mode_name, "source": source, "target": target,
                "method": "manual", "message": f"执行异常：{type(exc).__name__}",
                "time": time.time(), "output_mode": "manual",
            })
