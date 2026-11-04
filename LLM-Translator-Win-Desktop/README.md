# LLM Translator

Windows 10 / 11 常驻系统托盘的选中文本处理工具。通过 **Ctrl+Shift+X** 将当前选区发送到 OpenAI 兼容 **Chat Completions API**，按选中的 Prompt 处理文字，并选择**替换原文**或**悬浮显示**。

这是 **Windows Python 源码项目**。可直接 `python app.py` 运行，也可在 Windows 构建单文件 `LLM Translator.exe`。内部配置目录和凭据服务暂保持 `SelTranslate`，以免更名影响已保存的 API Key。

主要功能：

- **浅色与深色主题**：在窗口右上角、设置页或托盘面板切换，立即生效并记住选择；太阳/月亮为独立 SVG 图标。
- **简洁选择器**：Prompt 使用独立按钮和菜单弹层；只有两项选择的输出、写回和主题改为直接切换的分段控件，不依赖原生 `QComboBox` 弹窗。
- **实时状态**：蓝色（就绪）、橙色（处理中）、绿色（成功）、红色（失败）、灰色（暂停）。托盘图标颜色会随阶段改变；右键弹出自绘面板，查看状态和快捷设置。
- **后台通知**：程序隐藏到托盘后，处理完成/失败可显示 Windows 通知；可在设置中关闭。
- **Prompt 模式**：默认只内置「中英互译」与「学术润色」。可新增、复制、编辑、删除，并从概览或托盘菜单切换当前模式；语言方向和处理风格完全由 Prompt 决定。
- **翻译**：独立的「翻译」页面拥有自己的输入、执行与结果，使用当前 Prompt 获取结果；不会读取或修改外部应用选区。两个文本框会随窗口高度伸缩，空间不足时页面可滚动。
- **概览与历史**：概览提供快捷设置与最近记录，点击历史仅更新右侧只读详情，不覆盖翻译页的内容。记录只保存在内存中，关闭后清空。
- **稳定触发**：独立热键线程和翻译工作线程；读取选区前先等待快捷键全部松开，网页复制失败时进行一次内部重试。正在执行时不对旧选区排队发起新请求。
- **两种输出方式**：替换原文（通过 Ctrl+V/Unicode）；悬浮结果卡片（可拖动标题、复制结果，且记住本次运行中拖动的位置）。可以在概览、设置或托盘面板切换。
- **系统凭据保护**：API Key 放在 Windows 凭据管理器；`settings.json` 只包含普通设置，不保存明文 Key。

品牌图标为参考图描绘的**透明背景「中 / A」线性矢量标记**，无底板或同步箭头。浅色界面使用黑色 `brand.svg`，深色界面使用白色 `brand-dark.svg`；**状态图标则使用同形状的白色字形及彩色圆角底板**，蓝色就绪、绿色成功、橙色处理中、红色错误、灰色暂停。托盘与主窗口任务栏图标会同步显示当前状态。功能标签保持单行，当前 Prompt 名称超长时用省略号截断，完整名称仍可通过鼠标悬停查看。悬浮结果窗口的拖动区域在全部控件初始化后才注册事件过滤器，避免启动阶段的属性访问错误。

## 快速安装

1. Windows 10 / 11 安装 Python **3.10+**，确保 `python` 或 `py` 能在 PowerShell 中运行。
2. 下载本仓库或解压源码 ZIP 到固定目录，进入 `LLM-Translator-Win-Desktop` 文件夹。
3. 在 PowerShell 中安装依赖：

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. 启动图形应用：

   ```powershell
   python app.py
   ```

5. 打开「设置」，填写自己的 **API Key / Base URL / Model**，点击保存。密钥会进入 Windows 凭据管理器。
6. 在「概览」选择翻译模式；在 Edge、Firefox、Word 等应用中选中文字，按 **Ctrl+Shift+X**。

要静默隐藏到托盘启动：

```powershell
pythonw app.py --minimized
```

窗口右上角关闭按钮默认隐藏到系统托盘；右键托盘图标选择「退出」才能真正退出。需要开机自启时，可自行创建指向 `pythonw.exe` 并传入 `app.py --minimized` 的快捷方式，放入 Windows 启动文件夹（`Win+R` → `shell:startup`）。

