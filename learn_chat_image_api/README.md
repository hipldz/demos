# 对话与图像 API 示例

[返回项目索引](../README.md)

提供 OpenAI 与 Azure OpenAI 的 JavaScript、Python 调用示例，包含普通对话、流式对话和图像生成。

## 文件与配置

| 文件 | 服务 | 运行前需修改的变量 |
| --- | --- | --- |
| [openai_example.js](./openai_example.js) | OpenAI | `apiKey`、`proxyUrl`，以及请求中的模型名 |
| [azure_openai_example.js](./azure_openai_example.js) | Azure OpenAI | `endpoint`、`apiKey`、`chatDeployment`、`dellDelpoyment`、`proxyUrl` |
| [openai_example.py](./openai_example.py) | OpenAI | `api_key`、`proxy_url`，以及请求中的模型名 |
| [azure_openai_example.py](./azure_openai_example.py) | Azure OpenAI | `azure_endpoint`、`api_key`、`chat_deployment`、`image_deployment`、`proxy_url` |

这些配置当前写在源码中；不使用代理时把代理地址设为空字符串。Azure 示例中的部署名、API 版本需与自己的资源匹配。示例使用的模型名和 API 版本是历史配置，运行前请按实际可用配置调整。不要提交填写了真实密钥的文件。

## JavaScript

在本目录安装依赖，选择一个示例运行：

```bash
npm install
node openai_example.js
# 或：node azure_openai_example.js
```

## Python

```bash
python -m pip install openai httpx
python openai_example.py
# 或：python azure_openai_example.py
```

Python 代理分支使用 `httpx.Client(proxies=...)` 写法；启用代理时需检查所安装的 httpx 版本是否支持该参数，必要时调整代码。

每个示例的入口都会依次调用普通对话、流式对话和图像生成。只体验某一项时，先调整入口中的调用列表；图像示例输出图片 URL。
