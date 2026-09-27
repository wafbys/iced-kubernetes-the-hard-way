# scripts —— 宿主机辅助脚本

本目录存放练习 KTHW 时用于准备**宿主机环境**的辅助脚本。它们不属于上游
教程步骤（上游步骤都在 Debian 虚拟机内执行），而是本仓库新增的便利工具。

## VMware-VBS-Switch.ps1

### 解决什么问题

在 Windows 宿主机上用 VMware Workstation/Player 跑 KTHW 的 4 台 Debian 12 虚机
（1 jumpbox + 1 server + 2 workers）时，如果宿主机开着：

- VBS（基于虚拟化的安全 / Device Guard）
- 内存完整性（HVCI）
- Hyper-V / 虚拟化平台

Windows 的 Hyper-V 会独占硬件虚拟化，导致 VMware 无法独占 Intel VT-x / AMD-V，
表现为**虚机性能明显下降**，并且**无法为 guest 开启嵌套虚拟化**——而 KTHW 需要
在单台 server 上运行 etcd/kube-apiserver 等控制平面组件，嵌套虚拟化通常是必要的。

### 脚本做什么

在两种状态之间切换（**切换后必须重启才生效**）：

| 模式 | 作用 |
| --- | --- |
| `vmware` | 关闭 VBS / 内存完整性(HVCI) / Hyper-V / 虚拟化平台，并设 `bcdedit hypervisorlaunchtype=off` |
| `restore` | 恢复 Windows 默认安全配置（重新开启 VBS / HVCI / 虚拟化平台） |
| `status` | 只读，显示当前虚拟化相关状态 |

### 用法

以管理员身份运行（脚本会自动请求提权）：

```powershell
# 交互菜单
.\VMware-VBS-Switch.ps1

# 关闭 VBS/Hyper-V，切换到 VMware 模式（练习 KTHW 前执行）
.\VMware-VBS-Switch.ps1 vmware

# 查看当前状态
.\VMware-VBS-Switch.ps1 status

# 练习结束后恢复 Windows 安全配置
.\VMware-VBS-Switch.ps1 restore
```

若被执行策略拦截，可临时绕过：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\VMware-VBS-Switch.ps1 vmware
```

### 切换后的操作

1. 重启宿主机。
2. 打开 VMware 虚机设置 → **处理器** → 勾选 **“虚拟化 Intel VT-x/EPT 或 AMD-V/RVI”**。
3. 进入 guest 后用 `lscpu | grep -i virtualization` 或 `ls /dev/kvm` 验证嵌套虚拟化可用。

### 注意事项

- **需要重启**：注册表/DISM/bcdedit 的更改在重启后才生效。
- **安全影响**：`vmware` 模式会临时关闭 VBS/内存完整性/Hyper-V 等 Windows 安全特性。
  仅在你清楚后果时使用，练习结束请执行 `restore` 并重启恢复。
- **仅限 Windows 宿主机**：本脚本面向 Windows + VMware；用 Linux/KVM 或云主机时不需要。
- 部分 DISM 功能可能不存在而“已跳过”，属正常；核心改动是 Device Guard 注册表与 bcdedit。

### 与教程章节的关系

属于环境准备，见 [docs/zh/01-prerequisites.md](../docs/zh/01-prerequisites.md)
中“虚拟机或物理机”的准备部分；本脚本不改变教程正文内容，仅帮助宿主环境达到可练习状态。
