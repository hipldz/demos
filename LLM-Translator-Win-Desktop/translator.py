"""OpenAI-compatible Chat Completions translation via the Python stdlib."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from app_paths import SETTINGS_PATH
from modes import default_modes
from secret_store import SecretStorageError, get_saved_api_key

CONFIG_PATH = SETTINGS_PATH  # Historical import name; now a per-user, non-secret settings file.


class TranslationError(Exception):
    """A safe-to-display configuration or translation failure."""


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    replace_method: str = "paste"
    timeout_seconds: float = 30.0
    max_source_chars: int = 10000
    output_mode: str = "replace"

    @property
    def completion_url(self) -> str:
        url = self.base_url.rstrip("/")
        if url.endswith("/chat/completions"):
            return url
        return url + "/chat/completions"


def parse_settings(raw: dict, api_key: str) -> Settings:
    """Validate non-secret options together with the separately stored key."""
    api_key = api_key.strip()
    base_url = str(raw.get("base_url") or "").strip()
    model = str(raw.get("model") or "").strip()
    method = str(raw.get("replace_method") or "paste").strip().lower()
    output_mode = str(raw.get("output_mode") or "replace").strip().lower()
    if not api_key:
        raise TranslationError("请在设置中保存 API Key 到 Windows 凭据管理器，或设置 SELECT_TRANSLATOR_API_KEY 环境变量。")
    if not model:
        raise TranslationError("请在设置中填写 model。")
    if not base_url:
        raise TranslationError("请在设置中填写 base_url，例如 https://api.openai.com/v1。")

    parts = urlsplit(base_url)
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password:
        raise TranslationError("base_url 必须是有效的 http(s) API 根地址，且不能包含用户名或密码。")
    if parts.query or parts.fragment:
        raise TranslationError("base_url 不能包含查询参数或 #fragment。")
    if parts.scheme == "http" and parts.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise TranslationError("为保护 API Key，远程接口必须使用 HTTPS；本地 localhost 允许 HTTP。")
    if method not in ("paste", "type"):
        raise TranslationError("replace_method 只能是 paste 或 type。")
    if output_mode not in ("replace", "float"):
        raise TranslationError("output_mode 只能是 replace 或 float。")
    try:
        timeout = float(raw.get("timeout_seconds", 30))
        max_chars = int(raw.get("max_source_chars", 10000))
    except (TypeError, ValueError) as exc:
        raise TranslationError("timeout_seconds 或 max_source_chars 格式不正确。") from exc
    if not 1 <= timeout <= 120 or not 1 <= max_chars <= 100000:
        raise TranslationError("timeout_seconds 需在 1~120，max_source_chars 需在 1~100000。")

    return Settings(api_key, base_url, model, method, timeout, max_chars, output_mode)


def load_settings(path: Path = CONFIG_PATH) -> Settings:
    if not path.is_file():
        raise TranslationError("尚未保存应用设置；请在图形界面的设置页填写 API 配置。")
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        raise TranslationError(f"读取 settings.json 失败：{type(exc).__name__}") from exc
    if not isinstance(raw, dict):
        raise TranslationError("settings.json 顶层必须是 JSON 对象。")
    if "api_key" in raw:
        raise TranslationError("设置文件含有明文 api_key；请通过 GUI 迁移到 Windows 凭据管理器。")

    api_key = os.getenv("SELECT_TRANSLATOR_API_KEY", "").strip()
    if not api_key:
        try:
            api_key = get_saved_api_key()
        except SecretStorageError as exc:
            raise TranslationError(str(exc)) from exc
    return parse_settings(raw, api_key)


def translate_text(source: str, settings: Settings, mode_prompt: str | None = None) -> str:
    if not source.strip():
        raise TranslationError("未选中非空文本。")
    if len(source) > settings.max_source_chars:
        raise TranslationError(f"选中文字太长（{len(source)} 字符），超过配置上限 {settings.max_source_chars}。")

    # Legacy CLI calls omit the mode; they still use the same built-in Prompt.
    instruction = mode_prompt if mode_prompt is not None else default_modes()[0]["prompt"]
    payload = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": instruction},
            {"role": "user", "content": source},
        ],
        "stream": False,
    }
    request = Request(
        settings.completion_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.timeout_seconds) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
    except HTTPError as exc:
        raise TranslationError(f"接口返回 HTTP {exc.code}；请检查 API Key、Base URL 和 model。") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise TranslationError(f"接口连接失败或超时：{type(exc).__name__}。") from exc
    if len(raw) > 8 * 1024 * 1024:
        raise TranslationError("接口响应过大，已取消替换。")

    try:
        content = json.loads(raw)["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(item.get("text", "") for item in content if isinstance(item, dict))
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise TranslationError("接口响应不是预期的 Chat Completions JSON 格式。") from exc
    if not isinstance(content, str) or not content.strip():
        raise TranslationError("接口没有返回非空处理结果，因此不会覆盖原文。")
    return content.strip("\r\n")
