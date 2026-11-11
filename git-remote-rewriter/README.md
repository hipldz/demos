# Git Remote Rewriter

[返回项目索引](../README.md)

一个简单的 Bash 工具，用于批量修改**当前目录下一层 Git 仓库**中 `@github.com/` 前的 Remote 用户名或认证前缀。

它会自动扫描：

```text
./*/.git/config
```

并找出类似：

```text
https://old-user@github.com/hipldz/repository.git
```

中的 `old-user`，然后让你输入新的 Remote 用户名，批量替换为：

```text
https://new-user@github.com/hipldz/repository.git
```

脚本只处理 `github.com`，不会修改 `gitee.com`、`gitlab.com` 或其他 Git 服务。

---

## 功能

* 自动扫描当前目录下一层的 Git 仓库
* 自动找出所有 GitHub Remote 用户名
* 无需手动填写旧用户名
* 交互式输入新的 Remote 用户名
* 支持多个不同旧用户名统一替换
* 只修改 `github.com`
* 修改前自动备份 `.git/config`
* 支持一键清理 `.git/config.bak`
* 删除备份前会再次确认

---

## 目录结构

例如当前目录：

```text
workspace/
├── repo-a/
│   └── .git/
│       └── config
├── repo-b/
│   └── .git/
│       └── config
├── repo-c/
│   └── .git/
│       └── config
└── nested/
    └── repo-d/
        └── .git/
            └── config
```

脚本会处理：

```text
./repo-a/.git/config
./repo-b/.git/config
./repo-c/.git/config
```

不会处理更深层目录中的：

```text
./nested/repo-d/.git/config
```

---

## 使用方法

给脚本添加执行权限：

```bash
chmod +x replace_git_owner.sh
```

然后在包含多个 Git 仓库的父目录中运行：

```bash
./replace_git_owner.sh
```

脚本会自动扫描 GitHub Remote。

例如：

```text
正在扫描 GitHub remote 用户名...

发现以下 GitHub remote 用户名：

  old-token
  old-user

涉及配置：
  ./repo-a/.git/config
  ./repo-b/.git/config

请输入新的 GitHub remote 用户名:
```

输入：

```text
new-user
```

脚本会将所有匹配到的 Remote 用户名替换为：

```text
new-user
```

---

## 替换示例

修改前：

```ini
[remote "origin"]
    url = https://old-token@github.com/hipldz/example.git
```

修改后：

```ini
[remote "origin"]
    url = https://new-token@github.com/hipldz/example.git
```

GitHub Owner 和仓库名称都不会变化。

即：

```text
https://old-token@github.com/hipldz/example.git
         ^^^^^^^^^
```

只修改 `@github.com/` 前的 Remote 用户名：

```text
https://new-token@github.com/hipldz/example.git
         ^^^^^^^^^
```

## 多个旧用户名

如果当前目录中存在：

```text
https://token-a@github.com/hipldz/repo-a.git
https://token-b@github.com/hipldz/repo-b.git
https://old-token@github.com/hipldz/repo-c.git
```

脚本会自动发现：

```text
token-a
token-b
old-token
```

如果输入：

```text
new-token
```

最终会变成：

```text
https://new-token@github.com/hipldz/repo-a.git
https://new-token@github.com/hipldz/repo-b.git
https://new-token@github.com/hipldz/repo-c.git
```

---

## 不会修改 Gitee

例如：

```text
https://old-user@gitee.com/pldz1/repo.git
```

不会发生任何变化。

同样，其他非 GitHub 地址也不会被替换。

例如：

```text
https://gitlab.com/old-user/repo.git
git@gitee.com:old-user/repo.git
```

脚本的替换范围仅限：

```text
<remote-user>@github.com/<owner>/
```

---

## 自动备份

修改 `.git/config` 前，脚本会自动创建：

```text
.git/config.bak
```

例如：

```text
repo-a/
└── .git/
    ├── config
    └── config.bak
```

如果 `config.bak` 已经存在，脚本不会覆盖它。

这样可以保留第一次修改之前的原始配置。

---

## 删除备份

确认修改没有问题后，可以运行：

```bash
./replace_git_owner.sh clean
```

脚本会找出所有第一层仓库中的：

```text
.git/config.bak
```

例如：

```text
发现以下备份文件：

  ./repo-a/.git/config.bak
  ./repo-b/.git/config.bak
  ./repo-c/.git/config.bak

确定删除这些备份吗？[y/N]:
```

输入：

```text
y
```

才会真正删除。

如果直接回车或输入其他内容，则取消删除。

---

## 推荐使用流程

```bash
# 1. 添加执行权限
chmod +x replace_git_owner.sh

# 2. 执行替换
./replace_git_owner.sh

# 3. 检查几个仓库的 remote
git remote -v

# 4. 确认没有问题后删除备份
./replace_git_owner.sh clean
```

---

## 注意事项

脚本会把扫描到的所有 GitHub Remote 用户名**统一替换为你输入的新用户名**。

例如扫描到：

```text
token-a
token-b
token-c
```

输入：

```text
new-token
```

那么这三个 Remote 用户名都会变成：

```text
new-token
```

因此运行前请确认当前目录下的这些仓库确实需要统一使用新的 Remote 用户名或认证前缀。

---

## Requirements

需要：

* Bash
* `grep`
* `sed`
* `sort`
* `perl`

大多数 Linux 和 macOS 环境默认已经包含这些工具。

---
