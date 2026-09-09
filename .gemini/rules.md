# MediaClean & Jellyfin Server Development Rules

This workspace manages the media ingestion, standardization, and database maintenance pipeline for the self-hosted Jellyfin media server.

## 🔗 Project Context & Conversation History
- **Master Setup Conversation:** [MediaClean Genesis & Architecture](conversation://59c751de-43f9-4b15-bd47-dce3e006c61c)
- **Repository:** `git@github.com:ChrisGrantMKE/MediaHelper.git`
- **Interactive Documentation:** [`process_architecture.html`](file:///C:/code/MediaHelper/process_architecture.html)
- **Operational Guide:** [`STANDARDIZATION_GUIDE.md`](file:///C:/code/MediaHelper/STANDARDIZATION_GUIDE.md)

---

## 🗄️ Storage Locations & Infrastructure
- **Live SMB Storage Share:** `\\CHRISGRANTS\files\Media\Music Albums`
- **Host Machine:** Ubuntu Linux server (`CHRISGRANTS` / `192.168.8.241`)
- **Staging Dropzone:** `\\CHRISGRANTS\files\Media\Music Albums\_INCOMING`
- **Jellyfin Database:** `/home/chris/jellyfin/config/data/jellyfin.db` (Docker host path)

---

## 📂 The 6 Standard Library Buckets
1. `Ambient Classical & Jazz` (Ambient, Drone, Modern Classical, Minimalism, Jazz, Fusion, Japanese Ambient)
2. `Electronic` (Techno, House, Trance, Drum & Bass, Breakbeat, IDM, Hardcore, Industrial)
3. `Metal Industrial` (Metal, Industrial Metal, Thrash/Death/Black/Doom Metal)
4. `Reggae & World` (Reggae, Dub, African, Latin, Folk, Americana, Bluegrass)
5. `Rock & Pop` (Alt Rock, Classic Rock, Punk, Indie, Synthpop, Hip-Hop, R&B, Soul, Funk)
6. `Soundtracks & Holiday` (Movie/Game OSTs, Scores, Christmas, Holiday)

---

## 🛠️ Core Scripts & Workflows
- **`ingest_new_music.py` (`INGEST_NEW_MUSIC.bat`):** 
  - Automated intake from `_INCOMING`.
  - Converts lossless audio to 320k stereo MP3 via FFmpeg.
  - Applies 4-layer ambient detection and 2-tier genre taxonomy (`Main Genre; Subgenre`).
  - Automatically inverts Japanese/Classical `Last, First` naming patterns (e.g. `Yokota, Susumu` -> `Susumu Yokota`).
  - Preserves uppercase acronyms (`RS`, `DJ`, `MC`, `BT`, `DVA`, `XL`, `FX`).
  - Replaces incomplete albums if incoming copy has more tracks or higher bitrate.
  - Prints clean ASCII directory trees in terminal.
- **`unify_and_deduplicate_artists.py`:**
  - Library-wide deduplication engine.
  - Normalizes leading articles (`The Misfits` -> `Misfits`, `The Prodigy` -> `The Prodigy`).
  - Resolves foreign-script aliases (Hebrew `מזמור` -> `Mizmor`).
  - Executes safe 2-step Windows renames (`Rs Tangent` -> `__temp__` -> `RS Tangent`).
- **`clean_jellyfin_db.py`:**
  - Connects to Jellyfin SQLite database on Ubuntu server.
  - Creates automatic timestamped `.bak` safety backups.
  - Audits `BaseItems` table for 0-song orphaned artist records and purges them.
  - Runs SQLite `VACUUM` to compact the database.
