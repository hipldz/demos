# 从 VS Code 扩展使用 Codex 工具

> 最后更新：2026-08-18

## 为什么需要这个目录？

VS Code 里的 Codex 插件和单独安装的 Codex 使用的是同一套 Codex 工具。插件安装后，相关可执行文件已经放在 VS Code 扩展目录中；本目录提供几个轻量启动器，让你可以直接在终端使用插件自带的版本，不需要再下载或安装一份独立副本。

这样做适合希望节省磁盘空间、统一插件版本，或在终端与 VS Code 之间使用同一套工具的用户。启动器每次运行时会查找已安装的 OpenAI ChatGPT VS Code 扩展，并优先使用最新的扩展目录。

前提是已经安装 VS Code 的 OpenAI ChatGPT/Codex 扩展。扩展升级后，启动器会自动重新查找新版本；如果扩展被卸载或目录位置不同，启动器会提示找不到对应的可执行文件。

## Ubuntu / WSL

Ubuntu 启动器位于 `ubuntu/openai-vscode-tool`。仓库中只保留这一个启动器，不再保存 `codex`、`rg` 等软链接；它会按以下顺序查找扩展：

1. `~/.vscode/extensions`

### 安装启动器

在仓库根目录执行：

```bash
mkdir -p "$HOME/.local/bin" "$HOME/.local/libexec"
install -m 755 vsc-extension-tool/ubuntu/openai-vscode-tool \
  "$HOME/.local/libexec/openai-vscode-tool"

ln -sfn ../libexec/openai-vscode-tool "$HOME/.local/bin/codex"
ln -sfn ../libexec/openai-vscode-tool "$HOME/.local/bin/rg"
ln -sfn ../libexec/openai-vscode-tool "$HOME/.local/bin/codex-code-mode-host"
```

上面的 `ln -sfn` 会在用户自己的 `~/.local/bin` 中创建或更新三个命令入口，不会修改仓库目录，也不会把扩展里的可执行文件复制出来。若这些入口已经存在，命令会将它们指向当前安装的启动器。

启动器必须通过这些名称调用，因为它会根据 `$0` 的文件名决定要启动扩展里的 `codex`、`rg` 或 `codex-code-mode-host`。

### 加入 PATH

当前终端临时生效：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

希望以后每次登录都生效，可写入 `~/.profile`（bash 用户也可以写入 `~/.bashrc`）：

```bash
printf '%s\n' 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.profile"
source "$HOME/.profile"
```

检查是否生效：

```bash
command -v codex
codex --version
rg --version
```

## Windows

Windows 用户不需要创建硬链接或符号链接；本目录已经提供 `.bat` 启动器。它们会在 `%USERPROFILE%\.vscode\extensions` 下查找最新的 `openai.chatgpt-*-win32-x64` 扩展目录。

可用命令如下：

| 文件 | 调用的扩展工具 |
| --- | --- |
| `codex.bat` | `codex.exe` |
| `rg.bat` | `rg.exe` |
| `codex-command-runner.bat` | `codex-command-runner.exe` |
| `codex-windows-sandbox-setup.bat` | `codex-windows-sandbox-setup.exe` |

### 推荐安装位置

建议把这些 `.bat` 文件复制到用户目录下的 `.local/bin`：

```powershell
$bin = Join-Path $env:USERPROFILE '.local\bin'
New-Item -ItemType Directory -Force -Path $bin | Out-Null
Copy-Item .\vsc-extension-tool\windows\*.bat $bin -Force
```

然后把该目录加入当前用户的 PATH：

```powershell
$bin = Join-Path $env:USERPROFILE '.local\bin'
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (($userPath -split ';') -notcontains $bin) {
    $newPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $bin } else { "$userPath;$bin" }
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
}
$env:Path = "$bin;$env:Path"
```

已打开的终端或 VS Code 终端通常不会自动读取新的用户 PATH；请关闭并重新打开终端（必要时重启 VS Code）。之后可以直接运行：

```powershell
codex.bat --version
rg.bat --version
```

如果希望不带 `.bat` 后缀调用，Windows 的命令解析通常可以直接使用 `codex` 和 `rg`；若当前 shell 未自动补全扩展名，则使用 `codex.bat`、`rg.bat`。

## 故障排查

- 提示找不到可执行文件：确认 VS Code 的 OpenAI ChatGPT/Codex 扩展已安装，并检查启动器搜索的扩展目录。
- Ubuntu/WSL 找不到扩展：确认扩展安装在当前 WSL 用户下的 `~/.vscode/extensions` 或者其他PATH，而不是只安装在 Windows 端。
- Windows 找不到扩展：确认扩展目录位于 `%USERPROFILE%\.vscode\extensions`，且目录名匹配 `openai.chatgpt-*-win32-x64`。
- 命令仍指向旧版本：重新打开终端后再检查 `command -v codex`（Ubuntu）或 `Get-Command codex`（Windows），并确认 PATH 中没有更靠前的同名命令。
