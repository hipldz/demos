# Ubuntu 辅助脚本

[返回项目索引](../README.md)

[ubuntu_hack.sh](./ubuntu_hack.sh) 提供电池、资源占用、屏幕和代理环境变量相关的辅助命令。在本目录使用 Bash 运行，每次选择一个选项。

| 命令 | 功能 | 依赖或条件 |
| --- | --- | --- |
| `bash ubuntu_hack.sh -b` | 显示电池电量 | `upower`，且存在电池设备 |
| `bash ubuntu_hack.sh -m` | 显示 CPU 和内存使用率 | `top`、`free` |
| `bash ubuntu_hack.sh -r` | 将屏幕向左旋转 | `xrandr`，适用的 X11 图形会话 |
| `bash ubuntu_hack.sh -s` | 请求解除屏保 | `gnome-screensaver-command`，相应桌面组件 |
| `bash ubuntu_hack.sh -p 127.0.0.1:7890` | 输出代理环境变量设置命令 | 可用的 HTTP 代理地址 |

`-p` 只打印 `export` 命令。需要复制输出中的这些命令并在当前终端执行，才会设置 HTTP、HTTPS、FTP 代理及本机地址例外。传入地址使用 `host:port` 格式。

无参数或参数不匹配时会显示帮助。屏幕相关选项依赖桌面环境，不适用于所有 Ubuntu 会话或无桌面的服务器。
