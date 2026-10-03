# 检查并请求管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "正在请求管理员权限以还原输入法设置..." -ForegroundColor Cyan
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$repo = (Resolve-Path "$PSScriptRoot\..").Path
$dll = Join-Path $repo "target\release\qingjian_tsf.dll"

Write-Host "1. 正在停止后台 Server 服务..." -ForegroundColor Yellow
Get-Process qingjian-server -ErrorAction SilentlyContinue | Stop-Process -Force

$tip = "0804:{4FDCA82D-E923-49BF-9E75-BB906B93B8BB}{8119F8E0-CF81-423B-9189-C0D7374324B3}"

Write-Host "2. 正在恢复系统默认输入法覆盖..." -ForegroundColor Yellow
try {
    Set-WinDefaultInputMethodOverride -InputTip ""
    $list = Get-WinUserLanguageList
    $zh = $list | Where-Object { $_.LanguageTag -like "zh*" }
    if ($zh -and $zh.InputMethodTips.Contains($tip)) {
        $zh.InputMethodTips.Remove($tip) | Out-Null
        Set-WinUserLanguageList $list -Force
    }
} catch {
    Write-Host "警告: $($_)" -ForegroundColor Red
}

if (Test-Path $dll) {
    Write-Host "3. 正在反注册 TSF DLL 服务..." -ForegroundColor Yellow
    & regsvr32.exe /u /s "$dll"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " 已成功还原系统默认输入法并退出青简服务！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 3
