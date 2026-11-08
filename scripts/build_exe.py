import os
import sys
import dis
from pathlib import Path

# Fix Python 3.10.0 stdlib dis.py IndexError bug (fixed in 3.10.1+)
_orig_get_const_info = dis._get_const_info
def _safe_get_const_info(const_index, const_list):
    argval = const_index
    if const_list is not None and const_index < len(const_list):
        argval = const_list[const_index]
    return argval, repr(argval)
dis._get_const_info = _safe_get_const_info

import PyInstaller.__main__

def build():
    root = Path(__file__).resolve().parent.parent
    dist_dir = root / "dist"
    assets_dir = root / "assets"
    bin_dir = root / "bin"
    main_py = root / "main.py"

    ffmpeg_exe = bin_dir / "ffmpeg.exe"
    icon_ico = assets_dir / "icon.ico"

    if not ffmpeg_exe.is_file():
        print(f"[!] Error: ffmpeg.exe not found at {ffmpeg_exe}")
        sys.exit(1)

    if not icon_ico.is_file():
        print(f"[!] Error: icon.ico not found at {icon_ico}")
        sys.exit(1)

    print("==================================================")
    print(" 🚀 Building Portable VideoSubtitleStudio.exe")
    print("==================================================")

    args = [
        "--noconsole",
        "--onefile",
        "--name=VideoSubtitleStudio",
        f"--icon={icon_ico}",
        f"--add-data={assets_dir};assets",
        f"--add-binary={ffmpeg_exe};bin",
        "--collect-all=customtkinter",
        "--clean",
        str(main_py)
    ]

    print("[*] PyInstaller arguments:\n ", "\n  ".join(args))
    
    try:
        PyInstaller.__main__.run(args)
    except Exception as e:
        print(f"\n[!] Build error: {e}")
        return False

    exe_file = dist_dir / "VideoSubtitleStudio.exe"
    if exe_file.is_file():
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        print("\n==================================================")
        print(" ✅ BUILD BERHASIL!")
        print(f" 📦 Lokasi Portable Executable: {exe_file}")
        print(f" 💾 Ukuran: {size_mb:.2f} MB")
        print(" Anda dapat langsung memindahkan file ini ke Desktop")
        print(" dan menjalankannya langsung tanpa instalasi apapun.")
        print("==================================================")
        return True

    print("\n[!] File executable tidak ditemukan di folder dist.")
    return False

if __name__ == "__main__":
    build()
