# iced-kubernetes-the-hard-way

基于 [kelseyhightower/kubernetes-the-hard-way](https://github.com/kelseyhightower/kubernetes-the-hard-way)
的中文母语化学习项目，并结合个人实际练习笔记。用于个人学习，非生产用途。

> 上游原文：*Kubernetes The Hard Way*，作者 Kelsey Hightower。
> 本仓库为学习用途的中文衍生作品，署名与许可详见 [NOTICE](NOTICE)。

## 基线信息

- 上游基线提交：`52eb26d`（2025-04-09）
- 组件版本：
  - [kubernetes](https://github.com/kubernetes/kubernetes) v1.32.x
  - [containerd](https://github.com/containerd/containerd) v2.1.x
  - [cni](https://github.com/containernetworking/cni) v1.6.x
  - [etcd](https://github.com/etcd-io/etcd) v3.6.x

## 文档目录（中文）

0. [环境准备：安装 Debian](docs/zh/00-debian-install.md)（本仓库补充）
1. [前提条件](docs/zh/01-prerequisites.md)
2. [设置跳板机](docs/zh/02-jumpbox.md)
3. [准备计算资源](docs/zh/03-compute-resources.md)
4. [准备 CA 并生成 TLS 证书](docs/zh/04-certificate-authority.md)
5. [生成用于认证的 Kubernetes 配置文件](docs/zh/05-kubernetes-configuration-files.md)
6. [生成数据加密配置与密钥](docs/zh/06-data-encryption-keys.md)
7. [引导 etcd 集群](docs/zh/07-bootstrapping-etcd.md)
8. [引导 Kubernetes 控制平面](docs/zh/08-bootstrapping-kubernetes-controllers.md)
9. [引导 Kubernetes 工作节点](docs/zh/09-bootstrapping-kubernetes-workers.md)
10. [配置 kubectl 远程访问](docs/zh/10-configuring-kubectl.md)
11. [配置 Pod 网络路由](docs/zh/11-pod-network-routes.md)
12. [冒烟测试](docs/zh/12-smoke-test.md)
13. [清理](docs/zh/13-cleanup.md)

> 翻译进度见 [docs/zh/README.md](docs/zh/README.md)；英文原文见 [docs/](docs/)。
> 离线单文件版（全部章节合并且内嵌字体）：[docs/zh/kubernetes-the-hard-way-zh.html](docs/zh/kubernetes-the-hard-way-zh.html)。

## 环境准备（Windows 宿主机）

在 Windows + VMware 上练习时，**按需关闭 VBS / Hyper-V**：宿主机若开着 VBS（基于虚拟化的安全）、
内存完整性（HVCI）或 Hyper-V，硬件虚拟化会被它们占用，VMware 只能走兼容模式、虚机性能明显下降；
关闭后需**重启宿主机**才生效。KTHW 本身不需要嵌套虚拟化。

4 台 Debian 12 虚机的安装与配置步骤见
[docs/zh/00-debian-install.md](docs/zh/00-debian-install.md)。

## 仓库结构

| 路径 | 说明 |
| --- | --- |
| `docs/` | 上游英文原文（保持不动，便于对照与同步） |
| `docs/zh/` | 章节中文翻译（衍生作品，CC BY-NC-SA 4.0） |
| `notes/` | 个人练习笔记（含踩坑、补充、验证记录） |
| `reference/` | 术语表等参考资料 |
| `tools/` | 构建脚本（合成单文件 HTML），见 [tools/README.md](tools/README.md) |
| `configs/` `units/` | 上游配置与 systemd unit 文件（Apache-2.0） |

翻译工作流见 [docs/zh/README.md](docs/zh/README.md)。

## 许可

- 文档与译文：CC BY-NC-SA 4.0（署名 + 非商业 + 相同方式共享）
- 代码与配置片段：Apache License 2.0
- 个人笔记：见 [NOTICE](NOTICE)

## 许可原文

英文原仓库双许可：正文为 CC BY-NC-SA 4.0，代码为 Apache-2.0。
本仓库保留上游 `LICENSE` 与 `COPYRIGHT.md` 原文件。
