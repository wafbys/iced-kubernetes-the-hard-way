# docs/zh —— 中文翻译区

本目录存放 `docs/` 上游英文章节的中文翻译，属于**衍生作品**，
遵循上游文档许可 **CC BY-NC-SA 4.0**（署名 + 非商业 + 相同方式共享）。

## 规则

1. **只翻译说明性文字，命令与代码保持原样**（上游代码为 Apache-2.0）。
   如确需改动命令，用注释或“我的改动”小节单独标注。
2. 每个中文文件顶部保留来源注释块（见 `_template.md`），注明：
   源文件路径、上游基线提交、许可、状态。
3. 章节编号与文件名与上游保持一致，便于 `git diff` 对照与同步。
4. 本地补充/踩坑写进 `notes/`，不要混入译文正文；正文如必须加说明，用
   `> 译者注：` 引用块标记。

## 附加章节（本仓库新增，非上游）

以下不是上游 13 个 lab 的翻译，而是本地环境准备等原创补充内容。

| # | 文档 | 性质 | 状态 |
| --- | --- | --- | --- |
| 00 | docs/zh/00-debian-install.md（环境准备：安装 Debian） | 原创补充 | ☑ 已完成 |

## 章节对照与进度

| # | 上游原文 | 中文译文 | 状态 |
| --- | --- | --- | --- |
| 01 | docs/01-prerequisites.md | docs/zh/01-prerequisites.md | ☑ 已翻译 |
| 02 | docs/02-jumpbox.md | docs/zh/02-jumpbox.md | ☑ 已翻译 |
| 03 | docs/03-compute-resources.md | docs/zh/03-compute-resources.md | ☑ 已翻译 |
| 04 | docs/04-certificate-authority.md | docs/zh/04-certificate-authority.md | ☑ 已翻译 |
| 05 | docs/05-kubernetes-configuration-files.md | docs/zh/05-kubernetes-configuration-files.md | ☑ 已翻译 |
| 06 | docs/06-data-encryption-keys.md | docs/zh/06-data-encryption-keys.md | ☑ 已翻译 |
| 07 | docs/07-bootstrapping-etcd.md | docs/zh/07-bootstrapping-etcd.md | ☑ 已翻译 |
| 08 | docs/08-bootstrapping-kubernetes-controllers.md | docs/zh/08-bootstrapping-kubernetes-controllers.md | ☑ 已翻译 |
| 09 | docs/09-bootstrapping-kubernetes-workers.md | docs/zh/09-bootstrapping-kubernetes-workers.md | ☑ 已翻译 |
| 10 | docs/10-configuring-kubectl.md | docs/zh/10-configuring-kubectl.md | ☑ 已翻译 |
| 11 | docs/11-pod-network-routes.md | docs/zh/11-pod-network-routes.md | ☑ 已翻译 |
| 12 | docs/12-smoke-test.md | docs/zh/12-smoke-test.md | ☑ 已翻译 |
| 13 | docs/13-cleanup.md | docs/zh/13-cleanup.md | ☑ 已翻译 |

状态图例：☐ 未开始 / ◐ 进行中 / ☑ 已翻译 / ✔ 已实测校对

## 翻译步骤

1. 复制 `_template.md` 为目标章节文件（如 `01-prerequisites.md`）。
2. 打开上游 `docs/NN-*.md`，逐段翻译，命令保持原样。
3. 本地按译文实际操作一遍，把结果与踩坑记录到 `notes/NN-*.md`。
4. 更新上方进度表，并同步 `NOTICE` 中的“修改说明”。
