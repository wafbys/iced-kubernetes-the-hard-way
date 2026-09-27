<!--
衍生作品（中文翻译）
源文件: docs/03-compute-resources.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/03-compute-resources.md
-->

# 03 - 准备计算资源

Kubernetes 需要一组机器来承载 Kubernetes 控制平面，以及最终运行容器的工作节点。在本实验中，你将准备搭建 Kubernetes 集群所需的机器。

## 机器数据库

本教程将使用一个文本文件作为“机器数据库”，用于存储搭建 Kubernetes 控制平面和工作节点时会用到的各种机器属性。以下模式表示机器数据库中的条目，每行一条：

```text
IPV4_ADDRESS FQDN HOSTNAME POD_SUBNET
```

每一列分别对应机器 IP 地址 `IPV4_ADDRESS`、完全限定域名 `FQDN`、主机名 `HOSTNAME` 以及 IP 子网 `POD_SUBNET`。Kubernetes 为每个 `pod` 分配一个 IP 地址，而 `POD_SUBNET` 表示分配给集群中每台机器、用于此目的的唯一 IP 地址范围。

下面是一个与创建本教程时所用类似的示例机器数据库。注意 IP 地址已被隐去。只要各机器之间以及它们与 `jumpbox` 之间互相可达，你的机器可以分配任意 IP 地址。

```bash
cat machines.txt
```

```text
XXX.XXX.XXX.XXX server.kubernetes.local server
XXX.XXX.XXX.XXX node-0.kubernetes.local node-0 10.200.0.0/24
XXX.XXX.XXX.XXX node-1.kubernetes.local node-1 10.200.1.0/24
```

现在轮到你了：创建一个 `machines.txt` 文件，填写你将用于创建 Kubernetes 集群的三台机器的信息。参考上面的示例机器数据库，加入你自己机器的详情。

## 配置 SSH 访问

将使用 SSH 来配置集群中的机器。请确认你对机器数据库中列出的每台机器都具备 `root` SSH 访问权限。你可能需要更新每台节点上的 `sshd_config` 文件并重启 SSH 服务，以启用 root SSH 访问。

### 启用 root SSH 访问

如果你的每台机器都已启用 `root` SSH 访问，可以跳过本节。

默认情况下，新安装的 `debian` 会禁用 `root` 用户的 SSH 访问。这是出于安全考虑，因为 `root` 用户对类 Unix 系统拥有完全的管理控制权。如果一台联网机器使用了弱密码，嗯……只能说它迟早会变成别人的机器。如前面所述，为了精简本教程的步骤，我们将通过 SSH 启用 `root` 访问。安全是一种权衡，在此我们选择了便利。使用你的用户账号通过 SSH 登录每台机器，然后用 `su` 命令切换到 `root` 用户：

```bash
su - root
```

编辑 `/etc/ssh/sshd_config` SSH 守护进程配置文件，将 `PermitRootLogin` 选项设置为 `yes`：

```bash
sed -i \
  's/^#*PermitRootLogin.*/PermitRootLogin yes/' \
  /etc/ssh/sshd_config
```

重启 `sshd` SSH 服务以加载更新后的配置文件：

```bash
systemctl restart sshd
```

### 生成并分发 SSH 密钥

本节将生成一个 SSH 密钥对并分发到 `server`、`node-0`、`node-1` 机器，用于本教程中在这些机器上执行命令。以下命令在 `jumpbox` 机器上运行。

生成一个新的 SSH 密钥：

```bash
ssh-keygen
```

```text
Generating public/private rsa key pair.
Enter file in which to save the key (/root/.ssh/id_rsa):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /root/.ssh/id_rsa
Your public key has been saved in /root/.ssh/id_rsa.pub
```

将 SSH 公钥复制到每台机器：

```bash
while read IP FQDN HOST SUBNET; do
  ssh-copy-id root@${IP}
done < machines.txt
```

每把密钥添加完成后，验证 SSH 公钥访问是否正常工作：

```bash
while read IP FQDN HOST SUBNET; do
  ssh -n root@${IP} hostname
done < machines.txt
```

```text
server
node-0
node-1
```

## 主机名

