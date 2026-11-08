import time
import urllib.parse
from typing import Callable, List, Optional
import requests
from core.parser import SubtitleEntry

SUPPORTED_LANGUAGES = {
    "Indonesian (id)": "id",
    "English (en)": "en",
    "Japanese (ja)": "ja",
    "Korean (ko)": "ko",
    "Chinese Simplified (zh-CN)": "zh-CN",
    "Spanish (es)": "es",
    "French (fr)": "fr",
    "German (de)": "de",
    "Arabic (ar)": "ar",
    "Russian (ru)": "ru",
    "Portuguese (pt)": "pt",
    "Hindi (hi)": "hi",
    "Thai (th)": "th",
    "Vietnamese (vi)": "vi"
}


class SubtitleTranslator:
    def __init__(self, source_lang: str = "auto", target_lang: str = "id"):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def _translate_single_text(self, text: str) -> str:
        """Translates a single block of text using the Google Translate gtx service."""
        if not text.strip():
            return text

        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": self.source_lang,
            "tl": self.target_lang,
            "dt": "t",
            "q": text
        }

        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Structure of response: [[['translated text', 'source text', ...], ...], ...]
        translated_segments = []
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            for part in data[0]:
                if isinstance(part, list) and len(part) > 0 and isinstance(part[0], str):
                    translated_segments.append(part[0])
                    
        return "".join(translated_segments) if translated_segments else text

    def translate_entries(
        self,
        entries: List[SubtitleEntry],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        batch_size: int = 15,
        delay_seconds: float = 0.3
    ) -> List[SubtitleEntry]:
        """
        Translates a list of SubtitleEntry objects.
        Uses batching with unique delimiter to minimize HTTP requests and speed up translation.
        """
        total = len(entries)
        if total == 0:
            return entries

        delimiter = "\n[[[SEG_SEP]]]\n"

        for i in range(0, total, batch_size):
            batch = entries[i : i + batch_size]
            batch_texts = [e.source_text.replace(delimiter.strip(), " ") for e in batch]
            joined_payload = delimiter.join(batch_texts)

            try:
                translated_payload = self._translate_single_text(joined_payload)
                translated_parts = translated_payload.split(delimiter.strip())

                # If split matches batch length, assign 1-to-1
                if len(translated_parts) == len(batch):
                    for entry, trans in zip(batch, translated_parts):
                        entry.translated_text = trans.strip()
                else:
                    # Fallback to line-by-line if delimiter was altered by translator
                    for entry in batch:
                        try:
                            entry.translated_text = self._translate_single_text(entry.source_text).strip()
                            time.sleep(0.1)
                        except Exception:
                            entry.translated_text = entry.source_text
            except Exception as e:
                # Network or endpoint error fallback for this batch
                for entry in batch:
                    try:
                        entry.translated_text = self._translate_single_text(entry.source_text).strip()
                    except Exception:
                        entry.translated_text = entry.source_text

            # Update progress
            current_processed = min(i + batch_size, total)
            if progress_callback:
                last_sample = batch[-1].translated_text if batch else ""
                progress_callback(current_processed, total, last_sample)

            time.sleep(delay_seconds)

        return entries
