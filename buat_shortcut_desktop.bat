@echo off
title Buat Shortcut Desktop
cd /d "%~dp0"

set "TARGET_EXE=%~dp0dist\VideoSubtitleStudio.exe"
set "ICON_FILE=%~dp0assets\icon.ico"
set "WORKING_DIR=%~dp0"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Video Subtitle Studio.lnk"

if not exist "%TARGET_EXE%" (
    echo [!] File dist\VideoSubtitleStudio.exe belum ditemukan.
    echo [*] Menjalankan build terlebih dahulu...
    call build.bat
)

echo [*] Membuat shortcut di Desktop: "%SHORTCUT_PATH%"...

powershell -NoProfile -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); " ^
    "$Shortcut.TargetPath = '%TARGET_EXE%'; " ^
    "$Shortcut.WorkingDirectory = '%WORKING_DIR%'; " ^
    "$Shortcut.IconLocation = '%ICON_FILE%'; " ^
    "$Shortcut.Description = 'Aplikasi Video Soft-Sub Scraper & Translator'; " ^
    "$Shortcut.Save(); "

if exist "%SHORTCUT_PATH%" (
    echo.
    echo ==================================================
    echo  [SUCCESS] Shortcut berhasil dibuat di Desktop Anda!
    echo  Nama: Video Subtitle Studio
    echo ==================================================
) else (
    echo [!] Gagal membuat shortcut secara otomatis.
    echo Anda dapat menyalin file "%TARGET_EXE%" langsung ke Desktop Anda.
)

echo.
pause
