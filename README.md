# PLDZ Demos

这个仓库用于集中存放一些独立的小项目 Demo，涵盖 AI、前端、Python、C/C++ 和脚本工具。

## 项目索引

| 目录 | 类型 | 简介 |
| --- | --- | --- |
| `ai-agent` | Node.js | 单 Agent 架构 Demo，包含 Router/Executor/Tools 分层，多模态能力（聊天、搜索、推理、图像） |
| [LLM-Translator-Win-Desktop](./LLM-Translator-Win-Desktop/) | Python + PyQt5（Windows） | 常驻托盘的 LLM 文本处理工具，支持快捷键选区翻译、自定义 Prompt、原文替换和悬浮结果 |
| `pproxy-manager` | Python + aiohttp | `pproxy` 管理面板，支持规则管理、日志查询、状态监控 |
| `git-remote-rewriter` | Bash | 批量修改当前目录下一层 Git 仓库中 GitHub Remote 的用户名或认证前缀 |
| `sse_markdown` | Vue 3 + Vite | 在页面中动态增量渲染 Markdown（配合 SSE 场景） |
| `learn_chat_image_api` | JS + Python | OpenAI/Azure OpenAI 的对话与图像 API 调用示例 |
| `python_proxy` | Python + aiohttp | 简单 HTTP/WebSocket 代理转发服务 |
| `ubuntu_hack` | Bash | Ubuntu 常用辅助脚本（电池、资源、旋转屏幕、代理） |
| `cmake_tutorial` | C + CMake | CMake 入门示例（单工程与多子目录工程） |
| `create_a_python_project` | Python + Flask | Python 项目骨架示例（含配置和日志模块） |
| `vue3-static-blog-template-a` | Vue 3（Vue CLI） | 静态博客模板 A，含文章资源同步/加密脚本 |
| `vue3-static-blog-template-b` | Vue 3 + Vite | 静态博客模板 B（Vite 版本），含资源同步/加密脚本 |

## 快速开始

按需进入对应目录运行：

- Node.js / 前端项目：`npm install` 后执行 `npm run dev` / `npm run serve`
- Python 项目：`pip install -r requirements.txt` 后执行 `python xxx.py`
- CMake 示例：在项目目录执行 `cmake -S . -B build && cmake --build build`
- Bash 工具：先执行 `chmod +x xxx.sh`，再按项目 README 中的说明运行

### Windows 桌面翻译工具

`LLM-Translator-Win-Desktop` 需要 Windows 10 / 11 和 Python 3.10+。在 PowerShell 中执行：

```powershell
cd LLM-Translator-Win-Desktop
python -m pip install -r requirements.txt
python app.py
```

启动后在「设置」填写 API Key、Base URL 和模型，选择 Prompt，在其他应用中选中文字并按 `Ctrl+Shift+X`。支持 OpenAI 兼容 Chat Completions API；API Key 保存在 Windows 凭据管理器中。详细功能、配置和 EXE 打包步骤见[项目 README](./LLM-Translator-Win-Desktop/README.md)。

## 重点项目链接

- `LLM-Translator-Win-Desktop`: [源码与使用说明](./LLM-Translator-Win-Desktop/README.md)
- `sse_markdown`: [源码](https://github.com/pldz1/demos/tree/main/sse_markdown) | [预览](https://pldz1.com/io/markdown-sse) | [掘金](https://juejin.cn/post/7458656534718316595)
- `learn_chat_image_api`: [源码](https://github.com/pldz1/demos/tree/main/learn_chat_image_api) | [CSDN](https://blog.csdn.net/qq_42727752/article/details/145082786) | [掘金](https://juejin.cn/post/7458496437614788646)
- `python_proxy`: [源码](https://github.com/pldz1/demos/tree/main/python_proxy)
- `ubuntu_hack`: [源码](https://github.com/pldz1/demos/tree/main/ubuntu_hack) | [CSDN](https://blog.csdn.net/qq_42727752/article/details/145044058) | [掘金](https://juejin.cn/post/7457811062940434447)
- `cmake_tutorial`: [源码](https://github.com/pldz1/demos/tree/main/cmake_tutorial)
- `pproxy-manager`: [源码](https://github.com/pldz1/demos/tree/main/pproxy-manager)
- `ai-agent`: [源码](https://github.com/pldz1/demos/tree/main/ai-agent)
- `git-remote-rewriter`: [源码](https://github.com/pldz1/demos/tree/main/git-remote-rewriter)

## 其他

- 个人主页: https://pldz1.com
