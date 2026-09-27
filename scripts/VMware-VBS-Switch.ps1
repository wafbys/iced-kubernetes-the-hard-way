<#
.SYNOPSIS
    为练习 Kubernetes The Hard Way (KTHW) 一键切换 VMware 嵌套虚拟化环境。

.DESCRIPTION
    KTHW (https://github.com/kelseyhightower/kubernetes-the-hard-way) 需要 4 台
    Debian 12 虚机(1 jumpbox + 1 server + 2 workers)连在同一网络。在 Windows + VMware
    Workstation/Player 上跑这些虚机时，宿主机若开着 VBS/内存完整性/Hyper-V，
    VMware 无法独占硬件虚拟化，性能会显著下降，且无法给虚机开启嵌套虚拟化。

    本脚本在两种状态间切换（切换后需重启生效）：

      vmware  : 关闭 VBS(Device Guard) / 内存完整性(HVCI) / Hyper-V / 虚拟化平台，
                并 bcdedit hypervisorlaunchtype=off。之后 VMware 可启用“虚拟化 Intel VT-x/
                AMD-V”以便在 guest 里跑 KTHW 的 control plane（单一 node 上跑 etcd/kube-apiserver 等）。
      restore : 恢复 Windows 默认安全配置（重新打开 VBS/HVCI/虚拟化平台）。

.PARAMETER Mode
    vmware | restore | status ；不带参数进入交互菜单。

.EXAMPLE
    .\VMware-VBS-Switch.ps1 vmware
    .\VMware-VBS-Switch.ps1 restore
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('vmware', 'restore', 'status')]
    [string]$Mode
)

# ---------- 自动提权 ----------
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "需要管理员权限，正在尝试提权..." -ForegroundColor Yellow
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"")
    if ($Mode) { $argList += $Mode }
    $hostExe = (Get-Process -Id $PID).Path
    if (-not $hostExe) { $hostExe = 'pwsh.exe' }
    Start-Process -FilePath $hostExe -ArgumentList $argList -Verb RunAs
    exit
}

$ErrorActionPreference = 'Stop'

# ---------- 辅助函数 ----------
function Write-Head($text) {
    Write-Host ""
    Write-Host ("=" * 62) -ForegroundColor DarkGray
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host ("=" * 62) -ForegroundColor DarkGray
}

function Set-RegValue {
    param([string]$Path, [string]$Name, $Value, [string]$Type = 'DWord')
    if (-not (Test-Path $Path)) { New-Item -Path $Path -Force | Out-Null }
    New-ItemProperty -Path $Path -Name $Name -Value $Value -PropertyType $Type -Force | Out-Null
    Write-Host "  [reg]  $Path\$Name = $Value" -ForegroundColor Green
}

function Set-BcdHypervisor {
    param([string]$Value)   # off | auto
    & bcdedit /set "{current}" hypervisorlaunchtype $Value | Out-Null
    Write-Host "  [bcd]  hypervisorlaunchtype = $Value" -ForegroundColor Green
}

function Set-OptionalFeature {
    param([string]$Name, [string]$State)   # Enable | Disable
    & dism.exe /Online /$State-Feature /FeatureName:$Name /NoRestart /Quiet 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [dism] $Name -> $State" -ForegroundColor Green
    } else {
        Write-Host "  [dism] $Name -> $State (不可用/已跳过)" -ForegroundColor DarkYellow
    }
}