## 打包为单文件 EXE（在 Windows 上执行）

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m pip install pyinstaller pillow
py -3 build_exe.py
```

构建结果位于 `dist\LLM Translator.exe`，可直接双击运行，**目标电脑不必另装 Python**。程序不会把 API Key、个人设置或日志打进 EXE。资源文件 `assets/*.svg` 会随 EXE 打包，图标由 `brand.svg` 生成 Windows ICO。`build_exe.py` 只在 Windows 构建 Windows EXE：PyInstaller 不是跨系统交叉编译器。

注意：单文件程序首次启动需要解包内部资源，可能比直接运行 `.py` 略慢。请使用普通用户权限运行，不要随意“以管理员身份运行”。

## API Key 和配置存储

- **API Key**：保存在当前 Windows 用户的**凭据管理器**，服务名 `SelTranslate.ChatCompletions`，不会写入 JSON 或打包进 EXE。设置页面的密码框留空表示保持已经保存的密钥。
- **普通设置**：保存在 `%LOCALAPPDATA%\SelTranslate\settings.json`，只包含 Base URL、模型、快捷键、Prompt、输出方式等非敏感选项，更新 EXE 不会清除。
- **环境变量**：`SELECT_TRANSLATOR_API_KEY` 可临时覆盖凭据管理器中的密钥。不要把真实 Key 写进源码、启动参数、版本库或共享压缩包。
- **开发版配置**：当前配置版本为 `2`。从无版本号的旧配置启动时，Prompt 列表会直接重置为新版两项预设，不迁移旧版四个内置模式或用户自定义的旧模式；其他非敏感设置仍可沿用。请先备份希望保留的自定义 Prompt。旧 `config.json` 不再迁移，且 `settings.json` 不允许出现明文 `api_key`。

Windows 凭据管理器不是不可提取的硬件保险箱：在同一个 Windows 用户权限下运行的恶意程序仍可能读取应用使用的凭据。请不要在不受信任的电脑上保存生产环境 Key。

## 输出方式

| 模式 | 行为 | 适用场景 |
|---|---|---|
| **替换原文**（默认） | 等待翻译，验证目标窗口和原选区仍然有效，再原位写入 | `input`、`textarea`、Word 等编辑控件 |
| **悬浮显示** | 弹出置顶的可关闭结果卡片；保留原文，不向编辑器发粘贴指令 | 查词、阅读网页、只看翻译或润色候选 |

在**概览的“输出”**、**设置**或**托盘右键面板**里切换。悬浮卡片可按住标题栏拖动、点击“复制”或关闭，后续结果沿用拖动后的位置。悬浮模式的处理阶段可以切换窗口，结果仍会显示；替换模式则需要保持原选区不变。

### 翻译页面

进入侧边栏的「翻译」，在「输入」文本框键入或粘贴文字，点击「执行」。程序会使用当前 Prompt 和 API 配置，在后台生成「结果」，并将本次处理加入概览中的最近记录。历史详情和翻译输入分开存储，查看历史不会覆盖尚未处理的文字。这个操作与全局热键共享同一任务队列，但**不会读取系统选区、模拟粘贴或更改外部应用内容**。即使当前输出方式为「替换原文」，手动执行也只在应用内展示结果。

### 界面主题

窗口右上角的太阳/月亮按钮、「设置 → 外观」和托盘面板均可切换浅色/深色界面。应用内状态文字靠左，主题按钮靠右。更改后立即生效，并保存到 `settings.json` 中的 `theme` 字段。悬浮结果窗口也会同步切换主题。Windows 11 原生标题栏使用 DWM 属性匹配主题，旧版 Windows 采取兼容回退。窗口图标始终是品牌 SVG；仅系统托盘的彩色底板随忙碌、成功等状态改变。

> 首次启动如显示“快捷键被占用”，请关闭仍在运行的旧版本进程，或在「设置」修改快捷键。新版 GUI 只保留 **一个** 自动处理快捷键，已删除原来的手动 `Ctrl+C → 热键 → Ctrl+V` 模式。

## Prompt 模式

进入「Prompt」页，可以：

1. 选择一个内置模式并编辑名称和系统 Prompt，点击「保存 Prompt」。
2. 点击「＋ 新建模式」创建新 Prompt，或「复制模式」基于现有配置修改。
3. 点击「设为当前模式」，或直接在概览的下拉框、托盘右键菜单中选择。

Prompt 的内容将原样作为 Chat Completions 的 **system** 消息；选中的原文作为单独的 **user** 消息。无需在 Prompt 中写 `{text}`。程序不再设置目标语言，也不再替换 `{target_language}` 占位符。

首次安装的两条预设 Prompt 原文：

- **中英互译**：你是一名顶级的专业翻译家，擅长精准、地道地进行中英互译。请将下面内容翻译成另一种语言。在翻译过程中，严格保持原文的含义、语气和风格，**仅输出翻译结果，无需添加任何解释或评论**
- **学术润色**：你是一位专业的文档编辑专家，请根据原文语言，将其润色为**专业、严谨且流畅的官方文档或正式商业文本风格**。在润色时，务必保持原文的核心事实和技术术语不变。**仅输出翻译结果，无需添加任何解释或评论**：

例如，学术润色 Prompt 可以写成：

```text
Polish the text into natural academic English for a microbiology manuscript.
Preserve experimental details, species names, units, numerical results,
citations and factual meaning. Do not invent findings. Return only the edited text.
```

后续按 **Ctrl+Shift+X** 就会用当前模式处理选区。所有模式保存在用户目录的 `settings.json`，修改后下次运行仍然可用。**翻译开始时会固定本次 Prompt 和输出方式**，所以请求过程中切换模式只影响下一次触发。

## API 连接

- **Base URL**：如 `https://api.openai.com/v1`，会自动附加 `/chat/completions`；若已包含完整 Chat Completions 路径则不重复追加。
- **Model**：输入提供商支持 Chat Completions 的模型 ID，例如 `gpt-4o-mini`。
- **API Key**：在界面的密码框里填写；也可以通过环境变量 `SELECT_TRANSLATOR_API_KEY` 提供（环境变量优先）。
- **处理意图**：由当前 Prompt 控制，设置页只负责输出方式、写回实现、超时和长度限制。
- **超时**：默认 30 秒，范围 1–120 秒；与连续快捷键按下之间没有人为冷却期。
- **自动写回**：`paste` 通过内部模拟 Ctrl+V 写回，`type` 通过 Unicode 输入事件写回。即使手动剪贴板**模式已经删除**，底层仍会在必要时通过 Ctrl+C 获取浏览器选区。

在「设置」保存后生成非敏感 `settings.json`；API Key 不存入该文件。Prompt 仍是普通文本，若其中包含隐私信息请不要随意共享。远程 Base URL 强制 HTTPS；仅 localhost 允许 HTTP。分发包不包含个人密钥和设置。

## Windows 系统托盘

| 托盘颜色 | 状态 |
|---|---|
| 蓝色 | 空闲，监听已开启 |
| 橙色 | 正在读取、调用 API 或回填 |
| 绿色 | 最近一次处理成功 |
| 红色 | 最近一次处理失败 |
| 灰色 | 已暂停，不接收新任务 |

右键托盘图标打开应用自己的轻量面板：直接选择 Prompt、输出方式与外观，或暂停/恢复、打开窗口、退出。托盘系统通知受 Windows 通知设置及“勿扰”模式影响，因此更可靠的状态来源是**托盘图标颜色和右键面板**。

## Edge / Firefox 与安全限制

1. 先通过 UI Automation 读取选区；如果控件不支持，则程序**内部**模拟 Ctrl+C 读取纯文本。
2. 发送到用户配置的 API；接收结果后再检查前台窗口、输入焦点和可获得的选区是否发生变化。
3. 只有在仍认为原选区有效时才尝试写回；窗口/选区改变则中止替换。

自动模式依赖目标应用的 Windows 选区行为，不能保证所有自定义编辑器、网页富文本控件都能兼容。尤其是请求期间不要切换窗口、移动光标或修改文字。模拟复制/粘贴会暂时使用剪贴板，尽力恢复原纯文本，但无法保证恢复原有图片、HTML 等剪贴板格式。普通权限程序无法向某些管理员权限窗口模拟输入。

**连续全选/翻译**：支持在同一个 `textarea` 里反复执行 `Ctrl+A`、`Ctrl+Shift+X`。新版会等到完整组合键松开后再查询选区；若浏览器第一次没有响应模拟复制，会在确保窗口/输入焦点未变化时重试一次。如果仍然失败，界面会分别提示“模拟复制未更新剪贴板”“剪贴板已变化但无法读取文本”或“焦点改变”，方便进一步定位。**不需要在两次成功翻译之间人为等待**；但上一条翻译仍在进行时，程序会明确跳过新请求，避免覆盖错误文本。

**隐私提醒**：触发快捷键会把选中的文本发送给你配置的 API 服务商，请勿处理密码、密钥或不得上传的资料。旧的命令行 `main.py` 仍可能在本地写调试日志；新版 `app.py` 的会话文本不主动写盘。

## 源码结构与开发

主要模块：

- `app.py`：现代化 PyQt5 GUI 和会话历史。
- `vector_icons.py` 与 `assets/*.svg`：界面矢量图标和动态托盘图标。
- `hotkeys.py`：可配置快捷键组合的解析与校验。
- `modes.py`：预置模式、新建模式及 Prompt 校验。
- `desktop.py`：Windows 全局热键线程和后台翻译工作线程。
- `settings_store.py`：非敏感 JSON 设置及版本化 Prompt 默认值。
- `translator.py`：OpenAI 兼容 Chat Completions 请求。
- `main.py`：Windows UI Automation、剪贴板和原位替换底层逻辑（也能单独启动旧版命令行）。
- `floating_result.py`：独立的悬浮结果卡片，不自动激活原应用。
- `secret_store.py`：通过 keyring 调用 Windows 凭据管理器保存、读取 API Key。
- `app_paths.py`：确定用户配置目录。
- `build_exe.py`：PyInstaller 单文件 EXE 构建脚本。
- `settings.example.json`：**不含密钥**的非敏感设置示例；实际设置由 GUI 生成到用户目录。
- `requirements.txt`：PyQt5 和 UI Automation 依赖。
- `tests/test_core.py`：Prompt、配置、请求构造及部分界面结构的自动化检查。

源码直接运行，无需构建或安装 Python 包。可先进行基本的 Python 语法检查：

```powershell
python -m compileall -q app.py main.py desktop.py translator.py modes.py hotkeys.py settings_store.py vector_icons.py
```

随后在 **Windows 交互式桌面**中测试 Edge/Firefox 普通 `textarea`：输入文字，连续多次执行 `Ctrl+A → Ctrl+Shift+X`（每次等待翻译完成）。如果失败，请记录 GUI 显示的是“复制超时”“剪贴板不可读”还是“焦点改变”，以便定位。源码附带 `tests/test_core.py`，但真实浏览器兼容性仍需要在 Windows 本机验证。
