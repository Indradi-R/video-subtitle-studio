import os
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import List, Optional

import customtkinter as ctk
from PIL import Image, ImageDraw

from core.extractor import SubtitleExtractor, SubtitleTrack, VideoItem
from core.parser import SubtitleEntry, SubtitleParser
from core.translator import SUPPORTED_LANGUAGES, TRANSLATION_STYLES, SubtitleTranslator

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class SubtitleTranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🎬 Video Soft-Sub Studio & Translator")
        self.geometry("1240x800")
        self.minsize(1050, 680)

        # Set window icon
        icon_path = self._locate_asset("icon.ico")
        if icon_path and os.path.isfile(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Initialize core logic
        try:
            self.extractor = SubtitleExtractor()
        except Exception as e:
            messagebox.showerror("Error FFmpeg", str(e))
            self.extractor = None

        # Data states
        self.all_video_items: List[VideoItem] = []
        self.displayed_video_items: List[VideoItem] = []
        self.selected_video: Optional[VideoItem] = None
        self.selected_track: Optional[SubtitleTrack] = None

        # Subtitle states
        self.subtitle_entries: List[SubtitleEntry] = []
        self.filtered_entries: List[SubtitleEntry] = []
        self.entry_widgets = []
        self.current_page = 0
        self.page_size = 50
        self.sub_search_keyword = ""

        # Video filter/sort states
        self.video_search_query = ""
        self.filter_category = "Semua Video"
        self.sort_option = "Nama (A - Z)"

        # Image cache
        self.thumbnail_images = {}
        self.default_thumb = self._generate_default_thumbnail()

        # UI references for card highlights
        self.video_card_widgets = {}

        self._build_ui()

    def _locate_asset(self, filename: str) -> Optional[str]:
        if getattr(sys, "frozen", False):
            meipass_p = Path(sys._MEIPASS) / "assets" / filename
            if meipass_p.is_file():
                return str(meipass_p)
            exe_p = Path(sys.executable).parent / "assets" / filename
            if exe_p.is_file():
                return str(exe_p)
        proj_p = Path(__file__).resolve().parent.parent / "assets" / filename
        if proj_p.is_file():
            return str(proj_p)
        return None

    def _generate_default_thumbnail(self) -> ctk.CTkImage:
        img = Image.new("RGB", (120, 68), color=(35, 39, 46))
        draw = ImageDraw.Draw(img)
        draw.rectangle([6, 6, 114, 62], outline=(70, 75, 90), width=1)
        # Draw small film play icon
        draw.polygon([(52, 26), (52, 42), (72, 34)], fill=(120, 130, 150))
        return ctk.CTkImage(light_image=img, dark_image=img, size=(120, 68))

    def _get_thumbnail_image(self, thumb_path: Optional[str]) -> ctk.CTkImage:
        if not thumb_path or not os.path.isfile(thumb_path):
            return self.default_thumb
        if thumb_path in self.thumbnail_images:
            return self.thumbnail_images[thumb_path]
        try:
            pil_img = Image.open(thumb_path)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(120, 68))
            self.thumbnail_images[thumb_path] = ctk_img
            return ctk_img
        except Exception:
            return self.default_thumb

    # ---------------- UI BUILDERS ----------------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0, minsize=380)  # Left video library
        self.grid_columnconfigure(1, weight=1)               # Right subtitle studio
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        left_panel = ctk.CTkFrame(self, width=390, corner_radius=0, fg_color=("gray92", "#181a1f"))
        left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        left_panel.grid_propagate(False)
        left_panel.grid_rowconfigure(3, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # Header title with Logo
        header_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        logo_path = self._locate_asset("logo_small.png")
        if logo_path and os.path.isfile(logo_path):
            try:
                pil_logo = Image.open(logo_path)
                ctk_logo = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(36, 36))
                lbl_logo = ctk.CTkLabel(header_frame, text="", image=ctk_logo)
                lbl_logo.pack(side="left", padx=(0, 10))
            except Exception:
                pass

        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(side="left", fill="both", expand=True)

        lbl_app = ctk.CTkLabel(
            title_container,
            text="Video Subtitle Studio",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_app.pack(anchor="w")

        lbl_desc = ctk.CTkLabel(
            title_container,
            text="Soft-sub extractor & translator.",
            font=ctk.CTkFont(size=11),
            text_color="gray65"
        )
        lbl_desc.pack(anchor="w")

        # Folder Picker
        folder_box = ctk.CTkFrame(left_panel, fg_color=("gray85", "#21252b"), corner_radius=8)
        folder_box.grid(row=1, column=0, sticky="ew", padx=16, pady=6)

        btn_browse = ctk.CTkButton(
            folder_box,
            text="📁 Buka Folder Video",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2b5278",
            hover_color="#1d3b56",
            command=self._on_select_folder
        )
        btn_browse.pack(padx=10, pady=(10, 4), fill="x")

        self.lbl_folder_path = ctk.CTkLabel(
            folder_box,
            text="Belum ada folder yang dipilih",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            wraplength=340,
            justify="left"
        )
        self.lbl_folder_path.pack(padx=10, pady=(0, 10), anchor="w")

        # Search, Filter & Sort Controls
        filter_box = ctk.CTkFrame(left_panel, fg_color="transparent")
        filter_box.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 8))
        filter_box.grid_columnconfigure(0, weight=1)
        filter_box.grid_columnconfigure(1, weight=1)

        # Search entry
        self.video_search_entry = ctk.CTkEntry(
            filter_box,
            placeholder_text="🔍 Cari nama video...",
            height=30
        )
        self.video_search_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.video_search_entry.bind("<KeyRelease>", self._on_video_search_change)

        # Filter dropdown
        self.opt_filter = ctk.CTkOptionMenu(
            filter_box,
            values=["Semua Video", "Hanya yang Punya Soft-Sub", "Hanya MKV", "Hanya MP4"],
            height=28,
            font=ctk.CTkFont(size=11),
            command=self._on_filter_changed
        )
        self.opt_filter.set("Semua Video")
        self.opt_filter.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        # Sort dropdown
        self.opt_sort = ctk.CTkOptionMenu(
            filter_box,
            values=["Nama (A - Z)", "Nama (Z - A)", "Ukuran (Terbesar)", "Ukuran (Terkecil)", "Tanggal (Terbaru)"],
            height=28,
            font=ctk.CTkFont(size=11),
            command=self._on_sort_changed
        )
        self.opt_sort.set("Nama (A - Z)")
        self.opt_sort.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # Video Card Scrollable List
        self.video_scroll_frame = ctk.CTkScrollableFrame(
            left_panel,
            fg_color="transparent",
            label_text="Daftar Video (0)",
            label_font=ctk.CTkFont(size=12, weight="bold")
        )
        self.video_scroll_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.video_scroll_frame.grid_columnconfigure(0, weight=1)

        # Footer Action (Batch Translation)
        footer_frame = ctk.CTkFrame(left_panel, fg_color=("gray85", "#21252b"), corner_radius=0)
        footer_frame.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        
        self.btn_batch = ctk.CTkButton(
            footer_frame,
            text="⚡ Batch Translate Semua Video di Folder",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3b5998",
            hover_color="#2b4273",
            command=self._start_batch_translation
        )
        self.btn_batch.pack(padx=16, pady=10, fill="x")

    def _build_right_panel(self):
        right_panel = ctk.CTkFrame(self, fg_color=("gray95", "#1e2227"))
        right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(3, weight=1)

        # 1. Top Banner: Active Video Info & Track Selector
        self.banner = ctk.CTkFrame(right_panel, fg_color=("gray90", "#282c34"), corner_radius=10)
        self.banner.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        self.banner.grid_columnconfigure(1, weight=1)

        # Mini thumbnail preview in banner
        self.banner_thumb_lbl = ctk.CTkLabel(self.banner, text="", image=self.default_thumb)
        self.banner_thumb_lbl.grid(row=0, column=0, rowspan=2, padx=12, pady=12, sticky="nw")

        banner_info = ctk.CTkFrame(self.banner, fg_color="transparent")
        banner_info.grid(row=0, column=1, sticky="new", padx=(0, 12), pady=(10, 4))
        banner_info.grid_columnconfigure(0, weight=1)

        self.lbl_active_title = ctk.CTkLabel(
            banner_info,
            text="Silakan pilih video dari daftar di sebelah kiri",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        self.lbl_active_title.pack(anchor="w")

        self.lbl_active_meta = ctk.CTkLabel(
            banner_info,
            text="Belum ada video aktif.",
            font=ctk.CTkFont(size=11),
            text_color="gray65",
            anchor="w"
        )
        self.lbl_active_meta.pack(anchor="w", pady=(2, 0))

        # Controls row in banner
        controls_frame = ctk.CTkFrame(self.banner, fg_color="transparent")
        controls_frame.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(0, 10))

        lbl_track = ctk.CTkLabel(controls_frame, text="Track Subtitle:", font=ctk.CTkFont(size=12))
        lbl_track.pack(side="left", padx=(0, 6))

        self.opt_track = ctk.CTkOptionMenu(
            controls_frame,
            values=["(Pilih video dahulu)"],
            width=240,
            command=self._on_track_selected
        )
        self.opt_track.pack(side="left", padx=(0, 14))

        lbl_lang = ctk.CTkLabel(controls_frame, text="Bahasa Target:", font=ctk.CTkFont(size=12))
        lbl_lang.pack(side="left", padx=(0, 6))

        self.lang_names = list(SUPPORTED_LANGUAGES.keys())
        self.opt_lang = ctk.CTkOptionMenu(
            controls_frame,
            values=self.lang_names,
            width=160
        )
        self.opt_lang.set("Indonesian (id)")
        self.opt_lang.pack(side="left", padx=(0, 14))

        lbl_style = ctk.CTkLabel(controls_frame, text="Gaya Bahasa:", font=ctk.CTkFont(size=12))
        lbl_style.pack(side="left", padx=(0, 6))

        self.style_names = list(TRANSLATION_STYLES.keys())
        self.opt_style = ctk.CTkOptionMenu(
            controls_frame,
            values=self.style_names,
            width=220
        )
        self.opt_style.set("Santai / Sehari-hari (Film & Anime)")
        self.opt_style.pack(side="left")

        # 2. Action Bar
        action_bar = ctk.CTkFrame(right_panel, fg_color="transparent")
        action_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)

        self.btn_extract = ctk.CTkButton(
            action_bar,
            text="⬇️ 1. Ekstrak Subtitle",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self._start_extract_subtitles
        )
        self.btn_extract.pack(side="left", padx=(0, 8))

        self.btn_translate = ctk.CTkButton(
            action_bar,
            text="🌐 2. Terjemahkan Teks",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2b825b",
            hover_color="#1e5c40",
            command=self._start_translation
        )
        self.btn_translate.pack(side="left", padx=(0, 8))

        self.btn_export = ctk.CTkButton(
            action_bar,
            text="💾 3. Export ke .SRT",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#7b3294",
            hover_color="#572369",
            command=self._on_export_srt
        )
        self.btn_export.pack(side="left")

        # Progress bar & Status
        self.lbl_status = ctk.CTkLabel(
            action_bar,
            text="Siap.",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.lbl_status.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(right_panel)
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 6))
        self.progress_bar.set(0)

        # 3. Subtitle Editor Table Section
        editor_container = ctk.CTkFrame(right_panel, fg_color=("gray90", "#21252b"), corner_radius=10)
        editor_container.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        editor_container.grid_columnconfigure(0, weight=1)
        editor_container.grid_rowconfigure(2, weight=1)

        # Top tools within table: Search subtitle & Pagination
        table_tools = ctk.CTkFrame(editor_container, fg_color="transparent")
        table_tools.grid(row=0, column=0, sticky="ew", padx=12, pady=10)

        self.sub_search_entry = ctk.CTkEntry(
            table_tools,
            placeholder_text="🔍 Cari kalimat dalam subtitle...",
            width=260
        )
        self.sub_search_entry.pack(side="left")
        self.sub_search_entry.bind("<KeyRelease>", self._on_sub_search_change)

        self.lbl_sub_stats = ctk.CTkLabel(
            table_tools,
            text="0 baris subtitle",
            font=ctk.CTkFont(size=12),
            text_color="gray65"
        )
        self.lbl_sub_stats.pack(side="left", padx=14)

        # Pagination widgets
        self.btn_next = ctk.CTkButton(table_tools, text="Next ▶", width=65, command=self._on_next_page)
        self.btn_next.pack(side="right", padx=2)

        self.lbl_page = ctk.CTkLabel(table_tools, text="Halaman 0/0", font=ctk.CTkFont(size=12))
        self.lbl_page.pack(side="right", padx=8)

        self.btn_prev = ctk.CTkButton(table_tools, text="◀ Prev", width=65, command=self._on_prev_page)
        self.btn_prev.pack(side="right", padx=2)

        # Table Column Header
        tbl_col_header = ctk.CTkFrame(editor_container, height=32, fg_color=("gray80", "#2c313a"), corner_radius=6)
        tbl_col_header.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        tbl_col_header.grid_columnconfigure(0, weight=1)
        tbl_col_header.grid_columnconfigure(1, weight=4)
        tbl_col_header.grid_columnconfigure(2, weight=4)

        ctk.CTkLabel(tbl_col_header, text="No. & Waktu", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=8, sticky="w")
        ctk.CTkLabel(tbl_col_header, text="Teks Asli (Source)", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=1, padx=8, sticky="w")
        ctk.CTkLabel(tbl_col_header, text="Hasil Terjemahan (Bisa Diedit)", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=2, padx=8, sticky="w")

        # Scrollable Subtitle Area
        self.sub_scroll_frame = ctk.CTkScrollableFrame(editor_container, fg_color="transparent")
        self.sub_scroll_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.sub_scroll_frame.grid_columnconfigure(0, weight=1)
        self.sub_scroll_frame.grid_columnconfigure(1, weight=4)
        self.sub_scroll_frame.grid_columnconfigure(2, weight=4)

    # ---------------- FOLDER & VIDEO HANDLING ----------------

    def _on_select_folder(self):
        folder = filedialog.askdirectory(title="Pilih Folder Video")
        if not folder:
            return

        self.lbl_folder_path.configure(text=folder)
        self.lbl_status.configure(text="Memindai file video...")
        self.progress_bar.set(0.1)

        # 1. Instantly scan files
        video_paths = self.extractor.scan_folder(folder)
        if not video_paths:
            self.all_video_items = []
            self.displayed_video_items = []
            self._render_video_cards()
            self.video_scroll_frame.configure(label_text="Daftar Video (0)")
            self.lbl_status.configure(text="Tidak ditemukan file video di folder ini.")
            messagebox.showinfo(
                "Tidak Ditemukan Video",
                "Tidak ditemukan file video (.mkv, .mp4, .webm, .avi, dll.) di folder yang dipilih."
            )
            return

        # 2. Instantly populate fast items (instant UI display!)
        self.all_video_items = [self.extractor.get_fast_video_item(p) for p in video_paths]
        self._apply_video_filter_and_sort()
        self.lbl_status.configure(text=f"Ditemukan {len(self.all_video_items)} video. Memuat info di latar belakang...")
        self.video_scroll_frame.configure(label_text=f"Daftar Video ({len(self.all_video_items)})")

        if self.displayed_video_items:
            self._select_video(self.displayed_video_items[0])

        # 3. Start quiet background thread to load tracks & thumbnails without freezing UI or popping up CMD
        threading.Thread(target=self._async_load_metadata_worker, args=(self.all_video_items,), daemon=True).start()

    def _async_load_metadata_worker(self, items: List[VideoItem]):
        total = len(items)
        for i, item in enumerate(items, start=1):
            try:
                self.extractor.load_video_item_metadata(item)
                self.after(0, lambda it=item: self._update_single_card(it))
                self.after(0, lambda idx=i: self.progress_bar.set(idx / total))
            except Exception as e:
                print(f"Error loading {item.name}: {e}")

        def done():
            self.progress_bar.set(1.0)
            self.lbl_status.configure(text=f"Siap. Semua informasi {total} video telah dimuat.")
            if self.selected_video:
                self._update_banner_details(self.selected_video)
            if self.filter_category == "Hanya yang Punya Soft-Sub":
                self._apply_video_filter_and_sort()

        self.after(0, done)

    def _update_single_card(self, item: VideoItem):
        widgets = self.video_card_widgets.get(item.name)
        if not widgets:
            return
        thumb_lbl = widgets["thumb_lbl"]
        badge_lbl = widgets["badge_lbl"]

        if item.thumbnail_path:
            thumb_img = self._get_thumbnail_image(item.thumbnail_path)
            thumb_lbl.configure(image=thumb_img)

        badge_color = "#1b4d3e" if item.has_text_sub else "#333942"
        badge_text = f"🟢 {item.sub_summary}" if item.has_text_sub else "⚪ Tanpa soft-sub"
        badge_lbl.configure(text=f" {badge_text} ", fg_color=badge_color)

        if self.selected_video and self.selected_video.name == item.name:
            self._update_banner_details(item)

    def _on_video_search_change(self, event=None):
        self.video_search_query = self.video_search_entry.get().strip().lower()
        self._apply_video_filter_and_sort()

    def _on_filter_changed(self, choice: str):
        self.filter_category = choice
        self._apply_video_filter_and_sort()

    def _on_sort_changed(self, choice: str):
        self.sort_option = choice
        self._apply_video_filter_and_sort()

    def _apply_video_filter_and_sort(self):
        filtered = self.all_video_items[:]

        # Text search
        if self.video_search_query:
            filtered = [v for v in filtered if self.video_search_query in v.name.lower()]

        # Category filter
        if self.filter_category == "Hanya yang Punya Soft-Sub":
            filtered = [v for v in filtered if v.has_text_sub]
        elif self.filter_category == "Hanya MKV":
            filtered = [v for v in filtered if v.path.suffix.lower() == ".mkv"]
        elif self.filter_category == "Hanya MP4":
            filtered = [v for v in filtered if v.path.suffix.lower() == ".mp4"]

        # Sort
        if self.sort_option == "Nama (A - Z)":
            filtered.sort(key=lambda v: v.name.lower())
        elif self.sort_option == "Nama (Z - A)":
            filtered.sort(key=lambda v: v.name.lower(), reverse=True)
        elif self.sort_option == "Ukuran (Terbesar)":
            filtered.sort(key=lambda v: v.size_bytes, reverse=True)
        elif self.sort_option == "Ukuran (Terkecil)":
            filtered.sort(key=lambda v: v.size_bytes)
        elif self.sort_option == "Tanggal (Terbaru)":
            filtered.sort(key=lambda v: v.modified_time, reverse=True)

        self.displayed_video_items = filtered
        self._render_video_cards()

    def _render_video_cards(self):
        for widget in self.video_scroll_frame.winfo_children():
            widget.destroy()
        self.video_card_widgets.clear()

        if not self.displayed_video_items:
            empty_box = ctk.CTkFrame(self.video_scroll_frame, fg_color="transparent")
            empty_box.pack(pady=40, fill="both", expand=True)
            ctk.CTkLabel(
                empty_box,
                text="📁 Tidak ada file video yang ditemukan.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="gray60"
            ).pack(pady=(0, 4))
            ctk.CTkLabel(
                empty_box,
                text="Pastikan folder berisi file .mkv, .mp4, .webm, dll.",
                font=ctk.CTkFont(size=11),
                text_color="gray50"
            ).pack()
            return

        for item in self.displayed_video_items:
            card = ctk.CTkFrame(
                self.video_scroll_frame,
                fg_color=("gray85", "#21252b"),
                corner_radius=8,
                border_width=1,
                border_color=("gray75", "#2c313a")
            )
            card.pack(fill="x", pady=4, padx=2)
            card.grid_columnconfigure(1, weight=1)

            thumb_img = self._get_thumbnail_image(item.thumbnail_path)
            thumb_lbl = ctk.CTkLabel(card, text="", image=thumb_img)
            thumb_lbl.grid(row=0, column=0, rowspan=2, padx=8, pady=8, sticky="w")

            title_lbl = ctk.CTkLabel(
                card,
                text=item.name,
                font=ctk.CTkFont(size=12, weight="bold"),
                wraplength=210,
                justify="left",
                anchor="w"
            )
            title_lbl.grid(row=0, column=1, padx=(4, 8), pady=(8, 2), sticky="nw")

            meta_frame = ctk.CTkFrame(card, fg_color="transparent")
            meta_frame.grid(row=1, column=1, padx=(4, 8), pady=(0, 8), sticky="sw")

            badge_color = "#1b4d3e" if item.has_text_sub else "#333942"
            badge_text = f"🟢 {item.sub_summary}" if item.metadata_loaded else "⏳ Memeriksa..."
            badge_lbl = ctk.CTkLabel(
                meta_frame,
                text=f" {badge_text} ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=badge_color,
                corner_radius=4
            )
            badge_lbl.pack(side="left", padx=(0, 6))

            size_lbl = ctk.CTkLabel(
                meta_frame,
                text=f"{item.size_str}",
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            )
            size_lbl.pack(side="left")

            def bind_click(w, video_item=item):
                w.bind("<Button-1>", lambda e: self._select_video(video_item))
                w.configure(cursor="hand2")

            bind_click(card)
            bind_click(thumb_lbl)
            bind_click(title_lbl)
            bind_click(meta_frame)
            bind_click(badge_lbl)
            bind_click(size_lbl)

            self.video_card_widgets[item.name] = {
                "card": card,
                "thumb_lbl": thumb_lbl,
                "badge_lbl": badge_lbl
            }

        self._highlight_selected_card()

    def _select_video(self, item: VideoItem):
        self.selected_video = item
        self._highlight_selected_card()

        if not item.metadata_loaded:
            self.extractor.load_video_item_metadata(item)
            self._update_single_card(item)

        self._update_banner_details(item)

        self.subtitle_entries.clear()
        self.filtered_entries.clear()
        self.current_page = 0
        self._render_current_page()
        self.lbl_sub_stats.configure(text="0 baris subtitle")
        self.lbl_status.configure(text=f"Video dipilih: {item.name}")

    def _update_banner_details(self, item: VideoItem):
        self.lbl_active_title.configure(text=item.name)
        self.lbl_active_meta.configure(text=f"Ukuran: {item.size_str}  •  {item.sub_summary}  •  {item.path.suffix.upper()}")
        self.banner_thumb_lbl.configure(image=self._get_thumbnail_image(item.thumbnail_path))

        if item.tracks:
            track_labels = [t.display_name for t in item.tracks]
            self.opt_track.configure(values=track_labels)
            first_text = next((t for t in item.tracks if t.is_text), item.tracks[0])
            self.opt_track.set(first_text.display_name)
            self.selected_track = first_text
        else:
            self.opt_track.configure(values=["(Tidak ada track subtitle)"])
            self.opt_track.set("(Tidak ada track subtitle)")
            self.selected_track = None

    def _highlight_selected_card(self):
        if not self.selected_video:
            return
        for name, widgets in self.video_card_widgets.items():
            card = widgets["card"]
            if name == self.selected_video.name:
                card.configure(
                    fg_color=("gray75", "#283547"),
                    border_color="#3B8ED0",
                    border_width=2
                )
            else:
                card.configure(
                    fg_color=("gray85", "#21252b"),
                    border_color=("gray75", "#2c313a"),
                    border_width=1
                )

    def _on_track_selected(self, selected_label: str):
        if not self.selected_video:
            return
        self.selected_track = next((t for t in self.selected_video.tracks if t.display_name == selected_label), None)

    # ---------------- SUBTITLE WORKFLOW ----------------

    def _start_extract_subtitles(self):
        if not self.selected_video or not self.selected_track:
            messagebox.showwarning("Peringatan", "Pilih video dan track subtitle terlebih dahulu.")
            return

        if not self.selected_track.is_text:
            messagebox.showwarning(
                "Track Bitmap/PGS",
                "Track subtitle ini berupa format gambar (Bitmap/PGS), bukan teks.\n"
                "FFmpeg hanya dapat mengekstrak langsung format teks (SRT, ASS, VTT, MOV_TEXT)."
            )
            return

        self.lbl_status.configure(text="Mengekstrak soft-sub dari video...")
        self.progress_bar.set(0.3)
        threading.Thread(target=self._extract_worker, daemon=True).start()

    def _extract_worker(self):
        try:
            temp_srt = self.selected_video.path.with_suffix(".temp_ext.srt")
            self.extractor.extract_subtitle(
                video_path=str(self.selected_video.path),
                sub_index=self.selected_track.sub_index,
                output_path=str(temp_srt)
            )

            entries = SubtitleParser.load_from_file(str(temp_srt))
            if temp_srt.exists():
                temp_srt.unlink()

            self.subtitle_entries = entries
            self.current_page = 0
            self.after(0, self._apply_sub_search_and_render)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Gagal Ekstraksi", str(e)))
            self.after(0, lambda: self.lbl_status.configure(text="Gagal mengekstrak subtitle."))

    def _on_sub_search_change(self, event=None):
        self.sub_search_keyword = self.sub_search_entry.get().strip().lower()
        self.current_page = 0
        self._apply_sub_search_and_render()

    def _on_prev_page(self):
        if self.current_page > 0:
            self._sync_current_page_edits()
            self.current_page -= 1
            self._render_current_page()

    def _on_next_page(self):
        max_page = max(0, (len(self.filtered_entries) - 1) // self.page_size)
        if self.current_page < max_page:
            self._sync_current_page_edits()
            self.current_page += 1
            self._render_current_page()

    def _sync_current_page_edits(self):
        for entry, widget in self.entry_widgets:
            edited_text = widget.get().strip()
            if edited_text:
                entry.translated_text = edited_text

    def _apply_sub_search_and_render(self):
        if not self.sub_search_keyword:
            self.filtered_entries = self.subtitle_entries
        else:
            self.filtered_entries = [
                e for e in self.subtitle_entries
                if self.sub_search_keyword in e.source_text.lower() or self.sub_search_keyword in e.translated_text.lower()
            ]

        total = len(self.subtitle_entries)
        matching = len(self.filtered_entries)
        stats_text = f"{total} baris subtitle"
        if self.sub_search_keyword:
            stats_text += f" (Cocok: {matching})"
        self.lbl_sub_stats.configure(text=stats_text)
        self.lbl_status.configure(text=f"Berhasil memuat {total} baris subtitle.")
        self.progress_bar.set(1.0)

        self._render_current_page()

    def _render_current_page(self):
        for widget in self.sub_scroll_frame.winfo_children():
            widget.destroy()
        self.entry_widgets.clear()

        total = len(self.filtered_entries)
        if total == 0:
            self.lbl_page.configure(text="Halaman 0/0")
            return

        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, total_pages - 1)
        self.lbl_page.configure(text=f"Halaman {self.current_page + 1} / {total_pages}")

        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total)
        page_entries = self.filtered_entries[start_idx:end_idx]

        for entry in page_entries:
            row_frame = ctk.CTkFrame(self.sub_scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=4)
            row_frame.grid_columnconfigure(2, weight=4)

            # Time badge
            time_lbl = ctk.CTkLabel(
                row_frame,
                text=f"#{entry.index}\n{entry.start_str[:8]}",
                font=ctk.CTkFont(size=11),
                text_color="gray60",
                justify="left"
            )
            time_lbl.grid(row=0, column=0, padx=6, sticky="nw")

            # Source text
            src_box = ctk.CTkLabel(
                row_frame,
                text=entry.source_text,
                font=ctk.CTkFont(size=12),
                wraplength=320,
                justify="left",
                anchor="w"
            )
            src_box.grid(row=0, column=1, padx=6, sticky="nw")

            # Editable translated text box
            trans_entry = ctk.CTkEntry(
                row_frame,
                font=ctk.CTkFont(size=12),
                placeholder_text="Hasil terjemahan akan tampil di sini..."
            )
            trans_entry.grid(row=0, column=2, padx=6, sticky="ew")
            if entry.translated_text:
                trans_entry.insert(0, entry.translated_text)

            self.entry_widgets.append((entry, trans_entry))

    def _start_translation(self):
        if not self.subtitle_entries:
            messagebox.showwarning("Peringatan", "Ekstrak subtitle terlebih dahulu sebelum menerjemahkan.")
            return

        self._sync_current_page_edits()
        chosen_lang_name = self.opt_lang.get()
        target_lang_code = SUPPORTED_LANGUAGES.get(chosen_lang_name, "id")

        self.btn_translate.configure(state="disabled")
        self.lbl_status.configure(text=f"Menerjemahkan ke {chosen_lang_name}...")
        self.progress_bar.set(0)

        threading.Thread(
            target=self._translation_worker,
            args=(target_lang_code,),
            daemon=True
        ).start()

    def _translation_worker(self, target_lang_code: str):
        chosen_style = TRANSLATION_STYLES.get(self.opt_style.get(), "casual")
        translator = SubtitleTranslator(source_lang="auto", target_lang=target_lang_code, style=chosen_style)

        def progress_cb(current, total, sample):
            prog = current / total if total > 0 else 0
            self.after(0, lambda: self.progress_bar.set(prog))
            self.after(0, lambda: self.lbl_status.configure(
                text=f"Menerjemahkan: {current}/{total} baris..."
            ))

        try:
            translator.translate_entries(
                self.subtitle_entries,
                progress_callback=progress_cb,
                batch_size=15
            )

            def update_ui():
                self._render_current_page()
                self.btn_translate.configure(state="normal")
                self.lbl_status.configure(text="Penerjemahan selesai! Anda bisa mengedit teks jika diperlukan.")
                self.progress_bar.set(1.0)
                messagebox.showinfo("Selesai", "Proses terjemahan berhasil diselesaikan!")

            self.after(0, update_ui)
        except Exception as e:
            self.after(0, lambda: self.btn_translate.configure(state="normal"))
            self.after(0, lambda: messagebox.showerror("Gagal Terjemahan", f"Terjadi kesalahan: {e}"))

    def _start_batch_translation(self):
        if not self.all_video_items:
            messagebox.showwarning("Peringatan", "Pilih folder yang berisi video terlebih dahulu.")
            return

        chosen_lang_name = self.opt_lang.get()
        target_lang_code = SUPPORTED_LANGUAGES.get(chosen_lang_name, "id")

        msg = f"Aplikasi akan memindai {len(self.all_video_items)} video di folder ini,\nmengekstrak soft-sub, menerjemahkan ke {chosen_lang_name},\ndan menyimpan file .srt otomatis.\n\nLanjutkan?"
        if not messagebox.askyesno("Konfirmasi Batch Translate", msg):
            return

        self.btn_batch.configure(state="disabled")
        self.btn_translate.configure(state="disabled")
        threading.Thread(target=self._batch_worker, args=(target_lang_code,), daemon=True).start()

    def _batch_worker(self, target_lang_code: str):
        chosen_style = TRANSLATION_STYLES.get(self.opt_style.get(), "casual")
        translator = SubtitleTranslator(source_lang="auto", target_lang=target_lang_code, style=chosen_style)
        total_videos = len(self.all_video_items)
        success_count = 0

        for i, item in enumerate(self.all_video_items, start=1):
            self.after(0, lambda idx=i, vname=item.name: self.lbl_status.configure(
                text=f"[{idx}/{total_videos}] Memproses: {vname}"
            ))
            self.after(0, lambda idx=i: self.progress_bar.set(idx / total_videos))

            try:
                text_tracks = [t for t in item.tracks if t.is_text]
                if not text_tracks:
                    continue

                best_track = text_tracks[0]
                temp_srt = item.path.with_suffix(".temp_batch.srt")
                self.extractor.extract_subtitle(str(item.path), best_track.sub_index, str(temp_srt))

                entries = SubtitleParser.load_from_file(str(temp_srt))
                if temp_srt.exists():
                    temp_srt.unlink()

                translator.translate_entries(entries, batch_size=15)

                out_srt = item.path.with_name(f"{item.path.stem}.{target_lang_code}.srt")
                SubtitleParser.export_to_srt(entries, str(out_srt), export_mode="translated")
                success_count += 1
            except Exception as ex:
                print(f"Error processing {item.name}: {ex}")

        def finish_batch():
            self.btn_batch.configure(state="normal")
            self.btn_translate.configure(state="normal")
            self.lbl_status.configure(text=f"Batch selesai: {success_count}/{total_videos} video berhasil diekspor.")
            self.progress_bar.set(1.0)
            messagebox.showinfo("Batch Selesai", f"Berhasil menerjemahkan {success_count} dari {total_videos} file video!")

        self.after(0, finish_batch)

    def _on_export_srt(self):
        if not self.subtitle_entries:
            messagebox.showwarning("Peringatan", "Tidak ada subtitle untuk diekspor.")
            return

        self._sync_current_page_edits()

        target_lang_code = SUPPORTED_LANGUAGES.get(self.opt_lang.get(), "id")
        suggested_name = f"{self.selected_video.path.stem}.{target_lang_code}.srt" if self.selected_video else f"subtitle.{target_lang_code}.srt"
        default_dir = str(self.selected_video.path.parent) if self.selected_video else os.getcwd()

        save_path = filedialog.asksaveasfilename(
            title="Simpan File Subtitle SRT",
            initialdir=default_dir,
            initialfile=suggested_name,
            defaultextension=".srt",
            filetypes=[("SubRip Subtitle", "*.srt"), ("All Files", "*.*")]
        )

        if not save_path:
            return

        try:
            out_file = SubtitleParser.export_to_srt(
                self.subtitle_entries,
                output_path=save_path,
                export_mode="translated"
            )
            messagebox.showinfo("Berhasil", f"File subtitle berhasil disimpan ke:\n{out_file}")
            self.lbl_status.configure(text=f"Tersimpan: {Path(out_file).name}")
        except Exception as e:
            messagebox.showerror("Gagal Export", f"Gagal mengekspor file SRT: {e}")


def launch_app():
    app = SubtitleTranslatorApp()
    app.mainloop()


if __name__ == "__main__":
    launch_app()