function Show-Status {
    Write-Head "当前虚拟化相关状态"
    try {
        $dg = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard -ErrorAction Stop
        $vbsState = switch ($dg.VirtualizationBasedSecurityStatus) { 0 {'关闭'} 1 {'已启用未运行'} 2 {'运行中'} default {'未知'} }
        Write-Host ("  VBS                  : $vbsState (" + $dg.VirtualizationBasedSecurityStatus + ")") -ForegroundColor Gray
        Write-Host ("  运行中安全服务        : " + (($dg.SecurityServicesRunning) -join ', ') + "   (2=内存完整性/HVCI)") -ForegroundColor Gray
    } catch { Write-Host "  VBS                  : 读取失败" -ForegroundColor DarkYellow }

    $hvci = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' -ErrorAction SilentlyContinue
    Write-Host ("  内存完整性(HVCI)      : " + $(if ($null -ne $hvci.Enabled) { "Enabled=$($hvci.Enabled)" } else { '未设置' })) -ForegroundColor Gray
    $hv = (Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue).HypervisorPresent
    Write-Host ("  Hypervisor 运行中     : $hv") -ForegroundColor Gray
    $bcd = (& bcdedit /enum "{current}" 2>&1 | Out-String)
    $line = ($bcd -split "`r?`n" | Select-String -Pattern 'hypervisorlaunchtype').Line
    if (-not $line) { $line = "hypervisorlaunchtype 未显式设置(默认 auto)" }
    Write-Host ("  bcdedit              : " + $line.Trim()) -ForegroundColor Gray
}

function Switch-ToVMware {
    Write-Head "切换到 VMware 模式（关闭 VBS / 内存完整性 / Hyper-V）"

    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' 'EnableVirtualizationBasedSecurity' 0
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' 'RequirePlatformSecurityFeatures' 0
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' 'Enabled' 0
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' 'LsaCfgFlags' 0

    Set-OptionalFeature 'Microsoft-Hyper-V-All'  'Disable'
    Set-OptionalFeature 'VirtualMachinePlatform' 'Disable'
    Set-OptionalFeature 'HypervisorPlatform'     'Disable'

    Set-BcdHypervisor 'off'

    Write-Host ""
    Write-Host "  VMware 模式配置完成。" -ForegroundColor Yellow
    Write-Host "  重启后：打开 VMware 虚机设置 -> 处理器 -> 勾选“虚拟化 Intel VT-x/EPT 或 AMD-V/RVI”，" -ForegroundColor DarkGray
    Write-Host "  即可给 KTHW 的 Debian 虚机启用嵌套虚拟化。" -ForegroundColor DarkGray
}

function Switch-ToRestore {
    Write-Head "恢复 Windows 安全模式（重新开启 VBS / 内存完整性 / Hyper-V）"

    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' 'EnableVirtualizationBasedSecurity' 1
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' 'RequirePlatformSecurityFeatures' 1
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' 'Enabled' 1

    try {
        Remove-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name 'LsaCfgFlags' -ErrorAction SilentlyContinue
        Write-Host "  [reg]  Lsa\LsaCfgFlags 已删除（恢复系统默认）" -ForegroundColor Green
    } catch {}

    Set-OptionalFeature 'VirtualMachinePlatform' 'Enable'
    Set-OptionalFeature 'HypervisorPlatform'     'Enable'

    Set-BcdHypervisor 'auto'

    Write-Host ""
    Write-Host "  安全模式配置完成。" -ForegroundColor Yellow
}

function Prompt-Reboot {
    Write-Host ""
    $ans = Read-Host "是否立即重启以使更改生效？(y/N)"
    if ($ans -match '^(y|yes|是)$') {
        Write-Host "  正在重启..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        Restart-Computer -Force
    } else {
        Write-Host "  已跳过重启，请稍后手动重启。" -ForegroundColor DarkGray
    }
}

# ---------- 主流程 ----------
if (-not $Mode) {
    Write-Head "KTHW / VMware 一键切换"
    Write-Host "  1) 切换到 VMware 模式  (关闭 VBS/内存完整性/Hyper-V) —— 练习 KTHW 前使用"
    Write-Host "  2) 恢复安全模式        (重新开启 VBS/内存完整性/Hyper-V)"
    Write-Host "  3) 仅查看当前状态" -ForegroundColor DarkGray
    Write-Host ""
    $choice = Read-Host "请选择 [1/2/3]"
    switch ($choice) {
        '1' { $Mode = 'vmware' }
        '2' { $Mode = 'restore' }
        '3' { $Mode = 'status' }
        default { Write-Host "无效选择，退出。" -ForegroundColor Red; exit 1 }
    }
}

Show-Status

switch ($Mode) {
    'vmware'  { Switch-ToVMware;  Prompt-Reboot }
    'restore' { Switch-ToRestore; Prompt-Reboot }
    'status'  { }
}
