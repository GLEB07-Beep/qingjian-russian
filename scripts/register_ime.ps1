# 检查并请求管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "正在请求管理员权限以注册 Windows 输入法服务..." -ForegroundColor Cyan
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$repo = (Resolve-Path "$PSScriptRoot\..").Path
$dll = Join-Path $repo "target\release\qingjian_tsf.dll"
$server = Join-Path $repo "target\release\qingjian-server.exe"

if (-not (Test-Path $dll)) {
    Write-Host "错误: 未找到 $dll ，请先构建 release 产物。" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "1. 正在注册 TSF 文本服务动态链接库..." -ForegroundColor Green
& regsvr32.exe /s "$dll"

$tip = "0804:{4FDCA82D-E923-49BF-9E75-BB906B93B8BB}{8119F8E0-CF81-423B-9189-C0D7374324B3}"

Write-Host "2. 正在将青简·俄语专版添加到当前用户语言列表..." -ForegroundColor Green
try {
    $list = Get-WinUserLanguageList
    $zh = $list | Where-Object { $_.LanguageTag -like "zh*" }
    if ($zh) {
        if (-not $zh.InputMethodTips.Contains($tip)) {
            $zh.InputMethodTips.Insert(0, $tip)
            Set-WinUserLanguageList $list -Force
        }
        Set-WinDefaultInputMethodOverride -InputTip $tip
        Write-Host "3. 已将默认输入法切换为: 青简·俄语专版！" -ForegroundColor Green
    } else {
        Write-Host "提示: 系统未安装中文语言包，请在设置中先添加中文语言。" -ForegroundColor Yellow
    }
} catch {
    Write-Host "设置系统默认输入法提示: $_" -ForegroundColor Yellow
}

Write-Host "4. 正在启动输入法后台服务 (qingjian-server.exe)..." -ForegroundColor Green
Get-Process qingjian-server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Process "$server" -WorkingDirectory "$repo" -WindowStyle Hidden

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 安装与默认切换完成！" -ForegroundColor Cyan
Write-Host " 现在您可以在任意应用（微信、记事本、浏览器）中直接打字体验俄语释义！" -ForegroundColor Cyan
Write-Host " 快捷键: Win + 空格 可随时切换输入法" -ForegroundColor Yellow
Write-Host " 如需恢复原输入法，请运行同目录下的 unregister_ime.ps1" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Start-Sleep -Seconds 3