本节将为 `server`、`node-0`、`node-1` 机器分配主机名。当从 `jumpbox` 向各机器执行命令时会用到该主机名。主机名在集群内部也扮演重要角色：Kubernetes 客户端不用 IP 地址向 Kubernetes API 服务器发起命令，而是使用 `server` 主机名。每台工作机器（`node-0`、`node-1`）在向给定 Kubernetes 集群注册时也会用到主机名。

要为每台机器配置主机名，请在 `jumpbox` 上运行以下命令。

为 `machines.txt` 文件中列出的每台机器设置主机名：

```bash
while read IP FQDN HOST SUBNET; do
    CMD="sed -i 's/^127.0.1.1.*/127.0.1.1\t${FQDN} ${HOST}/' /etc/hosts"
    ssh -n root@${IP} "$CMD"
    ssh -n root@${IP} hostnamectl set-hostname ${HOST}
    ssh -n root@${IP} systemctl restart systemd-hostnamed
done < machines.txt
```

验证每台机器的主机名已设置：

```bash
while read IP FQDN HOST SUBNET; do
  ssh -n root@${IP} hostname --fqdn
done < machines.txt
```

```text
server.kubernetes.local
node-0.kubernetes.local
node-1.kubernetes.local
```

## 主机查找表

本节将生成一个 `hosts` 文件，它会被追加到 `jumpbox` 的 `/etc/hosts`，以及本教程用到的三台集群成员的 `/etc/hosts` 中。这样每台机器就能通过 `server`、`node-0` 或 `node-1` 这样的主机名访问。

创建一个新的 `hosts` 文件，并添加一个头注释以标识将要加入的机器：

```bash
echo "" > hosts
echo "# Kubernetes The Hard Way" >> hosts
```

为 `machines.txt` 中的每台机器生成一条主机条目，并追加到 `hosts` 文件：

```bash
while read IP FQDN HOST SUBNET; do
    ENTRY="${IP} ${FQDN} ${HOST}"
    echo $ENTRY >> hosts
done < machines.txt
```

查看 `hosts` 文件中的主机条目：

```bash
cat hosts
```

```text

# Kubernetes The Hard Way
XXX.XXX.XXX.XXX server.kubernetes.local server
XXX.XXX.XXX.XXX node-0.kubernetes.local node-0
XXX.XXX.XXX.XXX node-1.kubernetes.local node-1
```

## 将 `/etc/hosts` 条目添加到本地机器

本节将把 `hosts` 文件中的 DNS 条目追加到 `jumpbox` 机器上的本地 `/etc/hosts` 文件。

将 `hosts` 中的 DNS 条目追加到 `/etc/hosts`：

```bash
cat hosts >> /etc/hosts
```

验证 `/etc/hosts` 文件已更新：

```bash
cat /etc/hosts
```

```text
127.0.0.1       localhost
127.0.1.1       jumpbox

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

# Kubernetes The Hard Way
XXX.XXX.XXX.XXX server.kubernetes.local server
XXX.XXX.XXX.XXX node-0.kubernetes.local node-0
XXX.XXX.XXX.XXX node-1.kubernetes.local node-1
```

此时，你应该能用主机名 SSH 到 `machines.txt` 中列出的每台机器。

```bash
for host in server node-0 node-1
   do ssh root@${host} hostname
done
```

```text
server
node-0
node-1
```

## 将 `/etc/hosts` 条目添加到远程机器

本节将把 `hosts` 中的主机条目追加到 `machines.txt` 文本文件中列出的每台机器的 `/etc/hosts` 中。

将 `hosts` 文件复制到每台机器，并把内容追加到 `/etc/hosts`：

```bash
while read IP FQDN HOST SUBNET; do
  scp hosts root@${HOST}:~/
  ssh -n \
    root@${HOST} "cat hosts >> /etc/hosts"
done < machines.txt
```

至此，从 `jumpbox` 或 Kubernetes 集群中的任意三台机器连接时，都可以使用主机名。你现在可以用 `server`、`node-0` 或 `node-1` 这样的主机名连接机器，而不必使用 IP 地址。

下一节：[准备 CA 并生成 TLS 证书](04-certificate-authority.md)
