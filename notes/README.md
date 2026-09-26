# notes —— 个人练习笔记

记录实际操作过程中的观察、踩坑、命令输出与验证结果。建议与 `docs/zh/`
章节一一对应，文件名沿用编号，如 `notes/07-bootstrapping-etcd.md`。

## 建议的笔记结构

```
# NN - 章标题 · 练习笔记
- 日期 / 环境：OS、架构(arm64/amd64)、机器角色(jumpbox/control/worker)、IP
- 目标：这一章我要达成什么
- 实际步骤：我实际敲了什么（与译文不同处要标出）
- 结果：成功/失败，关键输出摘要
- 踩坑与解决：报错原文 → 原因 → 解决
- 待办 / 疑问：
```

## 笔记原则

- 与译文分离：不要在 `docs/zh/` 里写个人内容（保持衍生作品的整洁）。
- 命令可复制：贴命令时保留完整上下文，便于日后复现。
- 记录环境差异：上游用 4 台机器，如你用单机/容器/虚拟机，diff 写清楚。

## 章节清单

- [ ] notes/01-prerequisites.md
- [ ] notes/02-jumpbox.md
- [ ] notes/03-compute-resources.md
- [ ] notes/04-certificate-authority.md
- [ ] notes/05-kubernetes-configuration-files.md
- [ ] notes/06-data-encryption-keys.md
- [ ] notes/07-bootstrapping-etcd.md
- [ ] notes/08-bootstrapping-kubernetes-controllers.md
- [ ] notes/09-bootstrapping-kubernetes-workers.md
- [ ] notes/10-configuring-kubectl.md
- [ ] notes/11-pod-network-routes.md
- [ ] notes/12-smoke-test.md
- [ ] notes/13-cleanup.md
