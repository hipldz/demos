"""Editable prompt profiles; source text always travels as a separate user message."""

from __future__ import annotations

from copy import deepcopy
import uuid

DEFAULT_MODES = [
    {
        "id": "smart",
        "name": "中英互译",
        "prompt": "你是一名顶级的专业翻译家，擅长精准、地道地进行中英互译。请将下面内容翻译成另一种语言。在翻译过程中，严格保持原文的含义、语气和风格，**仅输出翻译结果，无需添加任何解释或评论**",
    },
    {
        "id": "academic",
        "name": "学术润色",
        "prompt": "你是一位专业的文档编辑专家，请根据原文语言，将其润色为**专业、严谨且流畅的官方文档或正式商业文本风格**。在润色时，务必保持原文的核心事实和技术术语不变。**仅输出翻译结果，无需添加任何解释或评论**：",
    },
]


def default_modes() -> list[dict[str, str]]:
    return deepcopy(DEFAULT_MODES)


def new_mode() -> dict[str, str]:
    return {"id": uuid.uuid4().hex, "name": "新建模式", "prompt": "请按照当前任务要求处理用户提供的原文，仅输出处理结果，不要添加解释。"}


def validate_modes(items: object, active_id: object) -> tuple[list[dict[str, str]], str]:
    if not isinstance(items, list) or not (1 <= len(items) <= 30):
        raise ValueError("至少保留一个模式，最多支持 30 个模式")
    result = []
    ids = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("模式配置必须是对象列表")
        profile_id, name, prompt = item.get("id"), item.get("name"), item.get("prompt")
        if not isinstance(profile_id, str) or not profile_id or len(profile_id) > 64:
            raise ValueError("模式 ID 无效")
        if profile_id in ids:
            raise ValueError("模式 ID 不能重复")
        if not isinstance(name, str) or not (1 <= len(name.strip()) <= 40):
            raise ValueError("模式名称长度需在 1~40 字符之间")
        if not isinstance(prompt, str) or not (1 <= len(prompt.strip()) <= 6000):
            raise ValueError(f"模式「{name}」的 Prompt 长度需在 1~6000 字符之间")
        ids.add(profile_id)
        result.append({"id": profile_id, "name": name.strip(), "prompt": prompt.strip()})
    if not isinstance(active_id, str) or active_id not in ids:
        raise ValueError("当前选中的模式不存在")
    return result, active_id


def current_mode(config: dict) -> dict[str, str]:
    profiles, active = validate_modes(config["modes"], config["active_mode_id"])
    return next(profile for profile in profiles if profile["id"] == active)
