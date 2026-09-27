<!--
衍生作品（中文翻译）
源文件: docs/13-cleanup.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/13-cleanup.md
-->

# 13 - 清理

在本实验中，你将删除本教程创建的计算资源。

## 计算实例

本指南的早期版本在计算和网络等方面使用了 GCP 资源。当前版本与平台无关，所有配置都在 `jumpbox`、`server` 或各节点上完成。

清理很简单：删除你为本练习创建的所有虚拟机即可。

下一节：[重新开始](../../README.md)
