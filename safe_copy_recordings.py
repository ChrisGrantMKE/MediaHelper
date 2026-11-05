r"""
Safe copy from D:\RECORD to W:\New folder:
- Skips already safely copied files (matching size).
- Copies chunk-by-chunk (1 MB).
- Catches any read errors per-file without stopping the rest of the batch.
- Reports exact status of every file.
"""

import sys
import time
from pathlib import Path

SOURCE_DIR = Path(r"D:\RECORD")
DEST_DIR = Path(r"W:\New folder")
CHUNK_SIZE = 1024 * 1024  # 1 MB

def main():
    if not SOURCE_DIR.exists():
        print(f"Error: Source directory {SOURCE_DIR} does not exist.")
        sys.exit(1)

    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Only target actual recordings, ignore macOS ._ shadow files
    src_files = [f for f in SOURCE_DIR.glob("*.WAV") if not f.name.startswith("._")]
    src_files = sorted(src_files, key=lambda x: x.name)
    total_files = len(src_files)
    print(f"Found {total_files} real recording file(s) in {SOURCE_DIR}")
    print(f"Destination: {DEST_DIR}\n")

    successful = []
    skipped = []
    failed = []

    for idx, src in enumerate(src_files, 1):
        dst = DEST_DIR / src.name

        try:
            src_stat = src.stat()
            src_size = src_stat.st_size
            src_size_mb = src_size / (1024 * 1024)
        except Exception as e:
            print(f"[{idx}/{total_files}] FAILED to inspect {src.name}: {e}")
            failed.append((src.name, str(e)))
            continue

        # Check if already safely copied
        if dst.exists() and dst.stat().st_size == src_size:
            print(f"[{idx}/{total_files}] SKIP (Already safe): {src.name} ({src_size_mb:.1f} MB)")
            skipped.append(src.name)
            continue

        print(f"[{idx}/{total_files}] COPYING: {src.name} ({src_size_mb:.1f} MB)...", end="", flush=True)
        t0 = time.time()
        copied_bytes = 0

        try:
            with open(src, "rb") as f_in, open(dst, "wb") as f_out:
                while True:
                    chunk = f_in.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    copied_bytes += len(chunk)
            
            elapsed = time.time() - t0
            speed = (copied_bytes / (1024 * 1024)) / (elapsed if elapsed > 0 else 0.001)
            print(f" DONE in {elapsed:.1f}s ({speed:.1f} MB/s)")
            successful.append(src.name)

        except Exception as e:
            print(f" FAILED: {e}")
            if dst.exists() and dst.stat().st_size != src_size:
                # Remove incomplete copy
                try:
                    dst.unlink()
                except Exception:
                    pass
            failed.append((src.name, str(e)))

    print("\n" + "=" * 60)
    print("COPY SUMMARY:")
    print(f"  Total on USB:      {total_files}")
    print(f"  Already Safe:      {len(skipped)}")
    print(f"  Newly Copied:      {len(successful)}")
    print(f"  Total Safe on W:   {len(skipped) + len(successful)}")
    print(f"  Failed / Damaged:  {len(failed)}")
    if failed:
        print("\nFiles needing recovery:")
        for name, err in failed:
            print(f"  - {name}: {err}")
    print("=" * 60)

if __name__ == "__main__":
    main()
