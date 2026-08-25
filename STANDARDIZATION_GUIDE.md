# Music Server Library & Metadata Standardization Guide

This document is the master operational manual for managing, ingesting, and maintaining the music library on the Jellyfin media server.

---

# Part 1: Quick-Start Instructions & Workflows

## 🚀 How to Add New Music (Automated Intake)

Whenever you download or acquire new music, follow this 3-step workflow:

### Step 1: Drop Files into Staging
Place your new music files or folders into the dedicated incoming folder:
```text
\\CHRISGRANTS\files\Media\Music Albums\_INCOMING
```

### Step 2: Run the Ingestion Engine
Simply double-click:
```text
INGEST_NEW_MUSIC.bat
```
*(Located directly in `\\CHRISGRANTS\files\Media\Music Albums\`)*

Or run via PowerShell:
```powershell
python "\\CHRISGRANTS\files\Media\Music Albums\ingest_new_music.py"
```

**What the script does automatically:**
1. Scans all tracks inside `_INCOMING`.
2. **Lossless / FLAC to 320 KBPS Stereo MP3 Conversion:**
   - If incoming files are FLAC, WAV, M4A, AIFF, or OGG, it automatically converts them via `ffmpeg` into high-quality **320 kbps stereo MP3s** (`-c:a libmp3lame -b:a 320k -ac 2`) while seamlessly transferring and retaining 100% of their metadata.
   - Deletes original uncompressed source files from staging once converted.
3. **Duplicate Album Detection & Quality Upgrade:**
   - If the incoming album already exists on the server, it compares track count (completeness) and audio quality.
   - **Completeness Rule:** If the incoming album has *more* songs (e.g. Deluxe Edition, bonus tracks, full release vs partial), the script upgrades to the complete release and removes the incomplete version.
   - **Quality Rule:** If track counts match, it compares audio quality (320 kbps MP3 upgrades older 128k/192k/256k rips).
4. Cleans track-number prefixes from artist names (e.g., `01 culture club` $\rightarrow$ `Culture Club`), while preserving genuine numeric band names like `2Pac`, `10cc`, `311`, `16 Volt`.
5. Normalizes accents to clean ASCII (`Touré` $\rightarrow$ `Toure`, `Björk` $\rightarrow$ `Bjork`).
6. Overwrites and formats genre tags into the strict **2-tier taxonomy** (`Main Genre; Subgenre`).
7. Infers which of the 6 library buckets the album belongs to *(prompts you in the terminal with a simple `[1-6]` choice if ambiguous)*.
8. **Artwork & Media Asset Migration:**
   - Automatically migrates all album cover art, booklets, and image files (`.jpg`, `.jpeg`, `.png`, `.webp`, `.pdf`) from the incoming folder directly into the destination album directory on the server.
   - Cleans up any leftover playlist, log, or cue junk files (`.nfo`, `.txt`, `.m3u`, `.sfv`, `.cue`, `.log`).
9. **Guaranteed Clean Staging:**
   - Recursively prunes and removes all subdirectories so that `_INCOMING` is **100% empty and clean** after every successful run.

### Step 3: Refresh Jellyfin
Open your **Jellyfin Dashboard $\rightarrow$ Libraries** and click **"Scan All Libraries"**.

---

## 🛠️ Routine Maintenance & Troubleshooting

If legacy duplicates or misnamed artist cards ever reappear in Jellyfin:

1. **Check Artist & Album Artist Tags:** Ensure `Album Artist` is populated (`Various Artists` for compilations; matching `Artist` for solo releases).
2. **Synchronize Folder Names:** Ensure the artist folder on disk matches the exact casing of the tag.
3. **Rescan Libraries:** In Jellyfin Dashboard $\rightarrow$ Libraries, trigger **"Scan All Libraries"** (or use *"Replace all metadata"* on the affected library if needed).

---

# Part 2: Specifications & Architecture

## 1. Top-Level Library Structure

All music is segregated into **6 primary library folders** and **1 staging folder** located at `\\CHRISGRANTS\files\Media\Music Albums\`:

| Library Folder | Included Genres / Categories |
| :--- | :--- |
| **`Ambient Classical & Jazz`** | Dark Ambient, Drone, Space Ambient, Atmospheric, Bebop, Cool Jazz, Fusion, Post-Bop, Modal Jazz, Baroque, Romantic, Contemporary Classical, Minimalism |
| **`Electronic`** | Techno, House, Trance, Drum & Bass, Breakbeat, Downtempo, IDM, Hardcore & Industrial |
| **`Metal Industrial`** | Metal, Industrial Metal, Black/Death/Thrash/Heavy/Doom Metal |
| **`Reggae & World`** | Reggae, Dub, World, African, Cuban, Folk, Americana, Bluegrass, Contemporary Folk, Alt-Country |
| **`Rock & Pop`** | Alternative Rock, Classic Rock, Hard Rock, Punk, Indie Rock, Progressive Rock, Synthpop, Indie Pop, Dance-Pop, Dream Pop, Hip-Hop, R&B, Soul, Funk |
| **`Soundtracks & Holiday`** | Movie/Game Soundtracks, Scores, OSTs, Holiday, Christmas |
| **`_INCOMING`** | *Temporary staging drop-zone for new music intake* |

---

## 2. Directory & File Naming Conventions

All sorted files strictly follow this hierarchy:

```text
<Library Folder>/
├── <Artist Name>/
│   ├── <Album Name>/
│   │   ├── 01 - <Track Title>.mp3
│   │   ├── 02 - <Track Title>.flac
│   │   └── cover.jpg
└── Compilations/
    └── <Album Name>/
        ├── 01 - <Track Title>.mp3
        └── 02 - <Track Title>.mp3
```

### File & Folder Rules:
- **Plain ASCII (No Accents):** Accents and extended characters are stripped to prevent duplicate directories on Windows/SMB shares (e.g., `Röyksopp` $\rightarrow$ `Royksopp`).
- **No Trailing Dots or Spaces:** Folder names must never end in dots or whitespace (e.g., `Fred again..` $\rightarrow$ `Fred again`).
- **Sanitized Path Characters:** Characters forbidden in Windows paths (`< > : " / \ | ? *`) are replaced with underscores.
- **Track Number Padding:** Audio files start with zero-padded two-digit track numbers (`01 - Title.ext`).
- **Junk Pruning:** Any folder containing zero playable audio files (`.mp3`, `.flac`, `.m4a`, `.ogg`, `.wav`) is deleted.

---

## 3. The 2-Tier Genre Taxonomy

All audio files are tagged using the format:  
`Main Genre; Subgenre`

### Taxonomy Reference

* **Ambient**
  - `Ambient; Dark Ambient`
  - `Ambient; Drone`
  - `Ambient; Space Ambient`
  - `Ambient; Atmospheric`
* **Electronic**
  - `Electronic; Techno`
  - `Electronic; House`
  - `Electronic; Trance`
  - `Electronic; Drum & Bass`
  - `Electronic; Breakbeat`
  - `Electronic; Downtempo`
  - `Electronic; IDM`
  - `Electronic; Hardcore & Industrial`
* **Rock**
  - `Rock; Alternative Rock`
  - `Rock; Classic Rock`
  - `Rock; Hard Rock`
  - `Rock; Punk`
  - `Rock; Indie Rock`
  - `Rock; Metal`
  - `Rock; Progressive Rock`
  - `Rock; Industrial Metal`
* **Hip-Hop**
  - `Hip-Hop; East Coast Hip-Hop`
  - `Hip-Hop; West Coast Hip-Hop`
  - `Hip-Hop; Conscious Hip-Hop`
  - `Hip-Hop; Trap`
  - `Hip-Hop; Instrumental Hip-Hop`
* **Jazz**
  - `Jazz; Bebop`
  - `Jazz; Cool Jazz`
  - `Jazz; Fusion`
  - `Jazz; Post-Bop`
  - `Jazz; Modal Jazz`
* **Pop**
  - `Pop; Synthpop`
  - `Pop; Indie Pop`
  - `Pop; Dance-Pop`
  - `Pop; Dream Pop`
* **Classical**
  - `Classical; Baroque`
  - `Classical; Romantic`
  - `Classical; Contemporary Classical`
  - `Classical; Minimalism`
* **Folk & Country**
  - `Folk & Country; Americana`
  - `Folk & Country; Bluegrass`
  - `Folk & Country; Contemporary Folk`
  - `Folk & Country; Alt-Country`
* **R&B & Soul**
  - `R&B & Soul; Contemporary R&B`
  - `R&B & Soul; Funk`
  - `R&B & Soul; Motown`
  - `R&B & Soul; Neo-Soul`

---

## 4. Artist & Album Artist Metadata Rules

To guarantee that Jellyfin consolidates all works by an artist onto a single artist card:

1. **Explicit `Album Artist` Field:** Every track must have an `Album Artist` tag populated:
   - Solo / single-band release: `Album Artist` = `Artist`
   - Compilations / Soundtracks: `Album Artist` = `Various Artists`
2. **Standard Title / Sentence Casing:**
   - When duplicate or inconsistent capitalizations exist (e.g. `BauHaus` vs `Bauhaus`, `THE CURE` vs `The Cure`), they are automatically normalized to standard **Title Case** (**`Bauhaus`**, **`The Cure`**).
   - Known acronyms are whitelisted and preserved (e.g., `2Pac`, `OMD`, `UB40`, `AFX`, `RJD2`, `U2`, `XTC`, `KMFDM`, `Neu!`, `Sunn O)))`).
3. **Two-Step Directory Synchronization on Windows:**
   - Because the Windows NTFS/SMB filesystem is case-insensitive, directory casing can diverge from ID3 tag casing (e.g., folder named `BauHaus` with tags `Bauhaus`).
   - The ingestion and maintenance scripts use a **two-step rename** via a temporary name (`BauHaus` $\rightarrow$ `__temp__` $\rightarrow$ `Bauhaus`) so that Windows updates the folder name on disk to match the tag case exactly.
4. **No Track / Disc Number Prefixes in Artist Tags:**
   - Accidental track/disc numbers in the artist field are stripped (e.g., `01 culture club` $\rightarrow$ `Culture Club`, `02 duran duran` $\rightarrow$ `Duran Duran`, `05 omd` $\rightarrow$ `OMD`, `05 ub40` $\rightarrow$ `UB40`).
5. **Numeric Band Whitelist:**
   - Genuine numeric band names are whitelisted and preserved:  
     `2Pac`, `10cc`, `311`, `16 Volt`, `9 Lazy 9`, `2 Bad Mice`, `1 Giant Leap`, `16 Bit Lolitas`, `51 Days`, `2 Player`, `3 Phase`, `12 Gauge`, `702`, `808 State`, `404.Zero`, `65daysofstatic`, `100 gecs`, `23 Skidoo`, `4Hero`, `2 Brothers On The 4th Floor`.
6. **No `<Unbekannt>` / Untagged Folders:**
   - Any placeholder foreign tags (like `<Unbekannt>`) are mapped to clean compilations under `Ambient Classical & Jazz`.
