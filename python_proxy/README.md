# Python 代理转发示例

[返回项目索引](../README.md)

使用 aiohttp 将本地 `/defm/` 下的 HTTP 请求转发到指定目标，包含 SSE 流式响应处理和 WebSocket 转发代码。

## 启动服务

先修改 [server.py](./server.py) 中的 `TARGET`，设置实际目标地址，再在本目录执行：

```bash
python -m pip install aiohttp
python server.py
```

服务监听 `127.0.0.1:8000`。例如请求 `http://127.0.0.1:8000/defm/example`，HTTP 分支会移除 `defm/` 并转发到目标的 `/example` 路径，保留查询参数。

## 客户端示例

[client.py](./client.py) 使用 Azure OpenAI 客户端访问 `http://127.0.0.1:8000/defm`。按实际服务修改密钥、部署名和 API 版本后，在另一个终端执行：

```bash
python -m pip install openai httpx
python client.py
```

入口依次调用普通对话、流式对话和图像生成。不使用客户端出站代理时，保持 `proxy_url` 为空；代理分支的 `proxies` 参数需与安装的 httpx 版本匹配。

## 当前实现说明

- HTTP 分支会转发客户端请求头；源码中的服务端 `Authorization`、`api-key` 注入语句处于注释状态，单独修改 `APIKEY` 不会启用它们。
- WebSocket 分支目前会把 URL 中所有 `//` 替换为 `/`，也没有与 HTTP 分支相同的 `/defm/` 前缀移除逻辑。实际使用前需要修正该分支的 URL 拼接。
- 本项目是固定目标的转发示例，默认仅监听本机地址。
