import os
import sys
import subprocess
import time
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
import mutagen

# Force UTF-8 output to prevent Windows console crashes on special characters
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = r"\\CHRISGRANTS\files\Media\Books\Audiobooks"
INCOMING_DIR = os.path.join(ROOT_DIR, "_INCOMING")

def needs_optimization(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.mp3':
            audio = MP3(filepath)
            bitrate = audio.info.bitrate // 1000 if audio.info else 0
            channels = audio.info.channels if audio.info else 2
            if bitrate > 70 or channels > 1:
                return True
            return False
        elif ext in ['.m4a', '.m4b', '.mp4']:
            audio = MP4(filepath)
            bitrate = audio.info.bitrate // 1000 if hasattr(audio.info, 'bitrate') else 0
            channels = audio.info.channels if hasattr(audio.info, 'channels') else 2
            if bitrate > 70 or channels > 1:
                return True
            return False
        else:
            return True
    except Exception:
        return True

def optimize_file(src_filepath):
    base_no_ext = os.path.splitext(src_filepath)[0]
    out_path = f"{base_no_ext}_opt.mp3"
    
    print(f"Optimizing: {src_filepath}")
    
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", src_filepath,
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "64k",
        "-ac", "1",
        out_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            success = False
            # Retry loop in case Plex/Jellyfin or Windows is locking the file
            for _ in range(5):
                try:
                    os.remove(src_filepath)
                    os.rename(out_path, f"{base_no_ext}.mp3")
                    success = True
                    break
                except OSError:
                    time.sleep(2)
                    
            if success:
                print(f"  -> Done.")
            else:
                print(f"  [!] Failed to replace file (locked by another process). Kept original.")
                try: os.remove(out_path)
                except: pass
        else:
            print(f"  [!] Failed to generate valid output for {src_filepath}")
    except Exception as e:
        print(f"  [!] Error processing {src_filepath}: {e}")
        try: os.remove(out_path)
        except: pass

def process_library():
    print("==========================================================")
    print("    Library-Wide Audiobook Optimizer (64kbps Mono MP3)    ")
    print("==========================================================")
    
    files_to_optimize = []
    
    print("Scanning library for unoptimized files... This may take a moment.")
    for root, dirs, files in os.walk(ROOT_DIR):
        if INCOMING_DIR in root:
            continue
        for f in files:
            if f.lower().endswith(('.mp3', '.m4a', '.m4b', '.ogg', '.flac', '.wav')):
                fp = os.path.join(root, f)
                if needs_optimization(fp):
                    files_to_optimize.append(fp)

    total = len(files_to_optimize)
    print(f"Found {total} files requiring optimization.")
    
    if total == 0:
        print("Library is fully optimized!")
        return
        
    for idx, fp in enumerate(files_to_optimize, start=1):
        print(f"\n[{idx}/{total}]")
        optimize_file(fp)
        
    print("\nOptimization Complete!")

if __name__ == "__main__":
    process_library()
