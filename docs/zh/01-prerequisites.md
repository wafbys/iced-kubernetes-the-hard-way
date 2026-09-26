<!--
衍生作品（中文翻译）
源文件: docs/01-prerequisites.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/01-prerequisites.md
-->

# 01 - 前提条件

在本实验中，你将了解跟随本教程所需的机器要求。

## 虚拟机或物理机

本教程需要四（4）台运行 Debian 12（bookworm）的 ARM64 或 AMD64 虚拟机或物理机。下表列出了这四台机器及其 CPU、内存和存储要求。

| 名称    | 说明                   | CPU | 内存  | 存储 |
|---------|------------------------|-----|-------|------|
| jumpbox | 管理主机               | 1   | 512MB | 10GB |
| server  | Kubernetes 服务节点    | 1   | 2GB   | 20GB |
| node-0  | Kubernetes 工作节点    | 1   | 2GB   | 20GB |
| node-1  | Kubernetes 工作节点    | 1   | 2GB   | 20GB |

如何准备这些机器由你决定，唯一的要求是每台机器都满足上述系统要求，包括机器规格和操作系统版本。四台机器都准备好后，通过查看 `/etc/os-release` 文件来验证操作系统要求：

```bash
cat /etc/os-release
```

你应该会看到类似以下的输出：

```text
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
```

下一节：[设置跳板机](02-jumpbox.md)
