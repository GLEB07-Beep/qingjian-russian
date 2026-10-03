@echo off
cd /d "%~dp0"
echo ============================================================
echo   Uninstalling Qingjian-RU (Qingjian Russian Edition IME)
echo ============================================================
echo.

echo [1/3] Stopping Server...
taskkill /F /IM qingjian-server.exe >nul 2>&1

echo [2/3] Restoring original default input method...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-WinDefaultInputMethodOverride -InputTip ''; $list = Get-WinUserLanguageList; $zh = $list | Where-Object { $_.LanguageTag -like 'zh*' }; $tip = '0804:{4FDCA82D-E923-49BF-9E75-BB906B93B8BB}{8119F8E0-CF81-423B-9189-C0D7374324B3}'; if ($zh -and $zh.InputMethodTips.Contains($tip)) { $zh.InputMethodTips.Remove($tip) | Out-Null; Set-WinUserLanguageList $list -Force }; Write-Host 'SUCCESS: Restored original default input method.' -ForegroundColor Green"

echo [3/3] Unregistering TSF DLL...
if exist "%~dp0qingjian_tsf.dll" (
    regsvr32.exe /u /s "%~dp0qingjian_tsf.dll"
) else if exist "%~dp0target\release\qingjian_tsf.dll" (
    regsvr32.exe /u /s "%~dp0target\release\qingjian_tsf.dll"
)

echo.
echo ============================================================
echo   UNINSTALL COMPLETED: Qingjian-RU has been unregistered.
echo ============================================================
echo.
pause
