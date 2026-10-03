@echo off
cd /d "%~dp0"
echo ============================================================
echo   Installing Qingjian-RU (Qingjian Russian Edition IME)
echo ============================================================
echo.

echo [1/3] Registering TSF DLL...
if exist "%~dp0qingjian_tsf.dll" (
    regsvr32.exe /s "%~dp0qingjian_tsf.dll"
) else if exist "%~dp0target\release\qingjian_tsf.dll" (
    regsvr32.exe /s "%~dp0target\release\qingjian_tsf.dll"
)

echo [2/3] Setting Qingjian-RU in Windows Language List...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$list = Get-WinUserLanguageList; $zh = $list | Where-Object { $_.LanguageTag -like 'zh*' }; $tip = '0804:{4FDCA82D-E923-49BF-9E75-BB906B93B8BB}{8119F8E0-CF81-423B-9189-C0D7374324B3}'; if ($zh) { if (-not $zh.InputMethodTips.Contains($tip)) { $zh.InputMethodTips.Insert(0, $tip); Set-WinUserLanguageList $list -Force }; Set-WinDefaultInputMethodOverride -InputTip $tip; Write-Host 'SUCCESS: Default input method updated!' -ForegroundColor Green }"

echo [3/3] Starting Qingjian-RU Server...
taskkill /F /IM qingjian-server.exe >nul 2>&1
if exist "%~dp0qingjian-server.exe" (
    start "" "%~dp0qingjian-server.exe"
) else if exist "%~dp0target\release\qingjian-server.exe" (
    start "" "%~dp0target\release\qingjian-server.exe"
)

echo.
echo ============================================================
echo   INSTALLATION COMPLETED!
echo   Switch input methods via: Win + Space
echo ============================================================
echo.
pause
