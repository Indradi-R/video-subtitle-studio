@echo off
title Build Video Subtitle Studio (Standalone EXE)
cd /d "%~dp0"
echo [*] Memeriksa virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment belum ditemukan. Menyiapkan...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)

echo [*] Menghasilkan asset logo & icon...
.venv\Scripts\python.exe scripts\generate_assets.py

echo [*] Menjalankan build PyInstaller...
.venv\Scripts\python.exe scripts\build_exe.py

echo.
pause
