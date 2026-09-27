<!--
衍生作品（中文翻译）
源文件: docs/10-configuring-kubectl.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/10-configuring-kubectl.md
-->

# 10 - 配置 kubectl 远程访问

在本实验中，你将基于 `admin` 用户凭据为 `kubectl` 命令行工具生成一个 kubeconfig 文件。

> 请在 `jumpbox` 机器上运行本实验中的命令。

## Admin 的 Kubernetes 配置文件

每个 kubeconfig 都需要一个可连接的 Kubernetes API Server。

基于之前实验中 `/etc/hosts` 的 DNS 条目，你应该能够 ping 通 `server.kubernetes.local`。

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

生成一个适合以 `admin` 用户身份认证的 kubeconfig 文件：

```bash
{
  kubectl config set-cluster kubernetes-the-hard-way \
    --certificate-authority=ca.crt \
    --embed-certs=true \
    --server=https://server.kubernetes.local:6443

  kubectl config set-credentials admin \
    --client-certificate=admin.crt \
    --client-key=admin.key

  kubectl config set-context kubernetes-the-hard-way \
    --cluster=kubernetes-the-hard-way \
    --user=admin

  kubectl config use-context kubernetes-the-hard-way
}
```

运行上述命令的结果应在 `kubectl` 命令行工具使用的默认位置 `~/.kube/config` 创建 kubeconfig 文件。这也意味着你可以在不指定配置的情况下运行 `kubectl` 命令。

## 验证

查看远程 Kubernetes 集群的版本：

```bash
kubectl version
```

```text
Client Version: v1.32.3
Kustomize Version: v5.5.0
Server Version: v1.32.3
```

列出远程 Kubernetes 集群中的节点：

```bash
kubectl get nodes
```

```
NAME     STATUS   ROLES    AGE    VERSION
node-0   Ready    <none>   10m   v1.32.3
node-1   Ready    <none>   10m   v1.32.3
```

下一节：[配置 Pod 网络路由](11-pod-network-routes.md)
