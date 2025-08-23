# ugit 使用指南

**ugit** 是一个轻量级的、从零开始实现的 Git 克隆版本，完全使用 Python 编写，旨在帮助你理解 Git 的核心原理与实现细节。

## 一、项目概述

- **项目名称**：ugit
- **版本**：1.0
- **语言**：Python
- **功能定位**：学习 Git 核心机制，提供基本的版本控制功能

## 二、安装方式

在项目根目录下执行：

```bash
python setup.py develop --user
```

安装完成后，系统命令行将新增一个 `ugit` 命令，使用方式与原生 Git 类似。

> 注意：  
> 安装路径通常为  
> `C:\Users\%USERNAME%\AppData\Roaming\Python\Python3xx\Scripts`（Windows）  
> 或类似的用户目录（Linux/macOS）。  
> 如果命令未识别，请检查 PATH 环境变量。

## 三、核心功能

| 功能类别       | 子命令                          | 说明                         |
| -------------- | ------------------------------- | ---------------------------- |
| **初始化仓库** | `ugit init`                     | 创建新的 ugit 仓库           |
| **对象管理**   | `ugit hash-object <file>`       | 计算文件的 SHA-1 哈希值      |
|                | `ugit cat-file <object>`        | 查看对象内容                 |
| **索引与树**   | `ugit add <files...>`           | 将文件添加到暂存区           |
|                | `ugit write-tree`               | 将暂存区内容写入树对象       |
|                | `ugit read-tree <tree>`         | 将树对象读入暂存区           |
| **提交与分支** | `ugit commit -m <msg>`          | 提交暂存区内容               |
|                | `ugit log [commit]`             | 查看提交历史                 |
|                | `ugit branch [name]`            | 创建或查看分支               |
|                | `ugit checkout <commit>`        | 切换分支或提交               |
|                | `ugit reset <commit>`           | 重置分支指针                 |
| **标签**       | `ugit tag <name> [commit]`      | 创建标签                     |
| **差异与合并** | `ugit diff [--cached] [commit]` | 查看差异                     |
|                | `ugit merge <commit>`           | 合并分支                     |
|                | `ugit merge-base <c1> <c2>`     | 计算共同祖先                 |
| **远程操作**   | `ugit fetch <remote>`           | 从远程获取数据               |
|                | `ugit push <remote> <branch>`   | 推送分支到远程               |
| **可视化**     | `ugit k`                        | 调用 Graphviz 生成提交历史图 |

## 四、文件结构

```
ugit/
├── __init__.py
├── base.py          # 核心逻辑实现
├── cli.py           # 命令行接口
├── data.py          # 数据存储与对象管理
├── diff.py          # 差异计算与合并
├── diff_git_rel_diff.py  # 调用 Git 的 diff 工具
├── remote.py        # 远程仓库操作
└── setup.py         # 安装脚本
```

## 五、技术细节

- **对象存储**：使用 SHA-1 哈希作为对象 ID，存储在 `.ugit/objects/` 目录下。
- **引用管理**：分支、标签等引用存储在 `.ugit/refs/` 目录下。
- **索引文件**：`.ugit/index` 使用 JSON 格式存储暂存区内容。
- **差异与合并**：支持基于 Git 的 diff 和 diff3 合并算法。
- **远程仓库**：通过文件系统路径模拟远程仓库，支持 fetch 和 push 操作。

## 六、使用示例

### 1. 初始化仓库

```bash
mkdir myproject && cd myproject
ugit init
```

### 2. 添加文件并提交

```bash
echo "Hello ugit" > hello.txt
ugit add hello.txt
ugit commit -m "Initial commit"
```

### 3. 创建分支并切换

```bash
ugit branch feature
ugit checkout feature
```

### 4. 查看提交历史

```bash
ugit log
```

### 5. 可视化提交图

```bash
ugit k
```

> 需提前安装 [Graphviz](https://graphviz.org/download/)。

### 6. 远程操作示例

假设远程仓库路径为 `/tmp/remote_repo`：

```bash
# 初始化远程仓库
cd /tmp && mkdir remote_repo && cd remote_repo
ugit init

# 本地仓库推送到远程
cd /path/to/myproject
ugit push /tmp/remote_repo master

# 从远程仓库拉取
ugit fetch /tmp/remote_repo
```

## 七、注意事项与限制

- 当前版本仅支持本地文件系统路径作为远程仓库。
- 未实现 SSH、HTTP(S) 等协议支持。
- 未实现压缩存储（如 Git 的 packfile）。
- 适合学习用途，不建议用于生产环境。

## 八、结语

ugit 是一个纯粹用于学习和探索 Git 内部机制的实验项目。  
通过阅读和修改源代码，你可以深入理解 Git 的对象模型、索引机制、分支管理、差异与合并算法等核心概念。

祝你玩得开心，学得愉快！