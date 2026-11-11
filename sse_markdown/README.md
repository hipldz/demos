# SSE Markdown 增量渲染示例

[返回项目索引](../README.md)

使用 Vue 3、Vite 和 markdown-it 演示文本逐段到达时的 Markdown 渲染，包含代码高亮、复制和代码块更新逻辑。

## 运行

在本目录执行：

```bash
npm install
npm run dev
```

开发服务配置端口为 `8080`，访问地址以终端输出为准。在右侧输入 Markdown 并点击「开始模仿SSE」；留空时使用内置示例，左侧显示增量渲染结果。

## 实现入口

- [src/App.vue](./src/App.vue)：内容累积、渲染队列和页面交互。
- [src/module/server.js](./src/module/server.js)：在浏览器中随机切分文本，每段间隔约 20 ms，模拟流式输入；当前无需独立 SSE 后端。
- [src/module/markdown-it.js](./src/module/markdown-it.js)：Markdown 解析器及插件配置。
- [src/module/code-block.js](./src/module/code-block.js)：代码块构建与 DOM 更新。

接入实际 SSE 服务时，可参考 `enqueueRender` 将收到的文本片段送入渲染队列。`npm run build` 生成 `dist/`，`npm run preview` 预览构建结果。页面使用 Less 样式，当前依赖清单列有 `less-loader`；若 Vite 提示缺少 `less`，需补齐对应预处理器。

## 相关链接

- [在线预览](https://pldz1.com/io/markdown-sse)
- [掘金介绍](https://juejin.cn/post/7458656534718316595)
