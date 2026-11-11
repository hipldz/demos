# 🌐 Vue3 静态个人主页网站项目 - A

[返回项目索引](../README.md)

> 本项目的部分内容参考了 [KilaKila-Blog](https://github.com/zhiyiYo/KilaKila-Blog) 的设计和实现。

## 📖 项目简介

这是一个基于 Vue3 的项目, 用于部署静态的个人主页网站。

项目的预览地址: [vue3-static-blog-template-a](https://pldz1.com/io/vue3-static-blog-template-a)

## 🛠️ 技术要求

- **Node.js 版本支持**：
  - 推荐使用 **Node.js 16**。
  - 本项目对 Node.js **17 及以上版本**, 需要额外设置环境变量:
    - windows: `set NODE_OPTIONS=--openssl-legacy-provider`
    - linux: `export NODE_OPTIONS=--openssl-legacy-provider`

---

## 📂 项目结构

以下是项目的文件夹结构说明：

```
├── _blogs/              # 存放博客的 markdown 资源
├── _pics/               # 存放博客的图像资源
├── dist/                # 个人网站部署文件夹
├── public/              # 公共资源文件夹
│   ├── _blogs/          # 存放博客内容的文件夹, 脚本会帮助从 resources/ 下同步并且加密过来
│   ├── _pics/           # 存放博客的图像资源, 脚本会帮助从 resources/ 下同步并且加密过来
│   ├── _lib/            # 库文件夹
|   ├── all.blog.json    # 博客元数据文件, 脚本会帮助从 public/all.blog.json 下同步并且加密过来
│   ├── avatar.png       # 默认头像图片
│   ├── favicon.ico      # 网站图标
│   └── index.html       # 网站入口 HTML
├── src/                 # 项目源码
├── .env                 # 环境变量和用户信息的配置文件
```

---

## ⚙️ 环境变量配置

项目中的 `.env` 文件包含以下配置项, 用于设置网站的基本信息和功能：

| 变量名                          | 说明                                                 |
| ------------------------------- | ---------------------------------------------------- |
| `VUE_APP_WEBSITE_NAME`          | 网站的显示名字                                       |
| `VUE_APP_WEB_START_TIME`        | 网站的启动时间                                       |
| `VUE_APP_WEBSITE_AUTHOR_GITHUB` | 网站作者的 GitHub 链接                               |
| `VUE_APP_WEBSITE_AUTHOR_CSDN`   | 网站作者的 CSDN 链接                                 |
| `VUE_APP_WEBSITE_AUTHOR_JUEJIN` | 网站作者的稀土掘金链接                               |
| `VUE_APP_ENCRYPT_SOURCE`        | 是否对网站的一些源文件信息进行简单加密               |
| `VUE_APP_SECRET_KEY`            | 加密和解密使用的密钥（32 字节, 符合 AES-256 的要求） |
| `VUE_APP_ALGORITHM`             | 使用的加密算法（例如 `aes-256-cbc`）                 |

---

## 🚀 快速开始

### 📂 编写博客内容

1. **博客文件夹位置**：在项目的 `_blogs` 文件夹下编写博客内容。
2. **文件夹结构**：
   - `_blogs` 下的各个文件夹表示博客分类（`category`）。
   - 每篇博客使用 **Markdown 文件**格式, 并支持设置参数。

### 📋 Markdown 参数说明

每篇博客的 Markdown 文件需要包含以下基本参数：

| 参数名      | 说明                 | 示例                      |
| ----------- | -------------------- | ------------------------- |
| `title`     | 博客名字             | `1 Docker 基本指令`       |
| `category`  | 博客分类             | `Docker`                  |
| `serialNo`  | 博客序号             | `1`                       |
| `tags`      | 博客标签             | `[Docker, 学习笔记]`      |
| `date`      | 博客时间（`/` 格式） | `2025/1/1`                |
| `thumbnail` | 缩略图位置           | `./default_thumbnail.png` |
| `summary`   | 摘要                 | `无`                      |

### ✍️ 示例 Markdown 文件

以下是一个完整的 Markdown 文件示例：

```markdown
---
title: 1 Docker 基本指令
category: Docker
serialNo: 1
tags: [Docker, 学习笔记]
date: 2025/1/1
thumbnail: ./default_thumbnail.png
summary: 无
---

# 1.1 安装 docker

# 1.2 docker 安装并配置 ubuntu20

1. 拉取 docker 镜像：`sudo docker pull ubuntu:20.04`

2. 启动镜像： `docker run --rm -it --network=host ubuntu:20.04`
```

---

## 📝 运行项目

1. 确保安装了推荐版本的 Node.js（Node 16）。
2. 执行以下命令：

```bash
# 安装依赖
npm install

# 启动项目
npm run serve

# 打包静态网页
npm run build
```

3. 项目将在本地运行, 并可以通过浏览器访问。

4. 可以单独测试的脚本有：

```bash
# 查看列出的 all.blog.json 数据
node src/scripts/update.js

# (是否) 加密文件到 public 目录
node src/scripts/encrypt.js

# 部署为 git page 的额外操作
node src/scripts/deploy.js
```

---

## 💡 提示

- 请根据自己的需求调整 `_blogs` 目录结构和内容。
- 如果遇到问题, 可以通过调整 Node.js 版本来解决兼容性问题。

## 🚀 用这个项目部署 Git

具体的操作 可以等待作者后续更新 参考例子: [https://hipldz.github.io](https://hipldz.github.io)

1. 创建一个 Git Page 的代码仓库: [creating-a-github-pages-site](https://docs.github.com/zh/pages/getting-started-with-github-pages/creating-a-github-pages-site)

2. 利用本项目打包出你自己的静态网页: `npm run build` 得到 `dist` 文件夹

3. 将 `dist` 文件夹的内容 全部拷贝到你的 Git Page 仓库, 注意检查是不是有 `.nojekyll` 文件, 这个文件必须存在, 表示我们 发布静态网页的工作流

4. 推送到你的远程 Git Page 仓库

5. 配置你的 Git Page 仓库的 `settings`, 其实就是直接打开 Git Page 这个选项, [configuring-a-publishing-source-for-your-github-pages-site](https://docs.github.com/zh/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

6. 等待 流程跑完 几分钟后 查看你的 `https:/xxxx.github.io` 😎
