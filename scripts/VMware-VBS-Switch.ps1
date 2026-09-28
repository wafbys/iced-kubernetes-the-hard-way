<#
.SYNOPSIS
    为练习 Kubernetes The Hard Way (KTHW) 一键切换 VMware 嵌套虚拟化环境。

.DESCRIPTION
    KTHW (https://github.com/kelseyhightower/kubernetes-the-hard-way) 需要 4 台
    Debian 12 虚机(1 jumpbox + 1 server + 2 workers)连在同一网络。在 Windows + VMware
    Workstation/Player 上跑这些虚机时，宿主机若开着 VBS/内存完整性/Hyper-V，
    VMware 无法独占硬件虚拟化(VT-x/AMD-V)，虚机性能会显著下降。
    注意：KTHW 本身不需要嵌套虚拟化（guest 里只跑 etcd/kube-apiserver/containerd
    等进程）；只有你要在 Debian guest 里再运行虚机/模拟器时才需要。

    本脚本在两种状态间切换（切换后需重启生效）：

      vmware  : 关闭 VBS(Device Guard) / 内存完整性(HVCI) / Hyper-V / 虚拟化平台，
                并 bcdedit hypervisorlaunchtype=off，让 VMware 独占硬件虚拟化、恢复性能。
      restore : 按 vmware 模式记录的原始功能状态，恢复 VBS/HVCI/虚拟化平台/Hyper-V。

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

# ---------- 状态记录（vmware 模式保存原始状态，restore 据此恢复） ----------
$FeatureNames = @('Microsoft-Hyper-V-All', 'VirtualMachinePlatform', 'HypervisorPlatform')
$StateDir     = Join-Path $env:ProgramData 'VMware-VBS-Switch'
$StateFile    = Join-Path $StateDir 'features.json'

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

function Get-FeatureState {
    param([string]$Name)
    # 用 Win32_OptionalFeature(WMI) 读状态，约 0.1~1 秒。
    # 不要用 Get-WindowsOptionalFeature -Online：它会为每个功能启动一次 DISM 联机会话，
    # 动辄数分钟且期间无任何输出，看起来就像卡死。
    try {
        $f = Get-CimInstance Win32_OptionalFeature -Filter "Name='$Name'" -ErrorAction Stop
        switch ([int]$f.InstallState) {
            1 { 'Enabled' }
            2 { 'Disabled' }
            3 { 'Absent' }
            default { 'Unknown' }
        }
    } catch {
        'Unknown'
    }
}

function Set-OptionalFeature {
    param([string]$Name, [string]$State)   # Enable | Disable
    $target = if ($State -eq 'Enable') { 'Enabled' } else { 'Disabled' }

    if ((Get-FeatureState $Name) -eq $target) {
        Write-Host "  [dism] $Name 已是 $target，跳过" -ForegroundColor DarkGray
        return
    }

    Write-Host "  [dism] $Name -> $State ...（DISM 可能要几分钟，请勿关闭窗口）" -ForegroundColor DarkYellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    # 2>&1 把原生命令的 stderr 并进输出流：否则在 $ErrorActionPreference='Stop' 下
    # DISM 往 stderr 写一行就会被当成 NativeCommandError 直接终止脚本。
    & dism.exe /Online /$State-Feature /FeatureName:$Name /NoRestart 2>&1 |
        ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    $code = $LASTEXITCODE
    $sw.Stop()
    if ($code -eq 0) {
        Write-Host ("  [dism] $Name -> $State 完成（{0:N0}s）" -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green
    } else {
        Write-Host ("  [dism] $Name -> $State 失败/不可用（exit=$code, {0:N0}s）" -f $sw.Elapsed.TotalSeconds) -ForegroundColor DarkYellow
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

    # 先读取并记录原始状态，再改注册表。
    # （顺序不能反：RequirePlatformSecurityFeatures 被写成 0 之后就再也读不到原值了。）
    Write-Host "  正在读取当前 Windows 功能状态..." -ForegroundColor DarkGray
    $prevFeatures = [ordered]@{}
    foreach ($f in $FeatureNames) { $prevFeatures[$f] = Get-FeatureState $f }
    $prevRpsf = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' `
        -Name 'RequirePlatformSecurityFeatures' -ErrorAction SilentlyContinue).RequirePlatformSecurityFeatures
    $state = [ordered]@{
        recordedAt = (Get-Date).ToString('s')
        features   = $prevFeatures
        requirePlatformSecurityFeatures = $prevRpsf
    }
    New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
    $state | ConvertTo-Json -Depth 3 | Set-Content -Path $StateFile -Encoding UTF8
    Write-Host "  [state] 已记录原始状态 -> $StateFile" -ForegroundColor Green

    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' 'EnableVirtualizationBasedSecurity' 0
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' 'RequirePlatformSecurityFeatures' 0
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' 'Enabled' 0
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' 'LsaCfgFlags' 0

    foreach ($f in $FeatureNames) { Set-OptionalFeature $f 'Disable' }

    Set-BcdHypervisor 'off'

    Write-Host ""
    Write-Host "  VMware 模式配置完成。" -ForegroundColor Yellow
    Write-Host "  重启后 VMware 即可独占硬件虚拟化、恢复性能。" -ForegroundColor DarkGray
    Write-Host "  （KTHW 不需要嵌套虚拟化；如需在 guest 内再开虚机，可勾选处理器中的“虚拟化 Intel VT-x/EPT 或 AMD-V/RVI”。）" -ForegroundColor DarkGray
}

function Switch-ToRestore {
    Write-Head "恢复 Windows 安全模式（重新开启 VBS / 内存完整性 / Hyper-V）"

    $recorded = $null
    if (Test-Path $StateFile) {
        try { $recorded = Get-Content $StateFile -Raw | ConvertFrom-Json } catch { $recorded = $null }
    }

    $rpsf = 1
    if ($null -ne $recorded.requirePlatformSecurityFeatures) {
        $rpsf = [int]$recorded.requirePlatformSecurityFeatures
    }

    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' 'EnableVirtualizationBasedSecurity' 1
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' 'RequirePlatformSecurityFeatures' $rpsf
    Set-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' 'Enabled' 1

    try {
        Remove-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name 'LsaCfgFlags' -ErrorAction SilentlyContinue
        Write-Host "  [reg]  Lsa\LsaCfgFlags 已删除（恢复系统默认）" -ForegroundColor Green
    } catch {}

    $prevFeatures = @{}
    if ($recorded.features) {
        foreach ($prop in $recorded.features.PSObject.Properties) { $prevFeatures[$prop.Name] = [string]$prop.Value }
    }
    if ($prevFeatures.Count -gt 0) {
        foreach ($f in $FeatureNames) {
            $was = $prevFeatures[$f]
            if ($was -eq 'Enabled') {
                Set-OptionalFeature $f 'Enable'
            } else {
                Write-Host "  [dism] $f 原状态为 $(if ($was) { $was } else { '无记录' })，不启用" -ForegroundColor DarkGray
            }
        }
    } else {
        Write-Host "  [state] 未找到切换前记录（$StateFile），按默认恢复虚拟化平台" -ForegroundColor DarkYellow
        Set-OptionalFeature 'VirtualMachinePlatform' 'Enable'
        Set-OptionalFeature 'HypervisorPlatform'     'Enable'
    }

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
