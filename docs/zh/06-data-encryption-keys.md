<!--
衍生作品（中文翻译）
源文件: docs/06-data-encryption-keys.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/06-data-encryption-keys.md
-->

# 06 - 生成数据加密配置与密钥

Kubernetes 存储各种数据，包括集群状态、应用配置和 Secret。Kubernetes 支持对集群数据进行[静态加密](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data)。

在本实验中，你将生成一个加密密钥，以及一份适用于加密 Kubernetes Secret 的[加密配置](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/#understanding-the-encryption-at-rest-configuration)。

## 加密密钥

生成一个加密密钥：

```bash
export ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)
```

## 加密配置文件

创建 `encryption-config.yaml` 加密配置文件：

```bash
envsubst < configs/encryption-config.yaml \
  > encryption-config.yaml
```

将 `encryption-config.yaml` 加密配置文件复制到每个 controller 实例：

```bash
scp encryption-config.yaml root@server:~/
```

下一节：[引导 etcd 集群](07-bootstrapping-etcd.md)
