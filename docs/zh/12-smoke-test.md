<!--
衍生作品（中文翻译）
源文件: docs/12-smoke-test.md
源仓库: https://github.com/kelseyhightower/kubernetes-the-hard-way
基线提交: 52eb26dad1a3e9e8083a899bc854421eb4842a73 (52eb26d, 2025-04-09)
上游版本: kubernetes v1.32.x / containerd v2.1.x / cni v1.6.x / etcd v3.6.x
许可: CC BY-NC-SA 4.0（文档）；代码片段 Apache-2.0
状态: ☑ 已翻译（待实测校对）
对应笔记: notes/12-smoke-test.md
-->

# 12 - 冒烟测试

在本实验中，你将完成一系列任务，以确保 Kubernetes 集群正常运行。

## 数据加密

本节将验证对 [Secret 数据进行静态加密](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/#verifying-that-data-is-encrypted)的能力。

创建一个 generic Secret：

```bash
kubectl create secret generic kubernetes-the-hard-way \
  --from-literal="mykey=mydata"
```

打印存储在 etcd 中的 `kubernetes-the-hard-way` Secret 的十六进制转储：

```bash
ssh root@server \
    'etcdctl get /registry/secrets/default/kubernetes-the-hard-way | hexdump -C'
```

```text
00000000  2f 72 65 67 69 73 74 72  79 2f 73 65 63 72 65 74  |/registry/secret|
00000010  73 2f 64 65 66 61 75 6c  74 2f 6b 75 62 65 72 6e  |s/default/kubern|
00000020  65 74 65 73 2d 74 68 65  2d 68 61 72 64 2d 77 61  |etes-the-hard-wa|
00000030  79 0a 6b 38 73 3a 65 6e  63 3a 61 65 73 63 62 63  |y.k8s:enc:aescbc|
00000040  3a 76 31 3a 6b 65 79 31  3a 4f 1b 80 d8 89 72 f4  |:v1:key1:O....r.|
00000050  60 8a 2c a0 76 1a e1 dc  98 d6 00 7a a4 2f f3 92  |`.,.v......z./..|
00000060  87 63 c9 22 f4 58 c8 27  b9 ff 2c 2e 1a b6 55 be  |.c.".X.'..,...U.|
00000070  d5 5c 4d 69 82 2f b7 e4  b3 b0 12 e1 58 c4 9c 77  |.\Mi./......X..w|
00000080  78 0c 1a 90 c9 c1 23 6c  73 8e 6e fd 8e 9c 3d 84  |x.....#ls.n...=.|
00000090  7d bf 69 81 ce c9 aa 38  be 3b dd 66 aa a3 33 27  |}.i....8.;.f..3'|
000000a0  df be 6d ac 1c 6d 8a 82  df b3 19 da 0f 93 94 1e  |..m..m..........|
000000b0  e0 7d 46 8d b5 14 d0 c5  97 e2 94 76 26 a8 cb 33  |.}F........v&..3|
000000c0  57 2a d0 27 a6 5a e1 76  a7 3f f0 b7 0a 7b ff 53  |W*.'.Z.v.?...{.S|
000000d0  cf c9 1a 18 5b 45 f8 b1  06 3b a9 45 02 76 23 61  |....[E...;.E.v#a|
000000e0  5e dc 86 cf 8e a4 d3 c9  5c 6a 6f e6 33 7b 5b 8f  |^.......\jo.3{[.|
000000f0  fb 8a 14 74 58 f9 49 2f  97 98 cc 5c d4 4a 10 1a  |...tX.I/...\.J..|
00000100  64 0a 79 21 68 a0 9e 7a  03 b7 19 e6 20 e4 1b ce  |d.y!h..z.... ...|
00000110  91 64 ce 90 d9 4f 86 ca  fb 45 2f d6 56 93 68 e1  |.d...O...E/.V.h.|
00000120  0b aa 8c a0 20 a6 97 fa  a1 de 07 6d 5b 4c 02 96  |.... ......m[L..|
00000130  31 70 20 83 16 f9 0a 22  5c 63 ad f1 ea 41 a7 1e  |1p ...."\c...A..|
00000140  29 1a d4 a4 e9 d7 0c 04  74 66 04 6d 73 d8 2e 3f  |).......tf.ms..?|
00000150  f0 b9 2f 77 bd 07 d7 7c  42 0a                    |../w...|B.|
0000015a
```

etcd 中的键应以 `k8s:enc:aescbc:v1:key1` 为前缀，这表明使用了 `aescbc` 提供程序并配合 `key1` 加密密钥对数据进行了加密。

## Deployment

本节将验证创建和管理 [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) 的能力。

为 [nginx](https://nginx.org/en/) Web 服务器创建一个 Deployment：

```bash
kubectl create deployment nginx \
  --image=nginx:latest
```

列出 `nginx` Deployment 创建的 Pod：

```bash
kubectl get pods -l app=nginx
```

```bash
NAME                     READY   STATUS    RESTARTS   AGE
nginx-56fcf95486-c8dnx   1/1     Running   0          8s
```

### 端口转发

本节将验证使用[端口转发](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/)从远程访问应用的能力。

获取 `nginx` Pod 的完整名称：

```bash
POD_NAME=$(kubectl get pods -l app=nginx \
  -o jsonpath="{.items[0].metadata.name}")
```

将本机端口 `8080` 转发到 `nginx` Pod 的端口 `80`：

```bash
kubectl port-forward $POD_NAME 8080:80
```

```text
Forwarding from 127.0.0.1:8080 -> 80
Forwarding from [::1]:8080 -> 80
```

在新终端中使用该转发地址发起 HTTP 请求：

```bash
curl --head http://127.0.0.1:8080
```

```text
HTTP/1.1 200 OK
Server: nginx/1.27.4
Date: Sun, 06 Apr 2025 17:17:12 GMT
Content-Type: text/html
Content-Length: 615
Last-Modified: Wed, 05 Feb 2025 11:06:32 GMT
Connection: keep-alive
ETag: "67a34638-267"
Accept-Ranges: bytes
```

切回之前的终端，停止到 `nginx` Pod 的端口转发：

```text
Forwarding from 127.0.0.1:8080 -> 80
Forwarding from [::1]:8080 -> 80
Handling connection for 8080
^C
```

### 日志

本节将验证[检索容器日志](https://kubernetes.io/docs/concepts/cluster-administration/logging/)的能力。

打印 `nginx` Pod 的日志：

```bash
kubectl logs $POD_NAME
```

```text
...
127.0.0.1 - - [06/Apr/2025:17:17:12 +0000] "HEAD / HTTP/1.1" 200 0 "-" "curl/7.88.1" "-"
```

### Exec

本节将验证[在容器中执行命令](https://kubernetes.io/docs/tasks/debug-application-cluster/get-shell-running-container/#running-individual-commands-in-a-container)的能力。

通过在 `nginx` 容器中执行 `nginx -v` 命令打印 nginx 版本：

```bash
kubectl exec -ti $POD_NAME -- nginx -v
```

```text
nginx version: nginx/1.27.4
```

## Service

本节将验证使用 [Service](https://kubernetes.io/docs/concepts/services-networking/service/) 暴露应用的能力。

使用 [NodePort](https://kubernetes.io/docs/concepts/services-networking/service/#type-nodeport) 类型的 Service 暴露 `nginx` Deployment：

```bash
kubectl expose deployment nginx \
  --port 80 --type NodePort
```

> 无法使用 LoadBalancer 类型的 Service，因为你的集群未配置[云提供商集成](https://kubernetes.io/docs/getting-started-guides/scratch/#cloud-provider)。配置云提供商集成超出本教程范围。

获取分配给 `nginx` Service 的节点端口：

```bash
NODE_PORT=$(kubectl get svc nginx \
  --output=jsonpath='{range .spec.ports[0]}{.nodePort}')
```

获取运行 `nginx` Pod 的节点主机名：

```bash
NODE_NAME=$(kubectl get pods \
  -l app=nginx \
  -o jsonpath="{.items[0].spec.nodeName}")
```

使用 IP 地址和 `nginx` 节点端口发起 HTTP 请求：

```bash
curl -I http://${NODE_NAME}:${NODE_PORT}
```

```text
Server: nginx/1.27.4
Date: Sun, 06 Apr 2025 17:18:36 GMT
Content-Type: text/html
Content-Length: 615
Last-Modified: Wed, 05 Feb 2025 11:06:32 GMT
Connection: keep-alive
ETag: "67a34638-267"
Accept-Ranges: bytes
```

下一节：[清理](13-cleanup.md)
