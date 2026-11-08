import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import pysubs2

def ms_to_srt_time(ms: int) -> str:
    """Converts milliseconds into SRT time format HH:MM:SS,mmm."""
    if ms < 0:
        ms = 0
    total_seconds = ms // 1000
    milli = ms % 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milli:03d}"

def srt_time_to_ms(time_str: str) -> int:
    """Converts SRT time format HH:MM:SS,mmm to milliseconds."""
    clean = time_str.strip().replace(".", ",")
    pattern = r"(\d+):(\d+):(\d+),(\d+)"
    match = re.match(pattern, clean)
    if not match:
        return 0
    h, m, s, ms = map(int, match.groups())
    return (h * 3600 + m * 60 + s) * 1000 + ms

@dataclass
class SubtitleEntry:
    index: int
    start_ms: int
    end_ms: int
    start_str: str
    end_str: str
    source_text: str
    translated_text: str = ""

    @property
    def time_range_display(self) -> str:
        return f"{self.start_str} ➔ {self.end_str}"

    def apply_offset(self, offset_ms: int):
        """Shifts timestamps by offset_ms."""
        self.start_ms = max(0, self.start_ms + offset_ms)
        self.end_ms = max(self.start_ms + 200, self.end_ms + offset_ms)
        self.start_str = ms_to_srt_time(self.start_ms)
        self.end_str = ms_to_srt_time(self.end_ms)


class SubtitleParser:
    @staticmethod
    def load_from_file(file_path: str) -> List[SubtitleEntry]:
        """Loads and parses an SRT, VTT, or ASS file into a list of SubtitleEntry."""
        entries: List[SubtitleEntry] = []
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Subtitle file not found: {file_path}")

        try:
            subs = pysubs2.load(str(path), encoding="utf-8")
        except UnicodeDecodeError:
            subs = pysubs2.load(str(path))

        idx = 1
        for event in subs:
            if event.is_comment:
                continue
            
            raw_text = event.plaintext.strip()
            if not raw_text:
                continue

            entry = SubtitleEntry(
                index=idx,
                start_ms=event.start,
                end_ms=event.end,
                start_str=ms_to_srt_time(event.start),
                end_str=ms_to_srt_time(event.end),
                source_text=raw_text,
                translated_text=""
            )
            entries.append(entry)
            idx += 1

        return entries

    @staticmethod
    def export_to_srt(
        entries: List[SubtitleEntry],
        output_path: str,
        export_mode: str = "translated",
        export_translated: Optional[bool] = None,
        offset_ms: int = 0,
        **kwargs
    ) -> str:
        """
        Exports entries to an SRT file with UTF-8 encoding.
        Supports both export_mode ("translated", "original", "bilingual_target_top", "bilingual_source_top")
        and legacy export_translated (True/False).
        """
        if export_translated is not None:
            export_mode = "translated" if export_translated else "original"
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = []
        for i, entry in enumerate(entries, start=1):
            s_ms = max(0, entry.start_ms + offset_ms)
            e_ms = max(s_ms + 200, entry.end_ms + offset_ms)
            s_str = ms_to_srt_time(s_ms)
            e_str = ms_to_srt_time(e_ms)

            src = entry.source_text.strip()
            tgt = entry.translated_text.strip() if entry.translated_text else src

            if export_mode == "original":
                text_content = src
            elif export_mode == "bilingual_target_top":
                text_content = f"{tgt}\n{src}" if tgt != src else tgt
            elif export_mode == "bilingual_source_top":
                text_content = f"{src}\n{tgt}" if tgt != src else src
            else:  # "translated"
                text_content = tgt

            lines.append(str(i))
            lines.append(f"{s_str} --> {e_str}")
            lines.append(text_content)
            lines.append("")

        content = "\n".join(lines) + "\n"
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)

        return str(out)
