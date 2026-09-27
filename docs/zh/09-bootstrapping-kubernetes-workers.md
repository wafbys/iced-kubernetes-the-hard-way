<!--
衍生作品（中文翻译）
源文件: docs/09-bootstrapping-kubernetes-workers.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/09-bootstrapping-kubernetes-workers.md
-->

# 09 - 引导 Kubernetes 工作节点

在本实验中，你将引导两个 Kubernetes 工作节点。将安装以下组件：[runc](https://github.com/opencontainers/runc)、[容器网络插件](https://github.com/containernetworking/cni)、[containerd](https://github.com/containerd/containerd)、[kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet) 和 [kube-proxy](https://kubernetes.io/docs/concepts/cluster-administration/proxies)。

## 前提条件

本节命令必须从 `jumpbox` 运行。

将 Kubernetes 二进制文件和 systemd 单元文件复制到每个工作实例：

```bash
for HOST in node-0 node-1; do
  SUBNET=$(grep ${HOST} machines.txt | cut -d " " -f 4)
  sed "s|SUBNET|$SUBNET|g" \
    configs/10-bridge.conf > 10-bridge.conf

  sed "s|SUBNET|$SUBNET|g" \
    configs/kubelet-config.yaml > kubelet-config.yaml

  scp 10-bridge.conf kubelet-config.yaml \
  root@${HOST}:~/
done
```

```bash
for HOST in node-0 node-1; do
  scp \
    downloads/worker/* \
    downloads/client/kubectl \
    configs/99-loopback.conf \
    configs/containerd-config.toml \
    configs/kube-proxy-config.yaml \
    units/containerd.service \
    units/kubelet.service \
    units/kube-proxy.service \
    root@${HOST}:~/
done
```

```bash
for HOST in node-0 node-1; do
  scp \
    downloads/cni-plugins/* \
    root@${HOST}:~/cni-plugins/
done
```

下一节的命令必须在每个工作实例 `node-0`、`node-1` 上运行。使用 `ssh` 命令登录工作实例。例如：

```bash
ssh root@node-0
```

## 配置 Kubernetes 工作节点

安装操作系统依赖：

```bash
{
  apt-get update
  apt-get -y install socat conntrack ipset kmod
}
```

> `socat` 二进制文件用于支持 `kubectl port-forward` 命令。

禁用 Swap

Kubernetes 对使用 swap 内存的支持有限，因为在涉及 swap 时很难提供保证并准确核算 Pod 的内存使用。

确认 swap 是否已禁用：

```bash
swapon --show
```

如果输出为空，说明 swap 已禁用。如果 swap 已启用，运行以下命令立即禁用它：

```bash
swapoff -a
```

> 要确保重启后 swap 仍保持关闭，请查阅你所使用 Linux 发行版的文档。

创建安装目录：

```bash
mkdir -p \
  /etc/cni/net.d \
  /opt/cni/bin \
  /var/lib/kubelet \
  /var/lib/kube-proxy \
  /var/lib/kubernetes \
  /var/run/kubernetes
```

安装工作节点二进制文件：

```bash
{
  mv crictl kube-proxy kubelet runc \
    /usr/local/bin/
  mv containerd containerd-shim-runc-v2 containerd-stress /bin/
  mv cni-plugins/* /opt/cni/bin/
}
```

### 配置 CNI 网络

创建 `bridge` 网络配置文件：

```bash
mv 10-bridge.conf 99-loopback.conf /etc/cni/net.d/
```

为确保穿过 CNI `bridge` 网络的流量由 `iptables` 处理，加载并配置 `br-netfilter` 内核模块：

```bash
{
  modprobe br-netfilter
  echo "br-netfilter" >> /etc/modules-load.d/modules.conf
}
```

```bash
{
  echo "net.bridge.bridge-nf-call-iptables = 1" \
    >> /etc/sysctl.d/kubernetes.conf
  echo "net.bridge.bridge-nf-call-ip6tables = 1" \
    >> /etc/sysctl.d/kubernetes.conf
  sysctl -p /etc/sysctl.d/kubernetes.conf
}
```

### 配置 containerd

安装 `containerd` 配置文件：

```bash
{
  mkdir -p /etc/containerd/
  mv containerd-config.toml /etc/containerd/config.toml
  mv containerd.service /etc/systemd/system/
}
```

### 配置 Kubelet

创建 `kubelet-config.yaml` 配置文件：

```bash
{
  mv kubelet-config.yaml /var/lib/kubelet/
  mv kubelet.service /etc/systemd/system/
}
```

### 配置 Kubernetes Proxy

```bash
{
  mv kube-proxy-config.yaml /var/lib/kube-proxy/
  mv kube-proxy.service /etc/systemd/system/
}
```

### 启动工作节点服务

```bash
{
  systemctl daemon-reload
  systemctl enable containerd kubelet kube-proxy
  systemctl start containerd kubelet kube-proxy
}
```

检查 kubelet 服务是否在运行：

```bash
systemctl is-active kubelet
```

```text
active
```

在继续下一节之前，务必在每台工作节点 `node-0` 和 `node-1` 上都完成本节步骤。

## 验证

在 `jumpbox` 机器上运行以下命令。

列出已注册的 Kubernetes 节点：

```bash
ssh root@server \
  "kubectl get nodes \
  --kubeconfig admin.kubeconfig"
```

```
NAME     STATUS   ROLES    AGE    VERSION
node-0   Ready    <none>   1m     v1.32.3
node-1   Ready    <none>   10s    v1.32.3
```

下一节：[配置 kubectl 远程访问](10-configuring-kubectl.md)
