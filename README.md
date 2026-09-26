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

## 仓库结构

| 路径 | 说明 |
| --- | --- |
| `docs/` | 上游英文原文（保持不动，便于对照与同步） |
| `docs/zh/` | 章节中文翻译（衍生作品，CC BY-NC-SA 4.0） |
| `notes/` | 个人练习笔记（含踩坑、补充、验证记录） |
| `reference/` | 术语表等参考资料 |
| `configs/` `units/` | 上游配置与 systemd unit 文件（Apache-2.0） |

翻译工作流见 [docs/zh/README.md](docs/zh/README.md)。

## 许可

- 文档与译文：CC BY-NC-SA 4.0（署名 + 非商业 + 相同方式共享）
- 代码与配置片段：Apache License 2.0
- 个人笔记：见 [NOTICE](NOTICE)

## 许可原文

英文原仓库双许可：正文为 CC BY-NC-SA 4.0，代码为 Apache-2.0。
本仓库保留上游 `LICENSE` 与 `COPYRIGHT.md` 原文件。
