@echo off
title Push ke GitHub - Video Subtitle Studio
cd /d "%~dp0"

echo =======================================================
echo   🚀 Push Video Subtitle Studio ke GitHub
echo =======================================================
echo.

git remote remove origin >nul 2>&1

set /p REPO_URL="Masukkan URL Repository GitHub Anda (misal: https://github.com/username/videoTranslator.git): "

if "%REPO_URL%"=="" (
    echo [!] URL tidak boleh kosong. Dibatalkan.
    echo.
    pause
    exit /b
)

echo.
echo [*] Menghubungkan remote origin ke: %REPO_URL%...
git remote add origin %REPO_URL%

echo [*] Mengatur branch utama ke 'main'...
git branch -M main

echo [*] Melakukan push commit ke GitHub...
git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo =======================================================
    echo  [SUCCESS] Proyek berhasil di-push ke GitHub!
    echo =======================================================
) else (
    echo [!] Push gagal. Pastikan repository telah dibuat di GitHub
    echo     dan Anda telah login dengan akun GitHub Anda.
)

echo.
pause
