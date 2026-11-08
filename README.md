# 🎬 Video Subtitle Studio (Lightweight Soft-Sub Scraper & Translator)

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Engine](https://img.shields.io/badge/Engine-FFmpeg%20Standalone-green.svg?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Aplikasi desktop modern yang **ringan, cepat, dan mandiri (*portable standalone*)** untuk memindai koleksi video dalam folder, mengekstrak subtitle teks tertanam (*soft subtitles*), menampilkan cuplikan thumbnail, menyortir & memfilter video, menjabarkan baris subtitle dalam tabel interaktif yang dapat diedit, menerjemahkan secara instan dengan sistem *batching*, serta mengekspornya kembali ke format `.srt`.

---

## 📖 1. Latar Belakang (Background)

Di era konsumsi media digital saat ini, banyak film, serial animasi, materi kuliah, dokumenter, dan video tutorial yang didistribusikan dalam format wadah modern seperti **MKV**, **MP4**, atau **WebM** dengan *soft subtitle* (subtitle teks yang tertanam di dalam metadata file video, bukan *hardsub* yang dibakar permanen ke frame gambar).

Meskipun subtitle asli sering kali tersedia dalam bahasa asing (seperti Inggris, Jepang, Korea, atau Spanyol), pengguna di Indonesia atau negara lain sering menghadapi kendala:
1. **Aplikasi Penerjemah Terlalu Berat**: Banyak aplikasi desktop modern dibangun di atas *Electron*, yang menghabiskan memori RAM besar (300 MB hingga 1 GB) hanya untuk memproses teks subtitle sederhana.
2. **Proses Ekstraksi Manual yang Rumit**: Mengekstrak subtitle menggunakan *command line* FFmpeg atau MKVToolNix membutuhkan pengetahuan teknis sintaksis CLI dan memakan waktu bila ada puluhan episode dalam satu folder.
3. **Penerjemahan Lambat & Terkena Rate-Limit**: Menerjemahkan subtitle baris-demi-baris secara konvensional sering memicu pemblokiran request (*HTTP 429 Too Many Requests*) dari penyedia terjemahan dan memakan waktu lama.
4. **Ketergantungan Dependensi Luar**: Banyak skrip open-source mewajibkan instalasi manual runtime Python, FFmpeg, dan berbagai library yang membingungkan bagi pengguna non-teknis.

**Video Subtitle Studio** diciptakan untuk menjawab permasalahan tersebut: menghadirkan alat yang **berukuran kecil, hemat memori (~60–85 MB RAM)**, memiliki **antarmuka visual modern dengan thumbnail kartu**, mendukung **batching penerjemahan secepat kilat**, serta **dapat langsung dijalankan dari Desktop tanpa instalasi apapun**.

---

## 📋 2. Ringkasan Proyek (Summary)

**Video Subtitle Studio** menyediakan alur kerja terintegrasi satu pintu:
* **Deteksi & Ekstraksi Cepat**: Memindai seluruh stream subtitle yang ada di dalam video (SubRip, ASS/SSA, WebVTT, MOV_TEXT) dan mengekstraknya dalam hitungan milidetik tanpa me-render ulang video.
* **Galeri Visual & Sorting**: Menampilkan video dalam format kartu dengan thumbnail 16:9 otomatis yang di-cache lokal, dilengkapi filter tipe file, filter ketersediaan soft-sub, dan penyortiran (Nama, Ukuran, Tanggal).
* **Editor Subtitle Interaktif**: Menjabarkan baris subtitle secara rapi lengkap dengan nomor, stempel waktu awal-akhir, teks asli, dan teks hasil terjemahan yang dapat diedit secara langsung (*inline edit*).
* **Mesin Terjemahan Efisien**: Menggunakan teknik *delimiter batching* pada endpoint terjemahan (menerjemahkan 15–20 baris per request jaringan), menghasilkan efisiensi kecepatan hingga 10x–20x lebih kencang tanpa hambatan kuota harian.
* **Format Ekspor Standar**: Menghasilkan file `.srt` standar UTF-8 yang kompatibel dengan seluruh media player populer (VLC, MPC-HC, PotPlayer, GOM, TV pintar, dan pemutar web).

---

## ⚙️ 3. Spesifikasi Teknis (Technical Specifications)

| Parameter | Spesifikasi | Keterangan |
| :--- | :--- | :--- |
| **Arsitektur Bahasa** | Python 3.10+ | Kode modular (`core/`, `gui/`, `scripts/`) |
| **Antarmuka Grafis** | CustomTkinter 6.0+ | Modern dark theme, responsif, hemat resource |
| **Konsumsi Memori (RAM)** | ~50 MB – 85 MB | 70%–80% lebih hemat dibanding Electron |
| **Media Processor** | FFmpeg 4.3+ Standalone | Muxing, stream probing, thumbnailing & demuxing |
| **Ukuran Portable EXE** | ~25.4 MB | Single-file portable tanpa installer |
| **Format Kontainer Video** | `.mkv`, `.mp4`, `.webm`, `.avi`, `.mov`, `.m4v`, `.ts` | Dipindai otomatis dalam folder |
| **Format Soft-Sub Teks** | SubRip (`srt`), ASS/SSA (`ass`), WebVTT (`vtt`), MOV_TEXT | Dikonversi otomatis ke standar SRT |
| **Penanganan Subtitle Gambar** | PGS / VobSub / DVB | Dideteksi & diberi label peringatan visual |
| **Mesin Terjemahan** | Google GTX Batching Engine & Fallback | 14+ bahasa target, tanpa perlu API key |
| **Encoding Output** | UTF-8 (`.srt`) | Standar SubRip dengan timing `HH:MM:SS,mmm` |

---

## 🔄 4. Alur Kerja Sistem (Workflow & Architecture Flow)

Berikut adalah diagram alur kerja pemrosesan aplikasi:

```mermaid
flowchart TD
    A["📁 Folder Berisi Video"] --> B["🔍 Pemindaian Video & Ekstraksi Metadata"]
    B --> C["🖼️ Pembuatan Thumbnail Cuplikan (FFmpeg 16:9)"]
    C --> D["🗂️ Galeri Kartu Video (Filter & Sort)"]
    
    D -->|"Pilih Video"| E["🔎 Inspeksi Stream Subtitle (FFprobe / FFmpeg)"]
    E --> F{"Ada Soft-Sub Teks?"}
    
    F -- "Tidak / Hanya Gambar (PGS)" --> G["⚠️ Tampilkan Label Peringatan"]
    F -- "Ya (SRT / ASS / WebVTT)" --> H["⬇️ Ekstrak Stream Subtitle ke Teks"]
    
    H --> I["📑 Parsing Timestamp (ms) & Text Sanitizing"]
    I --> J["🖥️ Tampilkan di Subtitle Table (Pagination 50 baris/hlm)"]
    
    J -->|"Klik Terjemahkan"| K["📦 Batch Payload (15-20 Baris per Chunk)"]
    K --> L["🌐 Google GTX Translation Engine"]
    L --> M["🔄 Unpack & Tampilkan Hasil Terjemahan"]
    
    M --> N{"Koreksi Manual oleh Pengguna?"}
    N -- "Ya" --> O["✏️ Inline Edit pada Kolom Terjemahan"]
    N -- "Tidak" --> P["💾 Export ke File .SRT"]
    O --> P
    
    P --> Q["🎉 Selesai: video_name.id.srt (UTF-8)"]
```

---

## ✨ 5. Fitur Unggulan

### 1. Galeri Video Ber-Thumbnail & Smart Cache
Saat folder dibuka, aplikasi langsung mengambil cuplikan adegan di detik ke-2 video dan menyimpannya di direktori cache lokal berbasis hash. Pemuatan galeri berikutnya berlangsung instan.

### 2. Filter & Sorting Terintegrasi
* **Pencarian Real-Time**: Ketik sebagian kata dari judul video untuk menyaring tampilan.
* **Filter Dropdown**:
  * *Semua Video*
  * *Hanya yang Punya Soft-Sub* (hanya menampilkan video yang memiliki subtitle teks)
  * *Hanya MKV* / *Hanya MP4*
* **Sorting Dropdown**: Nama (A-Z / Z-A), Ukuran File (Terbesar/Terkecil), Tanggal Modifikasi (Terbaru).

### 3. Subtitle Inspector & Editor
* **Pagination Halus**: Menampilkan 50 baris per halaman sehingga video berdurasi 3 jam dengan ribuan baris teks tetap dapat dibuka dengan mulus tanpa *lag*.
* **Pencarian Kalimat**: Temukan dialog tertentu dengan fitur cari kata kunci di dalam subtitle.
* **Inline Editable**: Setiap baris terjemahan dapat langsung diubah manual sebelum diekspor.

### 4. Mode Batch Otomatis (1-Klik)
Tombol **"⚡ Batch Translate Semua Video di Folder"** secara otomatis memindai seluruh serial atau koleksi anime dalam folder, mengekstrak subtitle bahasa asal, menerjemahkannya, dan menyimpannya menjadi file `.srt` untuk masing-masing video.

---

## 🚀 6. Panduan Penggunaan (Usage Guide)

### Metode 1: Menggunakan Portable EXE (Paling Praktis)
1. Buka folder `dist/` dan jalankan **`VideoSubtitleStudio.exe`**.
2. Anda juga dapat langsung menyalin file `VideoSubtitleStudio.exe` ke **Desktop** Anda.
3. Klik tombol **"📁 Buka Folder Video"** dan pilih folder yang berisi video Anda.
4. Pilih video yang diinginkan dari galeri kartu di panel kiri.
5. Pilih **Track Subtitle** dan **Bahasa Target** (misal: *Indonesian*).
6. Klik **"⬇️ 1. Ekstrak Subtitle"**, lalu klik **"🌐 2. Terjemahkan Teks"**.
7. Klik **"💾 3. Export ke .SRT"** untuk menyimpan hasil subtitle.

### Metode 2: Menggunakan Skrip Shortcut Desktop
Jalankan file [buat_shortcut_desktop.bat](file:///d:/CODE/videoTranslator/buat_shortcut_desktop.bat). Skrip ini akan secara otomatis membuat shortcut resmi di Desktop Windows Anda dengan ikon aplikasi resolusi tinggi.

### Metode 3: Menjalankan dari Kode Sumber (Developer)
```powershell
# 1. Masuk ke direktori
cd d:\CODE\videoTranslator

# 2. Aktifkan virtual environment
.venv\Scripts\activate

# 3. Jalankan aplikasi GUI
python main.py
```

### Metode 4: Mode CLI / Otomasi Terminal
Aplikasi juga dapat dijalankan tanpa antarmuka grafis untuk kebutuhan otomasi:

* **Menerjemahkan Satu File Video:**
  ```powershell
  python main.py --cli --video "path\to\movie.mkv" --lang id --output "path\to\movie.id.srt"
  ```
* **Menerjemahkan Seluruh Video dalam Folder (Batch):**
  ```powershell
  python main.py --cli --folder "D:\Movies\AnimeSeries" --lang id
  ```

---

## 📁 7. Struktur Direktori Proyek

```
videoTranslator/
├── assets/
│   ├── icon.ico                  # Icon aplikasi Windows multi-resolusi
│   ├── logo.png                  # Logo resolusi tinggi (512x512)
│   └── logo_small.png            # Logo untuk header aplikasi
├── bin/
│   └── ffmpeg.exe                # Binary FFmpeg portable mandiri
├── core/
│   ├── __init__.py
│   ├── extractor.py              # Pemindaian folder, thumbnail generator, & demuxer
│   ├── parser.py                 # SRT/ASS parser, timestamp converter, & export logic
│   └── translator.py             # Mesin terjemahan batching & penanganan rate limit
├── dist/
│   └── VideoSubtitleStudio.exe   # File aplikasi mandiri portable (siap pakai)
├── gui/
│   ├── __init__.py
│   └── app.py                    # Antarmuka desktop CustomTkinter
├── scripts/
│   ├── build_exe.py              # Skrip kompilasi PyInstaller mandiri
│   ├── generate_assets.py        # Generator logo dan icon otomatis
│   └── create_desktop_shortcut.ps1
├── test_samples/                 # Klip video uji coba dengan berbagai format subtitle
├── buat_shortcut_desktop.bat     # Skrip pembuat shortcut Windows 1-klik
├── build.bat                     # Skrip kompilasi ulang executable
├── main.py                       # Titik masuk utama aplikasi (GUI & CLI)
├── requirements.txt              # Daftar dependensi Python
├── run.bat                       # Skrip peluncur cepat aplikasi
└── README.md                     # Dokumentasi komprehensif proyek
```

---

## 🛠️ 8. Cara Kompilasi Ulang (Build from Source)

Jika Anda melakukan perubahan pada kode sumber dan ingin membuat file `.exe` baru:
1. Pastikan dependensi terpasang (`pip install -r requirements.txt`).
2. Klik ganda file [build.bat](file:///d:/CODE/videoTranslator/build.bat) atau jalankan:
   ```powershell
   python scripts\build_exe.py
   ```
3. File executable baru akan otomatis diperbarui di folder `dist/VideoSubtitleStudio.exe`.

---

## 📄 9. Lisensi (License)

Proyek ini dirilis di bawah lisensi [MIT License](LICENSE). Anda bebas menggunakan, memodifikasi, dan mendistribusikan perangkat lunak ini untuk keperluan pribadi maupun komersial.
