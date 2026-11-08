import re
import time
import json
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

TRANSLATION_STYLES = {
    "Santai / Sehari-hari (Film & Anime)": "casual",
    "Standar Alami (Gaya Netflix/Bioskop)": "natural",
    "Formal / Baku (Dokumenter/Edukasi)": "formal"
}


class ConversationalIndonesianRefiner:
    """
    Refines rigid/robotic Indonesian machine translations into natural,
    everyday colloquial Indonesian subtitles.
    """

    # Common technical mistranslations in video/subtitles
    TECHNICAL_CORRECTIONS = [
        (r"\bsubtitle lembut\b", "soft-subtitle", True),
        (r"\bsubtitel lembut\b", "soft-subtitle", True),
        (r"\bterjemahan mesin\b", "terjemahan otomatis", True),
        (r"\btes penerjemah\b", "uji coba penerjemah", True),
        (r"\bberkas srt\b", "file SRT", True),
        (r"\bfile srt\b", "file SRT", False),
    ]

    # Stiff movie idioms -> Natural Indonesian equivalents
    IDIOM_CORRECTIONS = [
        (r"\bapakah anda bercanda\b", "kamu bercanda?", True),
        (r"\bapakah kamu bercanda\b", "kamu bercanda?", True),
        (r"\byang benar saja\b", "yang bener aja", True),
        (r"\bapa yang sedang terjadi\b", "ada apa nih", True),
        (r"\bapa yang terjadi\b", "ada apa", True),
        (r"\btidak ada jalan\b", "nggak mungkin", True),
        (r"\btidak mungkin\b", "nggak mungkin", False),
        (r"\btenang saja\b", "tenang aja", True),
        (r"\blupakan saja\b", "lupakan aja", True),
        (r"\btentu saja\b", "tentu aja", True),
        (r"\bserahkan padaku\b", "serahkan ke aku", True),
        (r"\baku mengerti\b", "aku paham", True),
        (r"\bsaya mengerti\b", "aku paham", True),
        (r"\btidak apa-apa\b", "nggak apa-apa", True),
        (r"\bterima kasih banyak\b", "makasih banyak", True),
        (r"\bsama-sama\b", "sama-sama", False),
        (r"\bhati-hati\b", "hati-hati ya", False),
        (r"\btunggu sebentar\b", "tunggu bentar", True),
        (r"\bsebentar lagi\b", "bentar lagi", True),
        (r"\bbukan urusanmu\b", "bukan urusan kamu", True),
        (r"\bapa maksudmu\b", "maksud kamu apa", True),
        (r"\bmaksud saya\b", "maksudku", True),
        (r"\bmaksud aku\b", "maksudku", True),
    ]

    # Rigid formal words -> Natural conversational words
    CASUAL_REPLACEMENTS = [
        # Stiff question opener "Apakah..." removal for natural dialogue
        (r"^Apakah\s+kamu\s+", "Kamu ", False),
        (r"^Apakah\s+Anda\s+", "Kamu ", False),
        (r"^Apakah\s+dia\s+", "Dia ", False),
        (r"^Apakah\s+mereka\s+", "Mereka ", False),
        (r"^Apakah\s+ini\s+", "Ini ", False),
        (r"^Apakah\s+itu\s+", "Itu ", False),
        (r"^Apakah\s+kita\s+", "Kita ", False),
        (r"^Apakah\s+ada\s+", "Ada ", False),
        (r"^Apakah\s+bisa\s+", "Bisa ", False),

        # Pronoun & conversational vocabulary
        (r"\bAnda\b", "kamu", True),
        (r"\banda\b", "kamu", False),
        (r"\btidak\b", "nggak", False),
        (r"\btak\b", "nggak", False),
        (r"\bmengapa\b", "kenapa", True),
        (r"\bbagaimana jika\b", "gimana kalau", True),
        (r"\bbagaimana kalau\b", "gimana kalau", True),
        (r"\bbagaimana bisa\b", "gimana bisa", True),
        (r"\bbagaimana\b", "gimana", True),
        (r"\bsedang apa\b", "lagi apa", True),
        (r"\bsedang\b", "lagi", False),
        (r"\bhanya\b", "cuma", False),
        (r"\bsudah\b", "udah", False),
        (r"\btetapi\b", "tapi", True),
        (r"\bseperti ini\b", "kayak gini", False),
        (r"\bseperti itu\b", "kayak gitu", False),
        (r"\bbegitu\b", "gitu", False),
        (r"\bbenar-benar\b", "bener-bener", False),
        (r"\bsangat\s+([a-zA-Z]+)", r"\1 banget", False),  # "sangat bagus" -> "bagus banget"
        (r"\bdengan siapa\b", "sama siapa", False),
        (r"\bdengan saya\b", "sama aku", False),
        (r"\bdengan kamu\b", "sama kamu", False),
        (r"\bkepada saya\b", "ke aku", False),
        (r"\bkepada kamu\b", "ke kamu", False),
        (r"\bmelihat ini\b", "liat ini", False),
        (r"\blihatlah\b", "coba liat", False),
        (r"\btidak mau\b", "nggak mau", False),
        (r"\btidak bisa\b", "nggak bisa", False),
        (r"\btidak tahu\b", "nggak tahu", False),
        (r"\btidak ada\b", "nggak ada", False),
        (r"\btidak perlu\b", "nggak usah", False),
        (r"\bjangan pernah\b", "jangan sekali-kali", False),
        (r"\bkemudian\b", "lalu", True),
        (r"\bjika\b", "kalau", False),
        (r"\bjikalau\b", "kalau", False),
        (r"\bsekarang juga\b", "sekarang juga", False),
    ]

    # Semi-formal natural movie subtitle style (Netflix style)
    NATURAL_REPLACEMENTS = [
        (r"^Apakah\s+kamu\s+", "Kamu ", False),
        (r"^Apakah\s+Anda\s+", "Kamu ", False),
        (r"^Apakah\s+ini\s+", "Ini ", False),
        (r"^Apakah\s+itu\s+", "Itu ", False),
        (r"\bAnda\b", "kamu", True),
        (r"\banda\b", "kamu", False),
        (r"\bmengapa\b", "kenapa", True),
        (r"\btetapi\b", "tapi", True),
        (r"\bjika\b", "kalau", False),
        (r"\bkemudian\b", "lalu", True),
        (r"\bseperti ini\b", "seperti ini", False),
    ]

    @classmethod
    def refine(cls, text: str, style: str = "casual") -> str:
        if not text:
            return text

        result = text

        # 1. Always apply technical corrections
        for pattern, repl, ignore_case in cls.TECHNICAL_CORRECTIONS:
            flags = re.IGNORECASE if ignore_case else 0
            result = re.sub(pattern, repl, result, flags=flags)

        # 2. If style is formal, return with only technical fixes
        if style == "formal":
            return result.strip()

        # 3. Always apply idiom corrections for natural & casual styles
        for pattern, repl, ignore_case in cls.IDIOM_CORRECTIONS:
            flags = re.IGNORECASE if ignore_case else 0
            result = re.sub(pattern, repl, result, flags=flags)

        # 4. Apply style-specific vocabulary
        replacements = cls.CASUAL_REPLACEMENTS if style == "casual" else cls.NATURAL_REPLACEMENTS
        for pattern, repl, ignore_case in replacements:
            flags = re.IGNORECASE if ignore_case else 0
            # Check capitalization preservation
            def make_repl(m):
                matched = m.group(0)
                subbed = re.sub(pattern, repl, matched, flags=flags)
                if matched and matched[0].isupper():
                    return subbed[0].upper() + subbed[1:] if len(subbed) > 1 else subbed.upper()
                return subbed

            result = re.sub(pattern, make_repl, result, flags=flags)

        # Capitalize first letter of sentence
        if result and len(result) > 1:
            result = result[0].upper() + result[1:]

        return result.strip()


