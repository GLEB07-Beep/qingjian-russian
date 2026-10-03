import os
import shutil
import zipfile

def package():
    dist_dir = 'dist/Qingjian-RU-v0.1.5-windows-x64'
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.makedirs(f'{dist_dir}/data/generated', exist_ok=True)
    os.makedirs(f'{dist_dir}/assets/levels', exist_ok=True)

    # 1. Binaries & DLLs
    src_release = 'target/release'
    for f in os.listdir(src_release):
        if f.endswith('.exe') or f.endswith('.dll') or f.endswith('.pri'):
            shutil.copy2(os.path.join(src_release, f), os.path.join(dist_dir, f))

    # 2. Dict & Glossary
    for f in ['dict.qj', 'glossary-ru.qj']:
        src = os.path.join('data/generated', f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dist_dir, 'data/generated', f))

    # 3. Levels
    shutil.copy2('assets/levels/levels-ru.tsv', os.path.join(dist_dir, 'assets/levels/levels-ru.tsv'))

    # 4. Install & Uninstall scripts
    install_script = """@echo off
cd /d "%~dp0"
echo ============================================================
echo   Installing Qingjian-RU (Qingjian Russian Edition IME)
echo ============================================================
echo.

echo [1/3] Registering TSF DLL...
if exist "%~dp0qingjian_tsf.dll" (
    regsvr32.exe /s "%~dp0qingjian_tsf.dll"
) else if exist "%~dp0target\\release\\qingjian_tsf.dll" (
    regsvr32.exe /s "%~dp0target\\release\\qingjian_tsf.dll"
)

echo [2/3] Setting Qingjian-RU in Windows Language List...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$list = Get-WinUserLanguageList; $zh = $list | Where-Object { $_.LanguageTag -like 'zh*' }; $tip = '0804:{4FDCA82D-E923-49BF-9E75-BB906B93B8BB}{8119F8E0-CF81-423B-9189-C0D7374324B3}'; if ($zh) { if (-not $zh.InputMethodTips.Contains($tip)) { $zh.InputMethodTips.Insert(0, $tip); Set-WinUserLanguageList $list -Force }; Set-WinDefaultInputMethodOverride -InputTip $tip; Write-Host 'SUCCESS: Default input method updated!' -ForegroundColor Green }"

echo [3/3] Starting Qingjian-RU Server...
taskkill /F /IM qingjian-server.exe >nul 2>&1
if exist "%~dp0qingjian-server.exe" (
    start "" "%~dp0qingjian-server.exe"
) else if exist "%~dp0target\\release\\qingjian-server.exe" (
    start "" "%~dp0target\\release\\qingjian-server.exe"
)

echo.
echo ============================================================
echo   INSTALLATION COMPLETED!
echo   Switch input methods via: Win + Space
echo ============================================================
echo.
pause
"""

    uninstall_script = """@echo off
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
) else if exist "%~dp0target\\release\\qingjian_tsf.dll" (
    regsvr32.exe /u /s "%~dp0target\\release\\qingjian_tsf.dll"
)

echo.
echo ============================================================
echo   UNINSTALL COMPLETED: Qingjian-RU has been unregistered.
echo ============================================================
echo.
pause
"""

    with open(f'{dist_dir}/install.bat', 'w', encoding='ascii') as f:
        f.write(install_script)

    with open(f'{dist_dir}/uninstall.bat', 'w', encoding='ascii') as f:
        f.write(uninstall_script)

    with open('install.bat', 'w', encoding='ascii') as f:
        f.write(install_script)

    with open('restore.bat', 'w', encoding='ascii') as f:
        f.write(uninstall_script)

    # 5. Zip
    zip_path = 'dist/Qingjian-RU-v0.1.5-windows-x64.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(dist_dir):
            for f in files:
                p = os.path.join(root, f)
                arcname = os.path.relpath(p, 'dist')
                z.write(p, arcname)

    print(f"Successfully created release zip: {zip_path}, size: {os.path.getsize(zip_path)} bytes")

if __name__ == '__main__':
    package()
