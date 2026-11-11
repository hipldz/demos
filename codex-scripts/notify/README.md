# Codex 任务完成通知

> 最后更新：2026-08-18

本目录提供接收 Codex 通知事件并显示桌面通知的脚本：

- Ubuntu：`ubuntu/notify.sh`（依赖 `notify-send` 和 Python 3）
- Windows：`windows/notify.ps1`（使用 Windows Forms）

## 配置

把脚本绝对路径写入用户级 `~/.codex/config.toml`（Windows 为 `%USERPROFILE%\\.codex\\config.toml`）：

```toml
# Ubuntu
notify = ["bash", "/absolute/path/to/codex-scripts/notify/ubuntu/notify.sh"]

# Windows（按平台选择其一）
notify = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", 'C:\path\to\codex-scripts\notify\windows\notify.ps1']
```

项目级 `.codex/config.toml` 不覆盖用户级 `notify` 配置。

## 手动测试

Ubuntu：

```bash
sudo apt install -y libnotify-bin python3
chmod +x ubuntu/notify.sh
./ubuntu/notify.sh '{"type":"agent-turn-complete","cwd":"/tmp/demo","last-assistant-message":"任务已经完成"}'
./ubuntu/notify.sh --title "My Codex" --duration 5000 "测试通知"
```

Windows：

```powershell
.\windows\notify.ps1 '{"type":"agent-turn-complete","cwd":"C:\\Temp\\demo","last-assistant-message":"任务已经完成"}'
```

`--duration`/`-Duration` 单位为毫秒。脚本支持 JSON 或普通文本，并会压缩过长内容。
