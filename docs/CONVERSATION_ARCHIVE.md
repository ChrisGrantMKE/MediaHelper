# MediaClean Master Conversation Archive & Project Log

**Conversation ID:** `59c751de-43f9-4b15-bd47-dce3e006c61c`  
**Direct Conversation URI:** [`conversation://59c751de-43f9-4b15-bd47-dce3e006c61c`](conversation://59c751de-43f9-4b15-bd47-dce3e006c61c)  
**Raw Transcripts Stored At:** [`docs/transcript.jsonl`](transcript.jsonl) and [`docs/transcript_full.jsonl`](transcript_full.jsonl)  
**Repository:** [`git@github.com:ChrisGrantMKE/MediaHelper.git`](https://github.com/ChrisGrantMKE/MediaHelper)

---

## 📖 Executive Summary of Development History

This document preserves the complete chronological history, technical decisions, debugging milestones, and architectural evolution of the **MediaClean** project developed across this conversation session.

---

## 🗺️ Chronological Milestone Timeline

### Phase 1: Ingestion Engine & Quality Upgrade Pipeline
- **Problem:** New music added to the server had messy tags, unpadded track numbers, arbitrary bitrates, and mixed audio formats (FLAC, WAV, M4A, OGG, MP3).
- **Solution:** Built `ingest_new_music.py` and `INGEST_NEW_MUSIC.bat`.
  - **Lossless Transcoding:** Converts incoming lossless/non-MP3 files to **320 kbps constant bitrate stereo MP3s** via FFmpeg (`libmp3lame`) with 100% tag preservation.
  - **Completeness Rule:** Automatically upgrades existing albums if the incoming release has more tracks (e.g. Deluxe Edition, Bonus tracks, full release vs partial).
  - **Quality Rule:** Upgrades lower-bitrate rips (128k, 192k) to 320k MP3s while discarding inferior duplicates.
  - **Asset Migration:** Transfers cover art (`.jpg`, `.png`, `.webp`, `.pdf`) and purges leftover junk (`.nfo`, `.m3u`, `.sfv`, `.cue`, `.log`).
  - **ASCII Tree Visualizer:** Renders a clean ASCII folder hierarchy diagram in the terminal after every ingested album or track.

---

### Phase 2: Numbered Artist Tag Recovery (62 Tracks)
- **Problem:** In `Electronic/Compilations/Electronic Rarities`, 62 tracks were tagged with numbers (`01` through `12`, `A02`, `1213`) in the artist field, obscuring the true artists.
- **Solution:** Recovered all 62 tracks using filename pattern extraction and ID3 tagging:
  - `The Prodigy`, `The Chemical Brothers`, `Uberzone`, `The Crystal Method`, `Underworld`, `CJ Bolland`, `Fatboy Slim`, `Otto Von Schirach`, `Propellerheads`, `BT`, `PF Project feat. Ewan McGregor`, `Harmonicom`.
  - Set `Album Artist = Various Artists` across the compilation.

---

### Phase 3: Full-Library Deduplication Engine (`unify_and_deduplicate_artists.py`)
- **Problem:** Legacy folders with typo variants existed across libraries (e.g. `Meat Bea Manifesto` vs `Meat Beat Manifesto`, `Alexander Robotnik` vs `Alexander Robotnick`, `Air Liquid` vs `Air Liquide`).
- **Solution:** Built `unify_and_deduplicate_artists.py`.
  - Audited all 6 libraries across 49 candidate clusters.
  - Implemented safe **2-step Windows renames** via temporary folders to overcome Windows case-insensitivity limitations.
  - Added strict false-positive guards (`Live` vs `Olive`, `Mesh` vs `Nmesh`).

---

### Phase 4: Jellyfin Database Ghost Record Purge Engine (`clean_jellyfin_db.py`)
- **Problem:** Even after unifying folders and tags on disk, Jellyfin continued to display duplicate artist cards (`BauHaus` alongside `Bauhaus`, `bog body` alongside `Bog Body`). Re-creating the library did not fix it.
- **Root Cause Discovered:** In Jellyfin (10.8+ through 10.11+), `MusicArtist` entities are stored in a **global server-wide SQLite table (`BaseItems`)** independent of library folders. When files on disk are renamed, Jellyfin unlinks the tracks but **never drops the empty 0-song artist rows from the database**.
- **Solution:** Developed `clean_jellyfin_db.py`.
  - Connects directly to `/home/chris/jellyfin/config/data/jellyfin.db`.
  - Creates automatic timestamped safety backups (`.bak`).
  - Audits `BaseItems` for all active audio tracks and deletes all orphaned 0-track ghost artist records.
  - Successfully purged **~200 ghost records** and executed SQLite `VACUUM`.

---

### Phase 5: Leading-Article & Foreign Script Deduplication
- **Problem:** Pairs like `The Misfits` vs `Misfits`, `The Prodigy` vs `Prodigy`, `The Smiths` vs `Smiths`, and Hebrew `מזמור` vs `Mizmor` were skipped by the initial deduplication pass.
- **Root Cause Discovered:** The fuzzy similarity check was evaluating character length differences (`abs(len(f1) - len(f2)) <= 2`) on the **raw un-normalized strings**. The 4-letter prefix `"The "` exceeded the 2-character limit.
- **Solution:**
  - Upgraded to an **Exact Normalized Match Rule** (`norm1 == norm2` after stripping leading articles and punctuation).
  - Added foreign-script transliteration dictionary (`מזמור` $\rightarrow$ `Mizmor`).
  - Unified 15 collection-wide clusters (`The Misfits` $\rightarrow$ `Misfits`, `The Prodigy`, `The Smiths`, `The Chemical Brothers`, `The Future Sound of London`, `The Orb`, `The Twinkle Brothers`, `The Sisters of Mercy`, `The Jesus and Mary Chain`, `The B-52's`).

---

### Phase 6: Acronym-Aware Title Casing & Standalone Self-Healing
- **Problem:** Uppercase acronyms (`RS Tangent`, `Clock DVA`, `DJ Shadow`) were being title-cased down to `Rs Tangent`, `Clock Dva`, `Dj Shadow`.
- **Solution:**
  - Replaced hardcoded dictionaries with **algorithmic acronym detection**: any 2-to-5 letter uppercase word (`RS`, `DJ`, `MC`, `BT`, `DVA`, `XL`, `FX`, `MF`) is automatically preserved.
  - Added a **Standalone Self-Healing Casing Pass** that audits single folders on disk and automatically brings their folder names and tags into canonical case alignment. Corrected **85 casing misalignments**.

---

### Phase 7: 4-Layer Ambient Detection & Library Re-alignment
- **Problem:** Newly imported ambient masters (`Susumu Yokota`, `Lusine`, `Ludwig A.F. Rohrscheid`, `H. Takahashi & David Edren`, `Studio`, `Alabaster DePlume`) were cataloged as generic `Electronic; IDM` or `Rock; Alternative Rock`.
- **Solution:**
  - Built a **4-Layer Ambient Classification Engine**:
    1. *Known Ambient Artists Catalog* (Eno, Yokota, Budd, Lusine, Stars of the Lid, Basinski, etc.).
    2. *Expanded Ambient Keyword Net* (`chillout`, `soundscape`, `drone`, `field recordings`, `japanese ambient`, `modular`, `berlin school`, `minimalism`, `krautrock`, `neo-classical`).
    3. *Ambient Precedence Rule* (Ambient subgenres always beat generic parent buckets).
    4. *Interactive CLI Fallback* (Prompts `[1-6]` for ambiguous releases rather than silently guessing).
  - Added automatic `Last, First` name inversion (`Yokota, Susumu` $\rightarrow$ `Susumu Yokota`).
  - Migrated and retagged **29 ambient releases** into **`Ambient Classical & Jazz`**.

---

### Phase 8: Playback Error & 0-Byte Audio File Audit
- **Problem:** Jellyfin threw an error attempting to play `04 - Various Artists - - Black Coffee.flac` (which displayed year `1900` and the András Schiff cover).
- **Solution:**
  - Audited the file and discovered it was a **corrupted 0-byte file**.
  - Scanned the entire collection across all 6 libraries and purged the only 3 zero-byte files found.
  - Added a pre-flight 0-byte deletion guard in `ingest_new_music.py`.

---

### Phase 9: Single-File Interactive Architecture Guide
- **Deliverable:** Created `process_architecture.html`.
  - Self-contained interactive single-file web application.
  - Features an interactive visual process map connecting all 9 modules with clickable navigation.
  - Includes a **Live Interactive Tag & Library Classifier Sandbox**.

---

### Phase 10: Real-Time Jellyfin Playback Tracker & Bandcamp Release Notifier
- **Problem:** When listening to music in Jellyfin, there was no automated way to discover if favorite artists have newer or unowned releases on Bandcamp without manual checking.
- **Solution:** Designed and deployed an event-driven discovery pipeline.
  - **Jellyfin Webhook Daemon (`jellyfin_listener.py`):** Runs on port 5055 as a Linux systemd service (`jellyfin_bandcamp.service`). Listens for `PlaybackStop` events from Jellyfin's official Webhook plugin.
  - **SQLite Playback Tracker (`playback_tracker.py`):**
    - Tracks play counts per artist within a rolling 24-hour window in `media_tracker.db`.
    - Automatically triggers when you reach **3 plays in 24 hours** from any artist.
    - Implements a **7-day cooldown guard** to avoid spam during album binges.
    - Supports recurring nudges: after 7 days, if you listen again, it nudges you about new releases unless explicitly muted.
  - **Library Inspector (`library_inspector.py`):** Audits local albums on disk and in `jellyfin.db` to extract owned albums and the latest release year.
  - **Bandcamp Discovery Engine (`bandcamp_client.py`):** Scrapes Bandcamp discographies directly without triggering bot protection, parsing `application/ld+json` for release dates and artwork.
  - **Multi-Channel Notifier (`notifier.py`):** Dispatches alerts via ntfy push notifications (`SeaGee_new_releases`), local Markdown (`NEW_RELEASES.md`), Discord webhooks, or HTML emails.
  - **Interactive Action Buttons:** Direct buttons on the phone push notification:
    - `Open Bandcamp`: Opens release in browser.
    - `Ignore Release`: Mutes this specific album forever.
    - `Mute Artist`: Mutes the entire artist forever.
  - **CLI Testing & Management Suite (`test_integration.py`):** Provides instant simulation, testing, and ignore list management (`--ignore-artist`, `--ignore-release`, `--list-ignored`).

---

## 🛠️ Summary of Scripts & Tools in Repository

| Script | Purpose |
| :--- | :--- |
| **`jellyfin_listener.py`** | Lightweight HTTP webhook server (port 5055) receiving Jellyfin playback events and handling interactive actions. |
| **`playback_tracker.py`** | SQLite tracker (`media_tracker.db`) counting plays, enforcing 7-day cooldowns, and managing ignore lists. |
| **`library_inspector.py`** | Cross-checks owned albums on disk and in `jellyfin.db` to identify newest release years. |
| **`bandcamp_client.py`** | Crawls Bandcamp artist discographies and extracts release dates, titles, and artwork via JSON-LD. |
| **`notifier.py`** | Dispatches notifications to ntfy mobile push, Markdown (`NEW_RELEASES.md`), Discord, or Email. |
| **`test_integration.py`** | CLI simulation and management tool for testing Bandcamp queries, plays, and muted items. |
| **`jellyfin_bandcamp.service`** | Systemd unit file for 24/7 background service deployment on Linux. |
| **`START_WEBHOOK_LISTENER.bat`** | Windows one-click launcher for local testing. |
| **`config.json` / `config.example.json`** | Configuration file for ports, thresholds, paths, and notification channels. |
| **`ingest_new_music.py`** | Automated staging intake, 320k transcoding, ambient classification, name inversion, and quality upgrades. |
| **`INGEST_NEW_MUSIC.bat`** | One-click Windows launcher for the ingestion engine. |
| **`unify_and_deduplicate_artists.py`** | Collection-wide deduplication engine with 2-step Windows renames and self-healing casing. |
| **`clean_jellyfin_db.py`** | SQLite database cleaner that purges 0-track ghost artist cards and vacuums `jellyfin.db`. |
| **`process_architecture.html`** | Interactive visual process map and real-time classifier tester. |
| **`STANDARDIZATION_GUIDE.md`** | Master operational manual and 2-tier genre taxonomy guide. |
| **`.gemini/rules.md`** | Persistent workspace rules and conversation bridge for Antigravity/Gemini. |
