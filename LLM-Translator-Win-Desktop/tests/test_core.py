"""Cross-platform checks for the Prompt-only processing contract."""

from __future__ import annotations

import ast
import ctypes
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from modes import current_mode, default_modes
from settings_store import read_config, save_config
from translator import Settings, translate_text
from windows_titlebar import _colorref, set_native_titlebar_theme


class PromptTests(unittest.TestCase):
    def test_two_builtin_prompts_are_exact(self):
        modes = default_modes()
        self.assertEqual([(mode["id"], mode["name"]) for mode in modes], [
            ("smart", "中英互译"), ("academic", "学术润色"),
        ])
        self.assertEqual(modes[0]["prompt"], "你是一名顶级的专业翻译家，擅长精准、地道地进行中英互译。请将下面内容翻译成另一种语言。在翻译过程中，严格保持原文的含义、语气和风格，**仅输出翻译结果，无需添加任何解释或评论**")
        self.assertEqual(modes[1]["prompt"], "你是一位专业的文档编辑专家，请根据原文语言，将其润色为**专业、严谨且流畅的官方文档或正式商业文本风格**。在润色时，务必保持原文的核心事实和技术术语不变。**仅输出翻译结果，无需添加任何解释或评论**：")

    def test_request_sends_prompt_unchanged(self):
        captured = []

        def fake_urlopen(request, timeout):
            captured.append(json.loads(request.data.decode("utf-8")))
            return io.BytesIO(b'{"choices":[{"message":{"content":"ok"}}]}')

        settings = Settings(api_key="dummy", base_url="https://api.example/v1", model="demo")
        with patch("translator.urlopen", side_effect=fake_urlopen):
            self.assertEqual(translate_text("hello", settings, "Only uppercase the text."), "ok")
            self.assertEqual(translate_text("你好", settings), "ok")
        self.assertEqual(captured[0]["messages"], [
            {"role": "system", "content": "Only uppercase the text."},
            {"role": "user", "content": "hello"},
        ])
        self.assertEqual(captured[1]["messages"][0]["content"], default_modes()[0]["prompt"])

    def test_old_development_modes_reset_without_compatibility(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            path.write_text(json.dumps({
                "target_language": "Japanese", "model": "my-model",
                "modes": [{"id": "old", "name": "旧模式", "prompt": "unused"}],
                "active_mode_id": "old",
            }), encoding="utf-8")
            cfg = read_config(path)
            self.assertEqual(cfg["settings_version"], 2)
            self.assertNotIn("target_language", cfg)
            self.assertEqual(cfg["model"], "my-model")
            self.assertEqual(current_mode(cfg)["id"], "smart")
            self.assertEqual(len(cfg["modes"]), 2)
            saved = save_config({"output_mode": "float"}, path, validate_api=False)
            self.assertEqual(saved["output_mode"], "float")
            self.assertNotIn("target_language", json.loads(path.read_text(encoding="utf-8")))

    def test_version_two_custom_modes_are_kept(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            modes = default_modes() + [{"id": "mine", "name": "术语检查", "prompt": "指出错误"}]
            path.write_text(json.dumps({
                "settings_version": 2, "modes": modes, "active_mode_id": "mine",
            }), encoding="utf-8")
            cfg = read_config(path)
            self.assertEqual(current_mode(cfg)["prompt"], "指出错误")
            self.assertEqual(len(cfg["modes"]), 3)

    def test_vector_assets_are_valid_xml(self):
        assets = Path(__file__).resolve().parents[1] / "assets"
        for name in (
            "brand.svg", "brand-dark.svg", "tray.svg",
            "check-on.svg", "check-off.svg", "check-off-dark.svg",
            "theme-sun.svg", "theme-moon.svg",
        ):
            with self.subTest(asset=name):
                content = (assets / name).read_text(encoding="utf-8")
                if name == "tray.svg":
                    content = content.replace("__STATUS_COLOR__", "#777cf6")
                root = ElementTree.fromstring(content)
                self.assertTrue(root.tag.endswith("svg"))

    def test_overview_owns_history_and_uses_custom_selectors(self):
        source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        window = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "MainWindow")
        methods = {node.name for node in window.body if isinstance(node, ast.FunctionDef)}
        self.assertNotIn("_build_history", methods)
        self.assertIn("self.history_list = QListWidget()", source)
        self.assertIn("self.active_mode_combo = SimpleSelect()", source)
        for control in ("output_quick", "output_field", "replace_field", "theme_field"):
            self.assertIn(f"self.{control} = SegmentedChoice()", source)
        self.assertNotIn("QComboBox()", source)
        self.assertIn("self.run_button.clicked.connect(self._manual_run)", source)

    def test_manual_and_history_fields_are_isolated(self):
        source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        window = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "MainWindow")
        methods = {
            node.name: ast.get_source_segment(source, node)
            for node in window.body if isinstance(node, ast.FunctionDef)
        }
        self.assertIn('self.nav_keys = ("overview", "manual", "modes", "settings")', source)
        self.assertIn("self.history_source = QPlainTextEdit()", methods["_build_dashboard"])
        self.assertNotIn("self.source_preview", methods["_build_dashboard"])
        self.assertNotIn("self.run_button", methods["_build_dashboard"])
        self.assertIn("self.source_preview = QPlainTextEdit()", methods["_build_manual"])
        self.assertIn("self.target_preview = QPlainTextEdit()", methods["_build_manual"])
        self.assertIn('text_label("翻译", "pageTitle")', methods["_build_manual"])
        self.assertIn("scroll.setWidgetResizable(True)", methods["_build_manual"])
        self.assertIn("self.pages.addWidget(scroll)", methods["_build_manual"])
        self.assertIn("self.source_preview.setMinimumHeight(88)", methods["_build_manual"])
        self.assertIn("self.target_preview.setMinimumHeight(88)", methods["_build_manual"])
        self.assertIn("vl.setStretch(vl.indexOf(input_card), 1)", methods["_build_manual"])
        self.assertIn("vl.setStretch(vl.indexOf(result_card), 1)", methods["_build_manual"])
        self.assertIn('self.manual_mode_label = text_label("中英互译", "modeTag")', methods["_build_manual"])
        self.assertIn("self.manual_mode_label.setWordWrap(False)", methods["_build_manual"])
        self.assertIn("self.manual_mode_label.setFixedSize(146, 34)", methods["_build_manual"])
        self.assertIn("self.manual_mode_label.fontMetrics().elidedText(", methods["_refresh_mode_widgets"])
        self.assertIn("label.setWordWrap(wrap)", source)
        self.assertNotIn("self.source_preview", methods["_show_history"])
        self.assertIn("self.history_source", methods["_show_history"])
        self.assertIn('item.get("output_mode") == "manual"', methods["_done"])

    def test_tray_uses_custom_panel_and_theme_svg(self):
        source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertIn("class TrayPopup(QWidget):", source)
        self.assertIn("self.tray.activated.connect(self._tray_activated)", source)
        self.assertNotIn("self.tray.setContextMenu(", source)
        self.assertIn("self.theme_toggle.setIcon(theme_icon(", source)
        self.assertIn('QTimer.singleShot(60, self.tray_popup.show_at_cursor)', source)

    def test_floating_result_is_draggable_and_remembers_position(self):
        source = (Path(__file__).resolve().parents[1] / "floating_result.py").read_text(encoding="utf-8")
        self.assertIn("def eventFilter(self, obj, event):", source)
        self.assertIn("self._user_moved = True", source)
        self.assertIn("if self._user_moved:", source)
        # Regression: installing the filter before creating heading crashed app startup.
        tree = ast.parse(source)
        result = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "FloatingResult")
        constructor = next(node for node in result.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        init_source = ast.get_source_segment(source, constructor)
        self.assertLess(init_source.index('self.heading = QLabel("处理结果")'),
                        init_source.index("self.heading.installEventFilter(self)"))
        self.assertLess(init_source.index('self.set_theme("light")'),
                        init_source.index("self.drag_handle.installEventFilter(self)"))
        self.assertIn('getattr(self, "heading", None)', source)
        self.assertIn('getattr(self, "drag_handle", None)', source)

    def test_brand_and_tray_use_the_same_translation_mark(self):
        assets = Path(__file__).resolve().parents[1] / "assets"
        brand = ElementTree.parse(assets / "brand.svg").getroot()
        brand_dark = ElementTree.parse(assets / "brand-dark.svg").getroot()
        tray = ElementTree.fromstring((assets / "tray.svg").read_text(encoding="utf-8").replace(
            "__STATUS_COLOR__", "#3575dc"))
        def paths(root):
            return [node.attrib["d"] for node in root.iter() if node.tag.endswith("path")]

        self.assertEqual(len(paths(brand)), 6)
        self.assertEqual(paths(brand), paths(brand_dark))
        self.assertEqual(paths(brand), paths(tray))
        for icon in (brand, brand_dark, tray):
            self.assertEqual(icon.attrib["viewBox"], "0 0 50 50")
        for icon in (brand, brand_dark):
            self.assertFalse(any(node.tag.endswith("rect") for node in icon.iter()),
                             "brand must remain transparent without a background tile")
        tray_tiles = [node for node in tray.iter() if node.tag.endswith("rect")]
        self.assertEqual(len(tray_tiles), 1)
        self.assertEqual(tray_tiles[0].get("fill"), "#3575dc")
        source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertIn("self.brand_logo.setPixmap(brand_icon(self.theme)", source)
        self.assertIn("self.logo.setPixmap(brand_icon(mode)", source)
        self.assertIn("self.tray.setIcon(status_icon)", source)
        self.assertNotIn("self.setWindowIcon(status_icon)", source)
        self.assertIn("self.setWindowIcon(brand_icon(self.theme))", source)

    def test_header_layout_and_native_titlebar_theme(self):
        source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        window = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "MainWindow")
        methods = {
            node.name: ast.get_source_segment(source, node)
            for node in window.body if isinstance(node, ast.FunctionDef)
        }
        header = methods["_build_ui"]
        self.assertIn('("翻译", "manual", 1)', header)
        self.assertLess(header.index('self.top_status = text_label('),
                        header.index("bar.addStretch(1)"))
        self.assertLess(header.index("bar.addStretch(1)"),
                        header.index("self.theme_toggle = QPushButton()"))
        self.assertIn("set_native_titlebar_theme(int(self.winId()), self.theme)", methods["_sync_native_titlebar"])
        self.assertIn("QTimer.singleShot(0, self._sync_native_titlebar)", methods["showEvent"])
        self.assertEqual(_colorref("#10151f"), 0x001F1510)
        self.assertEqual(_colorref("#eef3fb"), 0x00FBF3EE)
        # Does not access Windows APIs on non-Windows systems.
        set_native_titlebar_theme(12345, "dark")

    def test_titlebar_attributes_restore_light_colors(self):
        class DwmSpy:
            def __init__(self):
                self.calls = []

            def __call__(self, hwnd, attribute, value, size):
                number = ctypes.cast(value, ctypes.POINTER(ctypes.c_uint32)).contents.value
                self.calls.append((attribute, number))
                return 0

        spy = DwmSpy()
        with patch("windows_titlebar.sys.platform", "win32"), patch(
            "windows_titlebar.ctypes.WinDLL",
            return_value=SimpleNamespace(DwmSetWindowAttribute=spy), create=True,
        ):
            set_native_titlebar_theme(100, "dark")
            set_native_titlebar_theme(100, "light")
        self.assertEqual(spy.calls, [
            (20, 1), (35, 0x001F1510), (36, 0x00FBF3EE),
            (20, 0), (35, 0xFFFFFFFF), (36, 0xFFFFFFFF),
        ])

    def test_theme_is_saved_and_validated(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            self.assertEqual(read_config(path)["theme"], "light")
            saved = save_config({"theme": "dark"}, path, validate_api=False)
            self.assertEqual(saved["theme"], "dark")
            self.assertEqual(read_config(path)["theme"], "dark")
            with self.assertRaises(ValueError):
                save_config({"theme": "invalid"}, path, validate_api=False)

    def test_manual_request_does_not_use_windows_selection_functions(self):
        source = (Path(__file__).resolve().parents[1] / "desktop.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        worker = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "TranslationWorker")
        method = next(node for node in worker.body if isinstance(node, ast.FunctionDef) and node.name == "_perform_text")
        accessed = [
            node for node in ast.walk(method) if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name) and node.value.id == "win"
        ]
        self.assertEqual(accessed, [])
        self.assertIn("translate_text(source, settings, prompt)", source)


if __name__ == "__main__":
    unittest.main()
