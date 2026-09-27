<!--
衍生作品（中文翻译）
源文件: docs/02-jumpbox.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/02-jumpbox.md
-->

# 02 - 设置跳板机

在本实验中，你将把四台机器中的一台设置为 `jumpbox`（跳板机）。这台机器将在整个教程中用于执行命令。虽然本教程使用一台专用机器以保证一致性，但这些命令实际上几乎可以在任何机器上运行，包括你运行 macOS 或 Linux 的个人工作站。

你可以把 `jumpbox` 理解为管理机器——从零开始搭建 Kubernetes 集群时，你将以它为大本营。在开始之前，我们需要安装一些命令行工具，并克隆 Kubernetes The Hard Way 的 git 仓库，其中包含本教程中用于配置各种 Kubernetes 组件的额外配置文件。

登录 `jumpbox`：

```bash
ssh root@jumpbox
```

所有命令都将以 `root` 用户运行。这样做是为了方便，并减少完成所有配置所需的命令数量。

### 安装命令行工具

现在你已作为 `root` 用户登录到 `jumpbox`，接下来安装本教程中用于执行各种任务的命令行工具。

```bash
{
  apt-get update
  apt-get -y install wget curl vim openssl git
}
```

### 同步 GitHub 仓库

现在下载本教程的一份副本，其中包含用于从零构建 Kubernetes 集群的配置文件和模板。使用 `git` 命令克隆 Kubernetes The Hard Way 的 git 仓库：

```bash
git clone --depth 1 \
  https://github.com/kelseyhightower/kubernetes-the-hard-way.git
```

> 译者注：若想使用本中文项目（含译文与笔记），可改为克隆本仓库
> `https://github.com/wafbys/iced-kubernetes-the-hard-way.git`，其余步骤一致。

进入 `kubernetes-the-hard-way` 目录：

```bash
cd kubernetes-the-hard-way
```

这将是本教程后续步骤的工作目录。如果你迷失了位置，可以用 `pwd` 命令确认在 `jumpbox` 上执行命令时处于正确目录：

```bash
pwd
```

```text
/root/kubernetes-the-hard-way
```

### 下载二进制文件

本节将下载各种 Kubernetes 组件的二进制文件。这些文件将存放在 `jumpbox` 的 `downloads` 目录中，从而减少完成本教程所需的互联网带宽，避免为集群中的每台机器重复下载。

要下载的二进制文件列在 `downloads-amd64.txt` 或 `downloads-arm64.txt` 中（取决于你的硬件架构），可用 `cat` 命令查看：

```bash
cat downloads-$(dpkg --print-architecture).txt
```

使用 `wget` 命令将二进制文件下载到名为 `downloads` 的目录：

```bash
wget -q --show-progress \
  --https-only \
  --timestamping \
  -P downloads \
  -i downloads-$(dpkg --print-architecture).txt
```

根据你的网络速度，下载超过 `500` 兆字节的二进制文件可能需要一段时间。下载完成后，可用 `ls` 命令列出它们：

```bash
ls -oh downloads
```

从发布归档中解压各组件二进制文件，并组织到 `downloads` 目录下。

```bash
{
  ARCH=$(dpkg --print-architecture)
  mkdir -p downloads/{client,cni-plugins,controller,worker}
  tar -xvf downloads/crictl-v1.32.0-linux-${ARCH}.tar.gz \
    -C downloads/worker/
  tar -xvf downloads/containerd-2.1.0-beta.0-linux-${ARCH}.tar.gz \
    --strip-components 1 \
    -C downloads/worker/
  tar -xvf downloads/cni-plugins-linux-${ARCH}-v1.6.2.tgz \
    -C downloads/cni-plugins/
  tar -xvf downloads/etcd-v3.6.0-rc.3-linux-${ARCH}.tar.gz \
    -C downloads/ \
    --strip-components 1 \
    etcd-v3.6.0-rc.3-linux-${ARCH}/etcdctl \
    etcd-v3.6.0-rc.3-linux-${ARCH}/etcd
  mv downloads/{etcdctl,kubectl} downloads/client/
  mv downloads/{etcd,kube-apiserver,kube-controller-manager,kube-scheduler} \
    downloads/controller/
  mv downloads/{kubelet,kube-proxy} downloads/worker/
  mv downloads/runc.${ARCH} downloads/worker/runc
}
```

```bash
rm -rf downloads/*gz
```

让二进制文件可执行。

```bash
{
  chmod +x downloads/{client,cni-plugins,controller,worker}/*
}
```

### 安装 kubectl

本节将在 `jumpbox` 机器上安装 `kubectl`——Kubernetes 官方客户端命令行工具。当本教程稍后完成集群配置后，`kubectl` 将用于与 Kubernetes 控制平面交互。

使用 `chmod` 命令让 `kubectl` 二进制文件可执行，并将其移动到 `/usr/local/bin/` 目录：

```bash
{
  cp downloads/client/kubectl /usr/local/bin/
}
```

至此 `kubectl` 已安装，可通过运行 `kubectl` 命令验证：

```bash
kubectl version --client
```

```text
Client Version: v1.32.3
Kustomize Version: v5.5.0
```

至此，`jumpbox` 已配置好完成本教程各实验所需的全部命令行工具和实用程序。

下一节：[准备计算资源](03-compute-resources.md)
