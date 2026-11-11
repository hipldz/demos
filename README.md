# PLDZ Demos

这个仓库用于集中存放一些独立的小项目 Demo，涵盖 AI Agent、开发辅助工具、代理服务、前端、Python 和 C/C++。各项目独立维护，依赖安装和运行命令均在对应目录中执行。

## 项目索引

| 目录 | 类型 | 简介 | 使用说明 |
| --- | --- | --- | --- |
| [ai-agent](./ai-agent/) | Node.js | 单 Agent 架构 Demo，包含 Router/Executor/Tools 分层，支持聊天、搜索、推理、图像生成与理解 | [README](./ai-agent/README.md) |
| [codex-scripts](./codex-scripts/) | Bash + PowerShell | Codex 运行数据清理、任务完成桌面通知，以及 VS Code 扩展内置工具的启动器，支持 Ubuntu 与 Windows | [README](./codex-scripts/README.md) |
| [pi-port-proxy](./pi-port-proxy/) | TypeScript + Node.js | 本地端口反向代理与 Pi 扩展，提供管理面板、显式代理管理和端口发现，支持 WSL2、Linux 与 Termux | [README](./pi-port-proxy/README.md) |
| [pproxy-manager](./pproxy-manager/) | Python + aiohttp | `pproxy` 管理面板，支持规则管理、日志查询、状态监控与黑名单配置 | [README](./pproxy-manager/README.md) |
| [git-remote-rewriter](./git-remote-rewriter/) | Bash | 批量修改当前目录下一层 Git 仓库中 GitHub Remote 的用户名或认证前缀 | [README](./git-remote-rewriter/README.md) |
| [sse_markdown](./sse_markdown/) | Vue 3 + Vite | 在页面中动态增量渲染 Markdown（配合 SSE 场景） | [README](./sse_markdown/README.md) |
| [learn_chat_image_api](./learn_chat_image_api/) | JS + Python | OpenAI/Azure OpenAI 的对话与图像 API 调用示例 | [README](./learn_chat_image_api/README.md) |
| [python_proxy](./python_proxy/) | Python + aiohttp | HTTP、SSE 与 WebSocket 代理转发示例 | [README](./python_proxy/README.md) |
| [ubuntu_hack](./ubuntu_hack/) | Bash | Ubuntu 常用辅助脚本（电池、资源、旋转屏幕、代理） | [README](./ubuntu_hack/README.md) |
| [cmake_tutorial](./cmake_tutorial/) | C + CMake | CMake 入门示例（单工程与多子目录工程） | [README](./cmake_tutorial/README.md) |
| [create_a_python_project](./create_a_python_project/) | Python + Flask | Python 项目骨架示例，含配置和日志模块；当前入口仅支持 Windows | [README](./create_a_python_project/README.md) |
| [vue3-static-blog-template-a](./vue3-static-blog-template-a/) | Vue 3（Vue CLI） | 静态博客模板 A，含文章资源同步/加密脚本 | [README](./vue3-static-blog-template-a/README.md) |
| [vue3-static-blog-template-b](./vue3-static-blog-template-b/) | Vue 3 + Vite | 静态博客模板 B（Vite 版本），含资源同步/加密脚本 | [README](./vue3-static-blog-template-b/README.md) |

## 使用方式

上表的目录链接用于浏览源码，「使用说明」直接打开对应项目的 README。请先阅读各项目的依赖、配置和运行步骤，再进入相应目录执行命令。

- Codex 工具可直接查看[清理说明](./codex-scripts/clean-all/README.md)、[通知配置](./codex-scripts/notify/README.md)和[扩展工具启动器](./codex-scripts/vsc-extension-tool/README.md)。
- AI/API 示例需要先配置服务地址、密钥和模型；各项目的配置方式见对应 README。
- 仓库没有统一的安装、启动或构建命令。

## 预览与相关文章

- `sse_markdown`：[预览](https://pldz1.com/io/markdown-sse) | [掘金](https://juejin.cn/post/7458656534718316595)
- `learn_chat_image_api`：[CSDN](https://blog.csdn.net/qq_42727752/article/details/145082786) | [掘金](https://juejin.cn/post/7458496437614788646)
- `ubuntu_hack`：[CSDN](https://blog.csdn.net/qq_42727752/article/details/145044058) | [掘金](https://juejin.cn/post/7457811062940434447)

## 其他

- [GitHub 仓库](https://github.com/hipldz/demos)
- [个人主页](https://pldz1.com)
