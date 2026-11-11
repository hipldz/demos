# 清理 Codex 运行数据

> 最后更新：2026-08-18

本目录按平台提供清理脚本：

- `ubuntu/clean.sh`
- `windows/clean.ps1`

脚本会删除 Codex 的会话、缓存、快照、记忆、日志及顶层运行文件，同时保护 `auth.json` 和 `config.toml`。

## Ubuntu

```bash
chmod +x ubuntu/clean.sh
./ubuntu/clean.sh --dry-run   # 仅预览
./ubuntu/clean.sh             # 确认后执行
```

默认目标是 `~/.codex`；设置 `CODEX_HOME` 可指定其他目录。脚本会拒绝清理根目录或用户主目录。

## Windows

```powershell
.\windows\clean.ps1 -WhatIf   # 仅预览
.\windows\clean.ps1           # 确认后执行
```

Windows 目标固定为 `%USERPROFILE%\\.codex`。需要 PowerShell 的 `SupportsShouldProcess`（`-WhatIf`）支持。

## 清理范围

目录：`sessions`、`.tmp`、`tmp`、`shell_snapshots`、`memories`。顶层文件匹配 `log*`、`*.json`、`*.sqlite*`、`*.jsonl`、`*.log`，并额外处理 `cap_sid`、`.tmp`。
