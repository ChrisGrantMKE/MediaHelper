"""
Generate two unified chronological transcript files in W:\Linda Recordings:
1. FULL_CHRONOLOGICAL_TRANSCRIPT_ENGLISH.txt
2. FULL_CHRONOLOGICAL_TRANSCRIPT_VIETNAMESE.txt

Includes:
- Chronologically sorted entries for all 37 recordings.
- Detailed headers for each recording (date, time, duration, folder).
- Explicit note when no speech was detected.
- Table of contents with speech status indicators.
"""

import os
import re
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(r"W:\Linda Recordings")
EN_OUT = ROOT_DIR / "FULL_CHRONOLOGICAL_TRANSCRIPT_ENGLISH.txt"
VI_OUT = ROOT_DIR / "FULL_CHRONOLOGICAL_TRANSCRIPT_VIETNAMESE.txt"

def parse_datetime(filename: str) -> datetime:
    match = re.search(r'R(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})', filename)
    if match:
        y, m, d, hh, mm, ss = map(int, match.groups())
        return datetime(y, m, d, hh, mm, ss)
    return datetime.min

def parse_transcript_file(file_path: Path):
    duration = "Unknown"
    body_lines = []
    
    if not file_path.exists():
        return duration, body_lines
        
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    past_divider = False
    for line in lines:
        stripped = line.strip()
        if not past_divider:
            if stripped.startswith("Duration:"):
                duration = stripped.replace("Duration:", "").strip()
            elif stripped.startswith("====="):
                past_divider = True
        else:
            if stripped:
                body_lines.append(stripped)
                
    return duration, body_lines

