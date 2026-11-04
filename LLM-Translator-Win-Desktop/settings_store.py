"""Non-secret user settings for the current desktop release."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from app_paths import SETTINGS_PATH
from hotkeys import parse_hotkey
from modes import default_modes, validate_modes
from secret_store import SecretStorageError, get_saved_api_key, set_saved_api_key
from translator import CONFIG_PATH, TranslationError, parse_settings


DEFAULTS = {
    "settings_version": 2,
    "theme": "light",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "replace_method": "paste",
    "output_mode": "replace",
    "timeout_seconds": 30,
    "max_source_chars": 10000,
    "hotkey_auto": "Ctrl+Shift+X",
    "start_minimized": False,
    "notify_on_finish": True,
    "modes": default_modes(),
    "active_mode_id": "smart",
}


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"设置文件无法读取（{path.name}）：{type(exc).__name__}") from exc
    if not isinstance(data, dict):
        raise ValueError("设置文件顶层必须是 JSON 对象")
    return data


def _write_json(path: Path, data: dict) -> None:
    """Atomic replacement: no partial JSON or plaintext API Key on disk."""
    if "api_key" in data:
        raise ValueError("禁止把 API Key 写入普通设置文件")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".json", prefix=".settings-",
            dir=path.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_config(path: Path = CONFIG_PATH) -> dict:
    if not path.is_file():
        return {**DEFAULTS, "modes": default_modes()}
    existing = _load_json(path)
    if "api_key" in existing:
        raise ValueError("设置文件不能包含明文 API Key；请删除该字段并通过界面保存密钥。")
    merged = {**DEFAULTS, **existing}
    merged.pop("hotkey_clipboard", None)
    merged.pop("target_language", None)  # Obsolete: the selected Prompt owns intent and language.
    if existing.get("settings_version") != 2:
        # Development build: start fresh with the two new prompts; no v1 mode migration.
        merged["modes"] = default_modes()
        merged["active_mode_id"] = "smart"
    merged["settings_version"] = 2
    if merged["theme"] not in ("light", "dark"):
        raise ValueError("界面主题只能是 light 或 dark")
    merged["modes"], merged["active_mode_id"] = validate_modes(
        merged["modes"], merged["active_mode_id"]
    )
    return merged


def save_config(values: dict, path: Path = CONFIG_PATH, *, validate_api: bool = True) -> dict:
    """Save only non-secret preferences; a nonblank key updates the Win vault."""
    values = dict(values)
    incoming_key = str(values.pop("api_key", "") or "").strip()
    try:
        existing = read_config(path)
    except ValueError as exc:
        if path.is_file() and "设置文件无法读取" in str(exc):
            existing = {**DEFAULTS, "modes": default_modes()}
        else:
            raise  # Especially never hide failure to migrate a plaintext key.
    merged = {**existing, **values}
    merged.pop("hotkey_clipboard", None)
    merged.pop("target_language", None)
    merged.pop("api_key", None)
    if merged.get("theme") not in ("light", "dark"):
        raise ValueError("界面主题只能是 light 或 dark")
    parse_hotkey(str(merged["hotkey_auto"]))
    merged["modes"], merged["active_mode_id"] = validate_modes(
        merged["modes"], merged["active_mode_id"]
    )
    try:
        if validate_api:
            current_key = incoming_key or os.getenv("SELECT_TRANSLATOR_API_KEY", "").strip() or get_saved_api_key()
            parse_settings(merged, current_key)
        if incoming_key:
            set_saved_api_key(incoming_key)
        _write_json(path, merged)
    except (OSError, TranslationError, SecretStorageError) as exc:
        raise ValueError(str(exc)) from exc
    return merged
