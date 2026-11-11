# Python 项目骨架示例

[返回项目索引](../README.md)

提供一个 Flask 入口，以及独立的路径配置和日志模块，适合参考基本项目组织方式。

## 文件

| 文件 | 用途 |
| --- | --- |
| [app.py](./app.py) | 平台判断、导入路径设置和 Flask 服务入口 |
| [scripts/lib/config.py](./scripts/lib/config.py) | 将 `local_` 配置项转换为项目绝对路径 |
| [scripts/lib/log.py](./scripts/lib/log.py) | 控制台日志和按天轮转的文件日志 |

## 运行

当前 `app.py` 仅在 Windows 分支启动服务。在本目录的 PowerShell 中执行：

```powershell
python -m pip install flask
python app.py
```

访问 `http://127.0.0.1:5000/` 可看到 `Hello World!`。服务绑定 `0.0.0.0:5000`。

入口会把项目下的 `build/` 加入模块搜索路径，但本仓库未提供相应打包流程；当前首页也未引用配置或日志模块。`resources/` 是代码约定的模板和静态资源目录，需要使用资源时自行创建。Linux 等其他平台会输出不支持提示后退出。
