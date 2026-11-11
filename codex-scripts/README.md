# Codex 辅助工具

[返回项目索引](../README.md)

本目录提供 Codex 运行数据清理、任务完成桌面通知，以及 VS Code 扩展内置工具的启动器，分别支持 Ubuntu 与 Windows。

## 使用入口

| 功能 | 使用说明 | 脚本目录 |
| --- | --- | --- |
| 清理运行数据 | [清理范围与预览方法](./clean-all/README.md) | [Ubuntu](./clean-all/ubuntu/) / [Windows](./clean-all/windows/) |
| 桌面通知 | [依赖、配置与通知示例](./notify/README.md) | [Ubuntu](./notify/ubuntu/) / [Windows](./notify/windows/) |
| VS Code 扩展工具复用 | [安装启动器与 PATH 配置](./vsc-extension-tool/README.md) | [Ubuntu](./vsc-extension-tool/ubuntu/) / [Windows](./vsc-extension-tool/windows/) |

## 清理前预览

在本目录执行：

```bash
# Ubuntu：只预览，不删除
bash clean-all/ubuntu/clean.sh --dry-run
```

```powershell
# Windows：只预览，不删除
.\clean-all\windows\clean.ps1 -WhatIf
```

确认清理范围后，再按子目录说明执行实际清理。脚本会处理会话、缓存、快照、记忆和日志等运行数据，保留顶层 `auth.json` 与 `config.toml`。Ubuntu 默认目标为 `~/.codex`，可用 `CODEX_HOME` 覆盖；Windows 目标为 `%USERPROFILE%\.codex`。

## 通知与工具启动器

通知脚本路径分别为 `notify/ubuntu/notify.sh` 和 `notify/windows/notify.ps1`，配置示例见[通知说明](./notify/README.md)。

启动器复用已安装的 VS Code OpenAI 扩展中的可执行文件，使用前按[启动器说明](./vsc-extension-tool/README.md)设置命令入口与 PATH。
