import os
import subprocess
import shutil
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error as id3_error

PROC_DIR = r"C:\code\ebook2audiobook\tmp\proc-956d2ec4-5e9f-4906-9c58-97befcb8e067\5a79838a8d09bf8dc2d8f45472bcc2d7"
COMBINED_AUDIO = os.path.join(PROC_DIR, "The_Intentional_Father.flac")
METADATA_FILE = os.path.join(PROC_DIR, "metadata.txt")
COVER_FILE = r"c:\code\MediaHelper\The Intentional Father\cover.jpg"
OUTPUT_MP3 = r"c:\code\MediaHelper\The Intentional Father\IntentionalFather.mp3"

ffmpeg_exe = shutil.which("ffmpeg")

print(f"Starting ffmpeg encoding from {COMBINED_AUDIO}...")
cmd = [
    ffmpeg_exe,
    "-y",
    "-hide_banner",
    "-thread_queue_size", "1024",
    "-i", COMBINED_AUDIO,
    "-f", "ffmetadata",
    "-i", METADATA_FILE,
    "-map", "0:a",
    "-map_metadata", "1",
    "-c:a", "libmp3lame",
    "-b:a", "64k",
    "-ar", "44100",
    "-ac", "1",
    "-af", "dynaudnorm=f=150:g=15,afftdn=nf=-70",
    OUTPUT_MP3
]

print("Running command...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    print("FFmpeg error:", res.stderr)
    exit(1)

print("FFmpeg encoding completed successfully!")
print(f"Output MP3 size: {os.path.getsize(OUTPUT_MP3):,} bytes")

if os.path.exists(COVER_FILE):
    print("Embedding cover art...")
    audio = MP3(OUTPUT_MP3, ID3=ID3)
    try:
        audio.add_tags()
    except id3_error:
        pass
    with open(COVER_FILE, "rb") as img:
        audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=img.read()))
    audio.save()
    print("Cover art embedded successfully!")

print("All done!")
