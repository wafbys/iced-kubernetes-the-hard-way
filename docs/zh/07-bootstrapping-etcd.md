<!--
衍生作品（中文翻译）
源文件: docs/07-bootstrapping-etcd.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/07-bootstrapping-etcd.md
-->

# 07 - 引导 etcd 集群

Kubernetes 组件是无状态的，集群状态存储在 [etcd](https://github.com/etcd-io/etcd) 中。在本实验中，你将引导一个单节点 etcd 集群。

## 前提条件

将 `etcd` 二进制文件和 systemd 单元文件复制到 `server` 机器：

```bash
scp \
  downloads/controller/etcd \
  downloads/client/etcdctl \
  units/etcd.service \
  root@server:~/
```

本实验中的命令必须在 `server` 机器上运行。使用 `ssh` 命令登录 `server` 机器。例如：

```bash
ssh root@server
```

## 引导 etcd 集群

### 安装 etcd 二进制文件

解压并安装 `etcd` 服务器和 `etcdctl` 命令行工具：

```bash
{
  mv etcd etcdctl /usr/local/bin/
}
```

### 配置 etcd 服务器

```bash
{
  mkdir -p /etc/etcd /var/lib/etcd
  chmod 700 /var/lib/etcd
  cp ca.crt kube-api-server.key kube-api-server.crt \
    /etc/etcd/
}
```

etcd 集群中的每个成员都必须有唯一的名称。将 etcd 名称设置为与当前计算实例的主机名一致：

创建 `etcd.service` systemd 单元文件：

```bash
mv etcd.service /etc/systemd/system/
```

### 启动 etcd 服务器

```bash
{
  systemctl daemon-reload
  systemctl enable etcd
  systemctl start etcd
}
```

## 验证

列出 etcd 集群成员：

```bash
etcdctl member list
```

```text
6702b0a34e2cfd39, started, controller, http://127.0.0.1:2380, http://127.0.0.1:2379, false
```

下一节：[引导 Kubernetes 控制平面](08-bootstrapping-kubernetes-controllers.md)