def main():
    # Gather all recordings by finding the MP3 files
    mp3_files = sorted(list(ROOT_DIR.rglob("R2024*.mp3")), key=lambda p: parse_datetime(p.name))
    total_recordings = len(mp3_files)
    print(f"Found {total_recordings} recordings.")

    records = []
    for mp3 in mp3_files:
        dt = parse_datetime(mp3.name)
        base = mp3.stem
        parent_day = mp3.parent.name
        parent_week = mp3.parent.parent.name
        rel_folder = f"{parent_week} \\ {parent_day}"
        
        vi_path = mp3.parent / f"{base}_vietnamese.txt"
        en_path = mp3.parent / f"{base}_english.txt"
        
        dur_vi, vi_body = parse_transcript_file(vi_path)
        dur_en, en_body = parse_transcript_file(en_path)
        
        duration = dur_en if dur_en != "Unknown" else dur_vi
        
        records.append({
            "base": base,
            "mp3_name": mp3.name,
            "datetime": dt,
            "duration": duration,
            "folder": rel_folder,
            "vi_body": vi_body,
            "en_body": en_body,
            "has_speech": len(en_body) > 0 or len(vi_body) > 0
        })

    # =========================================================================
    # 1. BUILD ENGLISH DOCUMENT
    # =========================================================================
    print("Writing English chronological transcript...")
    with open(EN_OUT, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("           LINDA RECORDINGS - COMPLETE CHRONOLOGICAL TRANSCRIPT (ENGLISH)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Archive Root:   W:\\Linda Recordings\\\n")
        f.write(f"Total Sessions: {total_recordings} Recordings\n")
        f.write(f"Date Range:     July 24, 2024 to August 11, 2024\n")
        f.write(f"Language:       English (Direct Translation from Vietnamese Audio)\n")
        f.write(f"Generated On:   October 17, 2026\n")
        f.write("=" * 80 + "\n\n")

        f.write("TABLE OF CONTENTS / RECORDING INDEX:\n")
        f.write("-" * 80 + "\n")
        for idx, r in enumerate(records, 1):
            dt_str = r["datetime"].strftime("%Y-%m-%d %H:%M:%S")
            lines_cnt = len(r['en_body'])
            status = f"Speech Transcribed ({lines_cnt} lines)" if lines_cnt > 0 else "No speech detected (Quiet / Ambient)"
            f.write(f"  [{idx:02d}/37] {dt_str} | Duration: {r['duration']} | {status}\n")
        f.write("-" * 80 + "\n\n")

        # Recording Entries
        for idx, r in enumerate(records, 1):
            day_str = r["datetime"].strftime("%A, %B %d, %Y")
            time_str = r["datetime"].strftime("%I:%M:%S %p (%H:%M:%S)")
            f.write("=" * 80 + "\n")
            f.write(f"RECORDING {idx:02d} / {total_recordings:02d}: {r['base']}\n")
            f.write(f"Date:     {day_str}\n")
            f.write(f"Time:     {time_str}\n")
            f.write(f"Duration: {r['duration']}\n")
            f.write(f"Audio:    {r['mp3_name']}\n")
            f.write(f"Folder:   {r['folder']}\n")
            f.write("=" * 80 + "\n\n")

            if r["en_body"]:
                for line in r["en_body"]:
                    f.write(f"{line}\n")
            else:
                f.write("[NOTE: No speech detected in this recording. Audio was ambient background or silent.]\n")
            f.write("\n\n")

    # =========================================================================
    # 2. BUILD VIETNAMESE DOCUMENT
    # =========================================================================
    print("Writing Vietnamese chronological transcript...")
    with open(VI_OUT, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("       LINDA RECORDINGS - TOÀN BỘ BẢN GHI THEO THỨ TỰ THỜI GIAN (TIẾNG VIỆT)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Thư mục gốc:    W:\\Linda Recordings\\\n")
        f.write(f"Tổng số bản ghi: {total_recordings} Bản ghi âm\n")
        f.write(f"Khoảng thời gian: 24/07/2024 đến 11/08/2024\n")
        f.write(f"Ngôn ngữ:        Tiếng Việt (Bản phiên âm gốc từ giọng nói)\n")
        f.write(f"Ngày tạo:        17/10/2026\n")
        f.write("=" * 80 + "\n\n")

        f.write("MỤC LỤC BẢN GHI ÂM:\n")
        f.write("-" * 80 + "\n")
        for idx, r in enumerate(records, 1):
            dt_str = r["datetime"].strftime("%Y-%m-%d %H:%M:%S")
            lines_cnt = len(r['vi_body'])
            status = f"Có lời thoại ({lines_cnt} dòng)" if lines_cnt > 0 else "Không phát hiện lời nói (Yên tĩnh / Âm thanh nền)"
            f.write(f"  [{idx:02d}/37] {dt_str} | Thời lượng: {r['duration']} | {status}\n")
        f.write("-" * 80 + "\n\n")

        # Recording Entries
        for idx, r in enumerate(records, 1):
            date_str = r["datetime"].strftime("%d/%m/%Y")
            time_str = r["datetime"].strftime("%H:%M:%S")
            f.write("=" * 80 + "\n")
            f.write(f"BẢN GHI {idx:02d} / {total_recordings:02d}: {r['base']}\n")
            f.write(f"Ngày ghi âm: {date_str}\n")
            f.write(f"Giờ ghi âm:  {time_str}\n")
            f.write(f"Thời lượng:  {r['duration']}\n")
            f.write(f"Tệp âm thanh: {r['mp3_name']}\n")
            f.write(f"Thư mục:     {r['folder']}\n")
            f.write("=" * 80 + "\n\n")

            if r["vi_body"]:
                for line in r["vi_body"]:
                    f.write(f"{line}\n")
            else:
                f.write("[GHI CHÚ: Không phát hiện giọng nói trong bản ghi này. Tệp âm thanh chỉ có tiếng ồn nền hoặc yên tĩnh.]\n")
            f.write("\n\n")

    print("Done! Both documents created:")
    print(f"  - {EN_OUT} ({EN_OUT.stat().st_size} bytes)")
    print(f"  - {VI_OUT} ({VI_OUT.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
