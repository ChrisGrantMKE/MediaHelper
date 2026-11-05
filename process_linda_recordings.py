"""
Process Linda Recordings:
1. Organizes recordings into:
   Linda Recordings/
     └── Week of YYYY-MM-DD/
         └── YYYY-MM-DD/
             ├── <filename>.mp3               (Highly compressed mono audio)
             ├── <filename>_vietnamese.txt    (Native Vietnamese transcript)
             └── <filename>_english.txt       (English translation transcript)
2. Uses ffmpeg for audio compression (32kbps mono MP3, ~94% size reduction).
3. Uses faster-whisper with CUDA (GTX 1070) for local AI transcription & translation.
4. Resumable: skips files that are already completed.
"""

import os
import re
import sys
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

def parse_recording_date(filename: str, file_path: Path) -> datetime:
    # Match patterns like R2024-07-26-22-08-44 or 2024-07-26_22-08-44
    match = re.search(r'(\d{4})[-_](\d{2})[-_](\d{2})[-_](\d{2})[-_](\d{2})[-_](\d{2})', filename)
    if match:
        y, m, d, hh, mm, ss = map(int, match.groups())
        return datetime(y, m, d, hh, mm, ss)
    
    # Try date only
    match_date = re.search(r'(\d{4})[-_](\d{2})[-_](\d{2})', filename)
    if match_date:
        y, m, d = map(int, match_date.groups())
        return datetime(y, m, d)

    # Fallback to file modification time
    mtime = file_path.stat().st_mtime
    return datetime.fromtimestamp(mtime)