class SubtitleTranslator:
    def __init__(
        self,
        source_lang: str = "auto",
        target_lang: str = "id",
        style: str = "casual",
        ai_api_key: Optional[str] = None
    ):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.style = style  # "casual", "natural", "formal"
        self.ai_api_key = ai_api_key
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def _translate_single_text(self, text: str) -> str:
        """Translates a block of text using Google Translate GTX service."""
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

        resp = self.session.get(url, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        translated_segments = []
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            for part in data[0]:
                if isinstance(part, list) and len(part) > 0 and isinstance(part[0], str):
                    translated_segments.append(part[0])

        raw_translated = "".join(translated_segments) if translated_segments else text
        return raw_translated

    def _post_process_text(self, text: str) -> str:
        """Applies conversational natural refiner when target is Indonesian."""
        if self.target_lang == "id":
            return ConversationalIndonesianRefiner.refine(text, style=self.style)
        return text

    def translate_entries(
        self,
        entries: List[SubtitleEntry],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        batch_size: int = 15,
        delay_seconds: float = 0.25
    ) -> List[SubtitleEntry]:
        """
        Translates a list of SubtitleEntry objects.
        Uses batching with unique delimiter to preserve structure, followed by
        colloquial refiner to produce natural, everyday dialogue subtitles.
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

                if len(translated_parts) == len(batch):
                    for entry, trans in zip(batch, translated_parts):
                        entry.translated_text = self._post_process_text(trans.strip())
                else:
                    for entry in batch:
                        try:
                            raw = self._translate_single_text(entry.source_text).strip()
                            entry.translated_text = self._post_process_text(raw)
                            time.sleep(0.08)
                        except Exception:
                            entry.translated_text = entry.source_text
            except Exception:
                for entry in batch:
                    try:
                        raw = self._translate_single_text(entry.source_text).strip()
                        entry.translated_text = self._post_process_text(raw)
                    except Exception:
                        entry.translated_text = entry.source_text

            current_processed = min(i + batch_size, total)
            if progress_callback:
                last_sample = batch[-1].translated_text if batch else ""
                progress_callback(current_processed, total, last_sample)

            time.sleep(delay_seconds)

        return entries
