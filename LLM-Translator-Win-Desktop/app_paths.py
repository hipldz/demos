"""Stable user-data paths, independent of the EXE/PyInstaller extraction folder."""

from __future__ import annotations

import os
from pathlib import Path


def user_data_dir() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        return root / "SelTranslate"
    return Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")) / "SelTranslate"


SETTINGS_PATH = user_data_dir() / "settings.json"  # Non-secret settings only.
