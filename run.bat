@echo off
title Video Subtitle Studio
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment belum ditemukan. Menyiapkan...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)
echo [*] Menjalankan Video Subtitle Studio...
start "" ".venv\Scripts\pythonw.exe" main.py
exit
