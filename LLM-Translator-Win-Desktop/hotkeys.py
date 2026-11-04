"""Pure-Python Windows hotkey parsing, shared by the UI and listener."""

from dataclasses import dataclass

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

_MODIFIERS = {
    "CTRL": (MOD_CONTROL, 0x11),
    "ALT": (MOD_ALT, 0x12),
    "SHIFT": (MOD_SHIFT, 0x10),
    "WIN": (MOD_WIN, 0x5B),
}
_ALIASES = {"CONTROL": "CTRL", "WINDOWS": "WIN", "META": "WIN"}
_SPECIAL = {
    "SPACE": 0x20, "TAB": 0x09, "ENTER": 0x0D, "ESC": 0x1B,
    "HOME": 0x24, "END": 0x23, "INSERT": 0x2D, "DELETE": 0x2E,
    "UP": 0x26, "DOWN": 0x28, "LEFT": 0x25, "RIGHT": 0x27,
}


@dataclass(frozen=True)
class HotkeySpec:
    label: str
    modifiers: int
    key: int
    release_keys: tuple[int, ...]


def parse_hotkey(value: str) -> HotkeySpec:
    parts = [_ALIASES.get(part.strip().upper(), part.strip().upper()) for part in value.split("+")]
    if not parts or any(not part for part in parts):
        raise ValueError("快捷键格式示例：Ctrl+Shift+X")
    modifiers = set(part for part in parts if part in _MODIFIERS)
    keys = [part for part in parts if part not in _MODIFIERS]
    if len(keys) != 1 or len(modifiers) + 1 != len(parts):
        raise ValueError("快捷键需要一个普通按键和不重复的修饰键，例如 Ctrl+Shift+X")
    if not modifiers or not ({"CTRL", "ALT", "WIN"} & modifiers):
        raise ValueError("快捷键必须包含 Ctrl、Alt 或 Win，避免与普通输入冲突")
    target = keys[0]
    if len(target) == 1 and ("A" <= target <= "Z" or "0" <= target <= "9"):
        vk = ord(target)
    elif target in _SPECIAL:
        vk = _SPECIAL[target]
    elif target.startswith("F") and target[1:].isdigit() and 1 <= int(target[1:]) <= 12:
        vk = 0x6F + int(target[1:])
    else:
        raise ValueError(f"不支持的按键：{target}；支持字母、数字、F1-F12 和常用功能键")
    ordered = [name for name in ("CTRL", "ALT", "SHIFT", "WIN") if name in modifiers]
    mask = sum(_MODIFIERS[name][0] for name in ordered)
    release = tuple(_MODIFIERS[name][1] for name in ordered) + (vk,)
    label = "+".join(name.title() for name in ordered) + "+" + target
    return HotkeySpec(label, mask | MOD_NOREPEAT, vk, release)


def validate_hotkeys(automatic: str, clipboard: str) -> tuple[HotkeySpec, HotkeySpec]:
    first, second = parse_hotkey(automatic), parse_hotkey(clipboard)
    if (first.modifiers, first.key) == (second.modifiers, second.key):
        raise ValueError("自动翻译和剪贴板快捷键不能相同")
    return first, second
