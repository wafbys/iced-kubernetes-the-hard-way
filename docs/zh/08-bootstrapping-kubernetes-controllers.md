<!--
衍生作品（中文翻译）
源文件: docs/08-bootstrapping-kubernetes-controllers.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/08-bootstrapping-kubernetes-controllers.md
-->

# 08 - 引导 Kubernetes 控制平面

在本实验中，你将引导 Kubernetes 控制平面。以下组件将安装到 `server` 机器上：Kubernetes API Server、Scheduler 和 Controller Manager。

## 前提条件

连接到 `jumpbox`，将 Kubernetes 二进制文件和 systemd 单元文件复制到 `server` 机器：

```bash
scp \
  downloads/controller/kube-apiserver \
  downloads/controller/kube-controller-manager \
  downloads/controller/kube-scheduler \
  downloads/client/kubectl \
  units/kube-apiserver.service \
  units/kube-controller-manager.service \
  units/kube-scheduler.service \
  configs/kube-scheduler.yaml \
  configs/kube-apiserver-to-kubelet.yaml \
  root@server:~/
```

本实验中的命令必须在 `server` 机器上运行。使用 `ssh` 命令登录 `server` 机器。例如：

```bash
ssh root@server
```

## 配置 Kubernetes 控制平面

创建 Kubernetes 配置目录：

```bash
mkdir -p /etc/kubernetes/config
```

### 安装 Kubernetes 控制器二进制文件

安装 Kubernetes 二进制文件：

```bash
{
  mv kube-apiserver \
    kube-controller-manager \
    kube-scheduler kubectl \
    /usr/local/bin/
}
```

### 配置 Kubernetes API Server

```bash
{
  mkdir -p /var/lib/kubernetes/

  mv ca.crt ca.key \
    kube-api-server.key kube-api-server.crt \
    service-accounts.key service-accounts.crt \
    encryption-config.yaml \
    /var/lib/kubernetes/
}
```

创建 `kube-apiserver.service` systemd 单元文件：

```bash
mv kube-apiserver.service \
  /etc/systemd/system/kube-apiserver.service
```

### 配置 Kubernetes Controller Manager

将 `kube-controller-manager` 的 kubeconfig 放到指定位置：

```bash
mv kube-controller-manager.kubeconfig /var/lib/kubernetes/
```

创建 `kube-controller-manager.service` systemd 单元文件：

```bash
mv kube-controller-manager.service /etc/systemd/system/
```

### 配置 Kubernetes Scheduler

将 `kube-scheduler` 的 kubeconfig 放到指定位置：

```bash
mv kube-scheduler.kubeconfig /var/lib/kubernetes/
```

创建 `kube-scheduler.yaml` 配置文件：

```bash
mv kube-scheduler.yaml /etc/kubernetes/config/
```

创建 `kube-scheduler.service` systemd 单元文件：

```bash
mv kube-scheduler.service /etc/systemd/system/
```

### 启动控制器服务

```bash
{
  systemctl daemon-reload

  systemctl enable kube-apiserver \
    kube-controller-manager kube-scheduler

  systemctl start kube-apiserver \
    kube-controller-manager kube-scheduler
}
```

> 给 Kubernetes API Server 最多 10 秒时间完成初始化。

你可以用 `systemctl` 命令检查任一控制平面组件是否处于活动状态。例如，检查 `kube-apiserver` 是否已完全初始化并处于活动状态：

```bash
systemctl is-active kube-apiserver
```

若要查看更详细的状态（包含额外的进程信息和日志消息），使用 `systemctl status` 命令：

```bash
systemctl status kube-apiserver
```

如果遇到错误，或想查看任一控制平面组件的日志，使用 `journalctl` 命令。例如，查看 `kube-apiserver` 的日志：

```bash
journalctl -u kube-apiserver
```

### 验证

此时 Kubernetes 控制平面组件应该已启动并运行。使用 `kubectl` 命令行工具验证：

```bash
kubectl cluster-info \
  --kubeconfig admin.kubeconfig
```

```text
Kubernetes control plane is running at https://127.0.0.1:6443
```

## Kubelet 授权的 RBAC

本节将配置 RBAC 权限，允许 Kubernetes API Server 访问每个工作节点上的 Kubelet API。访问 Kubelet API 是检索指标、日志以及在 Pod 中执行命令所必需的。

> 本教程将 Kubelet 的 `--authorization-mode` 标志设置为 `Webhook`。Webhook 模式使用 [SubjectAccessReview](https://kubernetes.io/docs/reference/access-authn-authz/authorization/#checking-api-access) API 来确定授权。

本节的命令会影响整个集群，只需在 `server` 机器上运行。

```bash
ssh root@server
```

创建 `system:kube-apiserver-to-kubelet` [ClusterRole](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole)，授予访问 Kubelet API 以及执行大多数与 Pod 管理相关的常见任务的权限：

```bash
kubectl apply -f kube-apiserver-to-kubelet.yaml \
  --kubeconfig admin.kubeconfig
```

### 验证

此时 Kubernetes 控制平面应已启动并运行。在 `jumpbox` 机器上运行以下命令验证其工作正常：

发起一次 HTTP 请求以获取 Kubernetes 版本信息：

```bash
curl --cacert ca.crt \
  https://server.kubernetes.local:6443/version
```

```text
{
  "major": "1",
  "minor": "32",
  "gitVersion": "v1.32.3",
  "gitCommit": "32cc146f75aad04beaaa245a7157eb35063a9f99",
  "gitTreeState": "clean",
  "buildDate": "2025-03-11T19:52:21Z",
  "goVersion": "go1.23.6",
  "compiler": "gc",
  "platform": "linux/arm64"
}
```

下一节：[引导 Kubernetes 工作节点](09-bootstrapping-kubernetes-workers.md)
