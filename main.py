import argparse
import sys
from pathlib import Path

def run_cli_single(extractor, video_path: Path, track_idx: int, target_code: str, output_path: str = None, style: str = "casual"):
    from core.parser import SubtitleParser
    from core.translator import SubtitleTranslator

    print(f"\n[*] Scanning video: {video_path.name}")
    tracks = extractor.get_subtitle_tracks(str(video_path))

    if not tracks:
        print(f"[-] No subtitle tracks found in {video_path.name}")
        return False

    text_tracks = [t for t in tracks if t.is_text]
    if not text_tracks:
        print(f"[-] Only bitmap/PGS tracks found in {video_path.name}, skipping.")
        return False

    selected_track = text_tracks[track_idx] if track_idx < len(text_tracks) else text_tracks[0]
    print(f"[*] Extracting track #{selected_track.sub_index} ({selected_track.language})...")

    temp_srt = video_path.with_suffix(".temp_ext.srt")
    extractor.extract_subtitle(str(video_path), selected_track.sub_index, str(temp_srt))

    entries = SubtitleParser.load_from_file(str(temp_srt))
    if temp_srt.exists():
        temp_srt.unlink()

    print(f"[+] Extracted {len(entries)} subtitle lines.")

    print(f"[*] Translating to language: {target_code} (Style: {style})...")
    translator = SubtitleTranslator(target_lang=target_code, style=style)

    def progress(cur, tot, sample):
        pct = (cur / tot) * 100
        print(f"    Progress: {cur}/{tot} ({pct:.1f}%) -> {sample[:35]}...")

    translator.translate_entries(entries, progress_callback=progress)

    out_file = output_path or str(video_path.with_name(f"{video_path.stem}.{target_code}.srt"))
    SubtitleParser.export_to_srt(entries, out_file, export_mode="translated")
    print(f"[SUCCESS] Subtitle saved to: {out_file}")
    return True


def run_cli(args):
    from core.extractor import SubtitleExtractor

    extractor = SubtitleExtractor(ffmpeg_path=args.ffmpeg)

    if args.folder:
        folder = Path(args.folder)
        if not folder.is_dir():
            print(f"Error: Folder not found: {folder}")
            sys.exit(1)

        videos = extractor.scan_folder(str(folder))
        print(f"[*] Found {len(videos)} video files in folder: {folder}")
        success = 0
        for v in videos:
            if run_cli_single(extractor, v, args.track, args.lang, style=args.style):
                success += 1
        print(f"\n[SUMMARY] Successfully processed {success}/{len(videos)} videos.")
    elif args.video:
        video_path = Path(args.video)
        if not video_path.is_file():
            print(f"Error: Video file not found: {video_path}")
            sys.exit(1)
        run_cli_single(extractor, video_path, args.track, args.lang, args.output, style=args.style)


def run_gui():
    from gui.app import launch_app
    launch_app()


def main():
    parser = argparse.ArgumentParser(description="Lightweight Video Soft-Sub Scraper & Translator")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode without GUI")
    parser.add_argument("--video", type=str, help="Path to video file (CLI mode)")
    parser.add_argument("--folder", type=str, help="Path to folder of videos for batch translation")
    parser.add_argument("--track", type=int, default=0, help="Subtitle track index (default: 0)")
    parser.add_argument("--lang", type=str, default="id", help="Target language code, e.g. id, en, ja (default: id)")
    parser.add_argument("--style", type=str, default="casual", choices=["casual", "natural", "formal"], help="Translation tone: casual (sehari-hari), natural (standar bioskop), formal (baku)")
    parser.add_argument("--output", type=str, help="Output .srt path (default: [video_stem].[lang].srt)")
    parser.add_argument("--ffmpeg", type=str, help="Custom path to ffmpeg executable")

    args = parser.parse_args()

    if args.cli or args.video or args.folder:
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
