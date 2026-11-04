"""Store the API Key in the Windows Credential Manager, never in a JSON file."""

from __future__ import annotations

import sys


SERVICE = "SelTranslate.ChatCompletions"
ACCOUNT = "api-key"


class SecretStorageError(RuntimeError):
    """Credential vault is unavailable; never silently fall back to plaintext."""


def _vault():
    if sys.platform != "win32":
        raise SecretStorageError("密钥存储需要 Windows 凭据管理器。")
    try:
        import keyring
        from keyring.backends.Windows import WinVaultKeyring

        # Never allow keyring config/plugins to pick a plaintext file backend.
        keyring.set_keyring(WinVaultKeyring())
        return keyring
    except Exception as exc:
        raise SecretStorageError("无法初始化 Windows 凭据管理器，请安装 keyring 和 pywin32。") from exc


def get_saved_api_key() -> str:
    try:
        return _vault().get_password(SERVICE, ACCOUNT) or ""
    except SecretStorageError:
        raise
    except Exception as exc:
        raise SecretStorageError("无法读取 Windows 凭据管理器中的 API Key。") from exc


def set_saved_api_key(value: str) -> None:
    if not value.strip():
        raise SecretStorageError("API Key 不能为空；清除密钥请使用专门的删除操作。")
    try:
        _vault().set_password(SERVICE, ACCOUNT, value.strip())
    except SecretStorageError:
        raise
    except Exception as exc:
        raise SecretStorageError("无法将 API Key 写入 Windows 凭据管理器。") from exc
