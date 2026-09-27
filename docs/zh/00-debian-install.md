<!--
本仓库新增（非上游章节）
性质: 原创补充文档（非翻译）
许可: 与 docs/zh 一致，按 CC BY-NC-SA 4.0 发布
说明: 本文不属于上游 13 个 lab，属于练习前的宿主机/虚机环境准备。
-->

# 00 - 环境准备：安装 Debian

本文是上游教程之外的补充章节，用于在本地准备 4 台 `Debian 12 (bookworm)` 虚机
（`jumpbox` / `server` / `node-0` / `node-1`），供第 01 章及之后使用。
上游第 01 章只规定机器规格，不涉及如何安装，故在此补齐。

## 0. 宿主机准备（Windows + VMware）

1. 确认 CPU 虚拟化已在 BIOS/UEFI 打开（Intel VT-x / AMD-V）。
2. **先运行仓库里的切换脚本**，否则 Hyper-V/VBS 开启时 VMware 会走兼容模式、虚机性能明显下降：
   ```powershell
   pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\VMware-VBS-Switch.ps1 vmware
   ```
   然后重启宿主机（详见 [scripts/README.md](../../scripts/README.md)）。
3. 安装 VMware Workstation Pro（个人免费）或 Player。
4. 下载 Debian 12 netinst ISO（amd64）：<https://www.debian.org/distrib/netinst>
   文件名形如 `debian-12.x.x-amd64-netinst.iso`（x86 宿主选 amd64；Apple/ARM 才选 arm64）。
5. 规划（对应第 01 章要求）：

   | 名称 | 角色 | vCPU | 内存 | 磁盘 | 建议静态 IP* |
   | --- | --- | --- | --- | --- | --- |
   | jumpbox | 管理主机 | 1 | 512MB | 10GB | 192.168.152.10 |
   | server | K8s 服务节点 | 1（建议 2） | 2GB | 20GB | 192.168.152.11 |
   | node-0 | 工作节点 | 1（建议 2） | 2GB | 20GB | 192.168.152.12 |
   | node-1 | 工作节点 | 1（建议 2） | 2GB | 20GB | 192.168.152.13 |

   \* IP 取你 VMware NAT 网段（`VMnet8`），先用默认即可，装完按下面改成静态。

## 1. 创建第一台虚机（以 jumpbox 为例）

1. VMware → `Create a New Virtual Machine` → **Custom (advanced)**。
2. Guest OS：**Linux → Debian 12.x 64-bit**。
3. 位置与磁盘：磁盘 10GB，存为**单个文件**。
4. 内存/CPU 按上表填。
5. 网络：**NAT**（4 台都在同一 NAT 网段即可互通；也可用“自定义”指定 `VMnet8`）。
6. 完成后进入 `Edit virtual machine settings` → **Processors** → 勾选
   **“Virtualize Intel VT-x/EPT or AMD-V/RVI”**（可选：仅当你要在 Debian 客户机里
   再运行虚机/模拟器时才需要；KTHW 本身不需要嵌套虚拟化）。
7. `CD/DVD` → 挂载下载好的 Debian ISO。

## 2. 安装 Debian 12

开机进入安装程序，选 `Graphical install`：

1. **Language / Location / Keymap**：English / United States / American English
   （服务器用英文可避免 locale 麻烦）。
2. **Network**：主机名填 `jumpbox`，域名留空。DHCP 自动获取即可（稍后改静态）。
3. **Root password**：设一个（记住）。
4. **Create a user**：用户名建议 `debian`，设密码。会问“是否设置 root 登录”，选否。
5. **Partition disks**：`Guided - use entire disk` → 单分区（不用 LVM 也行）→ 写入。
6. **Scan extra media / Package mirror**：可跳过；镜像选默认 `deb.debian.org`。
7. **Software selection**：**只勾选 `SSH server` 和 `standard system utilities`**，
   务必**不要**勾桌面环境（GNOME 等）。
8. **Install GRUB**：装到 `/dev/sda`（默认）。
9. 完成后重启；在 `Settings` 里把 ISO 从 CD/DVD 卸载，避免再次从光驱启动。

## 3. 首次登录后的基础配置（每台都要做）

用 `debian` 用户登录（或 VMware 控制台）。

**a. 确认版本（对应第 01 章验收）**
```bash
cat /etc/os-release     # 应显示 Debian GNU/Linux 12 (bookworm)
```

**b. 确保 sudo 可用**（若安装时设了 root 密码，普通用户默认不在 sudoers）
```bash
su -                       # 输入 root 密码
usermod -aG sudo debian
apt update && apt install -y sudo
exit
# 重新登录 debian 后验证
sudo -v
```

**c. 固定主机名 + hosts**
```bash
sudo hostnamectl set-hostname jumpbox
sudo tee -a /etc/hosts >/dev/null <<'EOF'
192.168.152.10 jumpbox
192.168.152.11 server
192.168.152.12 node-0
192.168.152.13 node-1
EOF
```

**d. 改静态 IP**（先看网卡名 `ip -br a`，常见 `ens33` / `ens160`）
```bash
ip -br a
sudo tee /etc/network/interfaces >/dev/null <<'EOF'
source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

auto ens33
iface ens33 inet static
    address 192.168.152.10/24
    gateway 192.168.152.2
    dns-nameservers 192.168.152.2 1.1.1.1
EOF
sudo systemctl restart networking    # 或 sudo ifdown ens33 && sudo ifup ens33
ip -br a                             # 确认地址生效
ping -c2 1.1.1.1                     # 确认出网
```
> 网关/DNS 用 VMware NAT 的网关（在“虚拟网络编辑器”或 `vmnetdhcp.conf` 中查看，通常 `x.x.x.2`）。
> 静态 IP 只是建议；全部用 DHCP 也能练习，只要 4 台互通即可。

**e. 关闭 swap（kubelet 要求）**
```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab
free -h      # Swap 应为 0
```

**f. 安装常用工具 + 打开 SSH**
```bash
sudo apt update && sudo apt install -y curl wget vim jq open-vm-tools
sudo systemctl enable --now ssh
```
这样宿主机和 jumpbox 之间就能 `ssh debian@192.168.152.10`。建议在 jumpbox 上生成
SSH 密钥并分发到其他 3 台，便于统一操作。

**g. 打个快照**（VMware → Snapshot），作为干净基线。

## 4. 克隆出其余 3 台

1. 关机后 VMware → `Manage → Clone` → **Full clone**，分别命名为 `server`、`node-0`、`node-1`。
2. 克隆会生成新 MAC。先启动每台，改两处：
   - 主机名：`sudo hostnamectl set-hostname server`（对应 node-0 / node-1）
   - 静态 IP 的 `address`：改成 `.11` / `.12` / `.13`（网关、DNS 不变）
   - `sudo systemctl restart networking`
   - `/etc/hosts` 在克隆机里已是完整清单，无需再改。
3. 资源：把各台内存/CPU 调到第 01 章表里的值（克隆默认沿用源机）。

## 5. 验收（4 台互通）

在 `jumpbox` 上：
```bash
for h in 192.168.152.10 192.168.152.11 192.168.152.12 192.168.152.13; do
  echo "== $h =="
  ssh -o StrictHostKeyChecking=no debian@$h 'hostname; head -1 /etc/os-release'
done
```
四台都返回正确主机名与 `Debian GNU/Linux 12 (bookworm)` 即准备完成，可进入第 02 章
（第 01 章的机器要求与系统校验已由本章第 0、3 节覆盖）。

下一节：[设置跳板机](02-jumpbox.md)