def format_timestamp(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def compress_audio(input_file: Path, output_file: Path):
    """Compress audio to 32kbps 16kHz mono MP3 using ffmpeg"""
    if output_file.exists() and output_file.stat().st_size > 0:
        return
    print(f"  [Compressing] -> {output_file.name}")
    cmd = [
        "ffmpeg", "-y", "-i", str(input_file),
        "-vn", "-ar", "16000", "-ac", "1",
        "-c:a", "libmp3lame", "-b:a", "32k",
        str(output_file)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def transcribe_and_translate(model, audio_path: Path, vi_path: Path, en_path: Path):
    """Run transcription (Vietnamese) and translation (English)"""
    
    # 1. Native Vietnamese Transcription
    if not vi_path.exists() or vi_path.stat().st_size == 0:
        print(f"  [Transcribing Vietnamese] -> {vi_path.name}")
        segments, info = model.transcribe(
            str(audio_path),
            language="vi",
            task="transcribe",
            beam_size=5,
            vad_filter=True
        )
        with open(vi_path, "w", encoding="utf-8") as f:
            f.write(f"=== Bản Dịch Tiếng Việt (Native Vietnamese) ===\n")
            f.write(f"File: {audio_path.name}\n")
            f.write(f"Language: {info.language} (Probability: {info.language_probability:.2f})\n")
            f.write(f"Duration: {format_timestamp(info.duration)}\n")
            f.write("=" * 50 + "\n\n")
            for segment in segments:
                start_str = format_timestamp(segment.start)
                end_str = format_timestamp(segment.end)
                f.write(f"[{start_str} -> {end_str}] {segment.text.strip()}\n")
                f.flush()
    else:
        print(f"  [Skipping] Vietnamese transcript already exists.")

    # 2. English Translation
    if not en_path.exists() or en_path.stat().st_size == 0:
        print(f"  [Translating to English] -> {en_path.name}")
        segments, info = model.transcribe(
            str(audio_path),
            language="vi",
            task="translate",
            beam_size=5,
            vad_filter=True
        )
        with open(en_path, "w", encoding="utf-8") as f:
            f.write(f"=== English Translation ===\n")
            f.write(f"File: {audio_path.name}\n")
            f.write(f"Original Audio: Vietnamese\n")
            f.write(f"Duration: {format_timestamp(info.duration)}\n")
            f.write("=" * 50 + "\n\n")
            for segment in segments:
                start_str = format_timestamp(segment.start)
                end_str = format_timestamp(segment.end)
                f.write(f"[{start_str} -> {end_str}] {segment.text.strip()}\n")
                f.flush()
    else:
        print(f"  [Skipping] English transcript already exists.")

def main():
    parser = argparse.ArgumentParser(description="Process and transcribe Linda Recordings")
    parser.add_argument("--source", default=r"W:\New folder", help="Folder containing raw WAV recordings")
    parser.add_argument("--output", default=r"W:\Linda Recordings", help="Root folder for Linda Recordings")
    parser.add_argument("--model", default="medium", choices=["tiny", "base", "small", "medium", "large-v3-turbo", "large-v3"], help="Whisper model size")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"], help="Device to run Whisper on")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N files (for testing)")
    args = parser.parse_args()

    source_dir = Path(args.source)
    output_dir = Path(args.output)

    if not source_dir.exists():
        print(f"Error: Source directory {source_dir} does not exist.")
        sys.exit(1)

    # Filter real WAV files and sort by file size ascending (smallest first, biggest last)
    raw_files = {f.resolve(): f for f in source_dir.glob("*.[wW][aA][vV]") if not f.name.startswith("._")}
    wav_files = sorted(list(raw_files.values()), key=lambda f: f.stat().st_size)

    if args.limit:
        wav_files = wav_files[:args.limit]
    if not wav_files:
        print(f"No WAV files found in {source_dir}", flush=True)
        return

    print(f"Found {len(wav_files)} recording(s) in {source_dir} (sorted smallest to largest)", flush=True)
    print(f"Output destination: {output_dir}", flush=True)

    # Lazy-load model only when needed
    model = None

    for idx, wav_file in enumerate(wav_files, 1):
        dt = parse_recording_date(wav_file.name, wav_file)
        
        # Calculate Week (Monday through Sunday)
        start_of_week = dt.date() - timedelta(days=dt.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        week_folder_name = f"Week of {start_of_week.strftime('%Y-%m-%d')} ({start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d, %Y')})"
        
        # Day folder
        day_folder_name = dt.strftime("%Y-%m-%d")
        
        target_dir = output_dir / week_folder_name / day_folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        base_name = wav_file.stem
        compressed_audio = target_dir / f"{base_name}.mp3"
        vi_transcript = target_dir / f"{base_name}_vietnamese.txt"
        en_transcript = target_dir / f"{base_name}_english.txt"

        size_mb = wav_file.stat().st_size / (1024 * 1024)
        print(f"\n[{idx}/{len(wav_files)}] Processing: {wav_file.name} ({size_mb:.2f} MB)", flush=True)
        print(f"  Target: {target_dir}", flush=True)

        # Step 1: Compress audio
        compress_audio(wav_file, compressed_audio)

        # Check if transcription already done
        vi_done = vi_transcript.exists() and vi_transcript.stat().st_size > 0
        en_done = en_transcript.exists() and en_transcript.stat().st_size > 0

        if vi_done and en_done:
            print("  [Done] All transcripts already exist for this file.")
            continue

        # Step 2: Load Model (first time only)
        if model is None:
            print(f"  Loading Whisper model '{args.model}' on {args.device}...")
            import ctranslate2
            from faster_whisper import WhisperModel
            supported = ctranslate2.get_supported_compute_types(args.device)
            if "int8_float32" in supported:
                compute_type = "int8_float32"
            elif "float16" in supported:
                compute_type = "float16"
            elif "int8" in supported:
                compute_type = "int8"
            else:
                compute_type = "default"
            print(f"  Using compute type: {compute_type}")
            model = WhisperModel(args.model, device=args.device, compute_type=compute_type)

        # Step 3: Transcribe & Translate (uses compressed audio to save memory & speed up)
        transcribe_and_translate(model, compressed_audio, vi_transcript, en_transcript)

    print("\n" + "="*60)
    print("All recordings processed successfully!")
    print(f"Output folder: {output_dir}")
    print("="*60)

if __name__ == "__main__":
    main()
