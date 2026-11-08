import hashlib
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class SubtitleTrack:
    stream_id: str          # e.g., "0:1"
    sub_index: int          # e.g., 0 for map 0:s:0
    codec: str              # e.g., "subrip", "ass", "mov_text", "hdmv_pgs_subtitle"
    language: str           # e.g., "eng", "ind", "und"
    title: str              # e.g., "English Dialogue"
    is_text: bool           # True if text-based (can convert to srt directly)

    @property
    def display_name(self) -> str:
        tag = "[TEXT]" if self.is_text else "[BITMAP/PGS]"
        desc = f"Track #{self.sub_index} ({self.language.upper()}) - {self.codec}"
        if self.title:
            desc += f" - \"{self.title}\""
        return f"{tag} {desc}"


@dataclass
class VideoItem:
    path: Path
    name: str
    size_bytes: int
    size_str: str
    modified_time: float
    tracks: List[SubtitleTrack] = field(default_factory=list)
    has_text_sub: bool = False
    thumbnail_path: Optional[str] = None

    @property
    def sub_summary(self) -> str:
        text_tracks = [t for t in self.tracks if t.is_text]
        if not text_tracks:
            return "Tanpa soft-sub teks"
        langs = ", ".join(sorted(set(t.language.upper() for t in text_tracks)))
        return f"{len(text_tracks)} Track ({langs})"


class SubtitleExtractor:
    SUPPORTED_VIDEO_EXTS = {".mkv", ".mp4", ".webm", ".avi", ".mov", ".m4v", ".ts"}
    TEXT_CODECS = {"subrip", "srt", "ass", "ssa", "mov_text", "webvtt", "text"}

    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = self._locate_ffmpeg(ffmpeg_path)
        self.cache_dir = Path.home() / ".cache" / "video_translator" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _locate_ffmpeg(self, custom_path: Optional[str] = None) -> str:
        if custom_path and os.path.isfile(custom_path):
            return custom_path

        exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"

        # Check PyInstaller frozen paths
        if getattr(sys, "frozen", False):
            # 1. Bundled inside _MEIPASS (onefile or onedir bundle)
            meipass_bin = Path(sys._MEIPASS) / "bin" / exe_name
            if meipass_bin.is_file():
                return str(meipass_bin)
            meipass_root = Path(sys._MEIPASS) / exe_name
            if meipass_root.is_file():
                return str(meipass_root)
            # 2. Next to executable
            exe_dir = Path(sys.executable).parent
            if (exe_dir / "bin" / exe_name).is_file():
                return str(exe_dir / "bin" / exe_name)
            if (exe_dir / exe_name).is_file():
                return str(exe_dir / exe_name)

        # Check relative project bin directory
        project_root = Path(__file__).resolve().parent.parent
        local_bin = project_root / "bin" / exe_name
        if local_bin.is_file():
            return str(local_bin)

        which_ffmpeg = shutil.which("ffmpeg")
        if which_ffmpeg:
            return which_ffmpeg

        raise FileNotFoundError(
            "FFmpeg executable not found. Place ffmpeg in the 'bin/' folder or install it in your system PATH."
        )

    def scan_folder(self, folder_path: str) -> List[Path]:
        """Returns list of video paths in folder."""
        folder = Path(folder_path)
        if not folder.is_dir():
            return []
        
        videos = []
        for p in folder.iterdir():
            if p.is_file() and p.suffix.lower() in self.SUPPORTED_VIDEO_EXTS:
                videos.append(p)
        return sorted(videos)

    @staticmethod
    def format_size(size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def get_video_item(self, video_path: Path, load_tracks: bool = True) -> VideoItem:
        """Inspects a video and returns a populated VideoItem with thumbnail."""
        stat = video_path.stat()
        item = VideoItem(
            path=video_path,
            name=video_path.name,
            size_bytes=stat.st_size,
            size_str=self.format_size(stat.st_size),
            modified_time=stat.st_mtime,
            tracks=[],
            has_text_sub=False,
            thumbnail_path=self.get_or_create_thumbnail(video_path)
        )
        if load_tracks:
            tracks = self.get_subtitle_tracks(str(video_path))
            item.tracks = tracks
            item.has_text_sub = any(t.is_text for t in tracks)

        return item

    def get_or_create_thumbnail(self, video_path: Path, time_pos: str = "00:00:02") -> Optional[str]:
        """Generates a 160x90 JPEG thumbnail for the video and caches it."""
        try:
            # Deterministic cache hash based on path + mtime
            file_key = f"{video_path.resolve()}_{video_path.stat().st_mtime}"
            hash_str = hashlib.md5(file_key.encode("utf-8")).hexdigest()
            thumb_file = self.cache_dir / f"{hash_str}.jpg"

            if thumb_file.is_file() and thumb_file.stat().st_size > 0:
                return str(thumb_file)

            cmd = [
                self.ffmpeg_path,
                "-y",
                "-ss", time_pos,
                "-i", str(video_path),
                "-vframes", "1",
                "-s", "160x90",
                str(thumb_file)
            ]
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if thumb_file.is_file() and thumb_file.stat().st_size > 0:
                return str(thumb_file)
        except Exception:
            pass
        return None

    def get_subtitle_tracks(self, video_path: str) -> List[SubtitleTrack]:
        """Inspects the video file using ffmpeg and extracts subtitle track information."""
        cmd = [self.ffmpeg_path, "-hide_banner", "-i", str(video_path)]
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            output = res.stderr
        except Exception as e:
            raise RuntimeError(f"Failed to inspect video: {e}")

        tracks: List[SubtitleTrack] = []
        stream_regex = re.compile(
            r"Stream\s+#(\d+:\d+)(?:\(([^)]+)\))?:\s+Subtitle:\s+([a-zA-Z0-9_\-]+)",
            re.IGNORECASE
        )
        
        lines = output.splitlines()
        current_sub_idx = 0

        for i, line in enumerate(lines):
            match = stream_regex.search(line)
            if match:
                stream_id = match.group(1)
                lang = match.group(2) or "und"
                codec = match.group(3).lower()
                
                title = ""
                for j in range(i + 1, min(i + 6, len(lines))):
                    if "Stream #" in lines[j]:
                        break
                    title_match = re.search(r"title\s*:\s*(.+)", lines[j], re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1).strip()
                        break

                is_text = codec in self.TEXT_CODECS
                tracks.append(SubtitleTrack(
                    stream_id=stream_id,
                    sub_index=current_sub_idx,
                    codec=codec,
                    language=lang,
                    title=title,
                    is_text=is_text
                ))
                current_sub_idx += 1

        return tracks

    def extract_subtitle(self, video_path: str, sub_index: int, output_path: str) -> str:
        """Extracts a soft-subtitle stream and writes it as an SRT file."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(video_path),
            "-map", f"0:s:{sub_index}",
            "-c:s", "srt",
            str(out_file)
        ]
        
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg extraction failed:\n{res.stderr}")
            
        if not out_file.is_file() or out_file.stat().st_size == 0:
            raise RuntimeError("Extraction finished but output SRT is empty or not found.")

        return str(out_file)
