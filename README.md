# MediaClean 🎵

**MediaClean** is an automated music library ingestion, metadata standardization, and duplicate upgrade engine designed for self-hosted media servers (such as Jellyfin, Plex, and Navidrome).

It eliminates messy tags, rogue artist cards, unorganized folders, and low-quality duplicates by enforcing strict taxonomy, audio encoding standards, and directory structures.

---

## ✨ Features

- **🚀 1-Click Intake Workflow:** Drop albums into `_INCOMING` and run `INGEST_NEW_MUSIC.bat` (or `python ingest_new_music.py`).
- **🎧 Auto FLAC / Lossless to 320k MP3 Conversion:** Automatically detects uncompressed audio (`.flac`, `.wav`, `.m4a`, `.ogg`, `.aiff`) and converts them to **320 kbps constant bitrate stereo MP3s** (`-c:a libmp3lame -b:a 320k -ac 2`) via `ffmpeg`, transferring 100% of metadata.
- **🧠 Duplicate Album & Quality Upgrade Engine:**
  - **Completeness Rule:** Automatically upgrades incomplete albums to full releases / Deluxe editions if incoming has more tracks.
  - **Quality Rule:** Upgrades lower-bitrate rips to 320 kbps MP3s while discarding inferior duplicates.
- **🏷️ Strict 2-Tier Genre Taxonomy:** Replaces cluttered genre tags with a clean `Main Genre; Subgenre` hierarchy (e.g. `Rock; Metal`, `Electronic; Techno`).
- **🔤 Title-Case & Casing Harmonization:** Eliminates duplicate artist entries caused by mixed case (e.g. `BauHaus` vs `Bauhaus`), while preserving legitimate acronyms (`2Pac`, `OMD`, `UB40`, `AFX`, `RJD2`, `U2`, `XTC`, `KMFDM`, `Neu!`, `Sunn O)))`).
- **🔢 Track-Prefix Stripping:** Cleans accidental track numbers from artist fields (e.g., `01 culture club` $\rightarrow$ `Culture Club`), while protecting real numeric bands (`10cc`, `311`, `16 Volt`, `808 State`, `404.Zero`).
- **🖼️ Media Asset & Artwork Migration:** Automatically moves cover art, booklets, and images (`.jpg`, `.jpeg`, `.png`, `.webp`, `.pdf`) into the destination album directory and removes leftover junk (`.nfo`, `.m3u`, `.sfv`, `.cue`, `.log`).
- **🧹 Guaranteed Clean Staging:** Completely prunes all empty folders and non-audio junk from `_INCOMING` after every successful run.

---

## 📁 Standard Directory Architecture

```text
Music Albums/
├── _INCOMING/                               <-- Staging drop-zone
├── Ambient Classical & Jazz/
├── Electronic/
├── Metal Industrial/
├── Reggae & World/
├── Rock & Pop/
└── Soundtracks & Holiday/
    └── <Artist>/
        └── <Album>/
            ├── 01 - Track Title.mp3
            ├── 02 - Track Title.mp3
            └── cover.jpg
```

---

## 🛠️ Prerequisites

- **Python 3.10+**
- **FFmpeg** (accessible in system `PATH` for 320k MP3 encoding)
- **Mutagen** for ID3/FLAC/MP4 tag manipulation:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### 1. Configuration
Open `ingest_new_music.py` and set your music root directory:
```python
ROOT_DIR = r"\\CHRISGRANTS\files\Media\Music Albums"
```

### 2. Ingesting Music
1. Drop your new music folders or tracks into:
   ```text
   <Music Root>/_INCOMING
   ```
2. Double-click **`INGEST_NEW_MUSIC.bat`** (or run `python ingest_new_music.py`).
3. In your Jellyfin/Plex dashboard, click **"Scan All Libraries"**.

---

## 📖 Master Documentation
For the full taxonomy list, library bucket mappings, and artist rules, refer to [STANDARDIZATION_GUIDE.md](STANDARDIZATION_GUIDE.md).
