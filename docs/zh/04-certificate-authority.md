<!--
衍生作品（中文翻译）
源文件: docs/04-certificate-authority.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/04-certificate-authority.md
-->

# 04 - 准备 CA 并生成 TLS 证书

在本实验中，你将使用 openssl 搭建一套 [PKI 基础设施](https://en.wikipedia.org/wiki/Public_key_infrastructure)，用于引导一个证书颁发机构（CA），并为以下组件生成 TLS 证书：kube-apiserver、kube-controller-manager、kube-scheduler、kubelet 和 kube-proxy。本节的命令应在 `jumpbox` 上运行。

## 证书颁发机构

本节将搭建一个证书颁发机构（CA），用于为其他 Kubernetes 组件生成额外的 TLS 证书。用 `openssl` 搭建 CA 并生成证书可能比较耗时，尤其是第一次做的时候。为了简化本实验，我提供了一个 openssl 配置文件 `ca.conf`，它定义了为每个 Kubernetes 组件生成证书所需的全部细节。

花点时间查看一下 `ca.conf` 配置文件：

```bash
cat ca.conf
```

你不需要理解 `ca.conf` 中的所有内容就能完成本教程，但可以把它当作学习 `openssl` 以及从高层理解证书管理配置的起点。

每个证书颁发机构都始于一个私钥和根证书。本节我们将创建一个自签名证书颁发机构；虽然本教程只需要这样就够了，但这不应被视为在真实生产环境中会采用的做法。

生成 CA 配置文件、证书和私钥：

```bash
{
  openssl genrsa -out ca.key 4096
  openssl req -x509 -new -sha512 -noenc \
    -key ca.key -days 3653 \
    -config ca.conf \
    -out ca.crt
}
```

结果：

```txt
ca.crt ca.key
```

## 创建客户端与服务器证书

本节将为每个 Kubernetes 组件生成客户端和服务器证书，并为 Kubernetes `admin` 用户生成客户端证书。

生成证书和私钥：

```bash
certs=(
  "admin" "node-0" "node-1"
  "kube-proxy" "kube-scheduler"
  "kube-controller-manager"
  "kube-api-server"
  "service-accounts"
)
```

```bash
for i in ${certs[*]}; do
  openssl genrsa -out "${i}.key" 4096

  openssl req -new -key "${i}.key" -sha256 \
    -config "ca.conf" -section ${i} \
    -out "${i}.csr"

  openssl x509 -req -days 3653 -in "${i}.csr" \
    -copy_extensions copyall \
    -sha256 -CA "ca.crt" \
    -CAkey "ca.key" \
    -CAcreateserial \
    -out "${i}.crt"
done
```

运行上述命令的结果是为每个 Kubernetes 组件生成一个私钥、一个证书请求和一个已签名的 SSL 证书。你可以用以下命令列出生成的文件：

```bash
ls -1 *.crt *.key *.csr
```

## 分发客户端与服务器证书

本节将把各种证书复制到每台机器上某个路径，每个 Kubernetes 组件会在该路径查找自己的证书对。在真实环境中，这些证书应当被视为一组敏感密钥，因为 Kubernetes 组件会用它们作为凭据来相互认证。

将相应的证书和私钥复制到 `node-0` 和 `node-1` 机器：

```bash
for host in node-0 node-1; do
  ssh root@${host} mkdir /var/lib/kubelet/

  scp ca.crt root@${host}:/var/lib/kubelet/

  scp ${host}.crt \
    root@${host}:/var/lib/kubelet/kubelet.crt

  scp ${host}.key \
    root@${host}:/var/lib/kubelet/kubelet.key
done
```

将相应的证书和私钥复制到 `server` 机器：

```bash
scp \
  ca.key ca.crt \
  kube-api-server.key kube-api-server.crt \
  service-accounts.key service-accounts.crt \
  root@server:~/
```

> `kube-proxy`、`kube-controller-manager`、`kube-scheduler` 和 `kubelet` 的客户端证书将用于在下一个实验中生成客户端认证配置文件。

下一节：[生成用于认证的 Kubernetes 配置文件](05-kubernetes-configuration-files.md)
