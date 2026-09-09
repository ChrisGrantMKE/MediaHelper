# MediaClean 🎵

**MediaClean** is an automated music library ingestion, metadata standardization, fuzzy artist deduplication, and quality upgrade engine designed for self-hosted media servers (such as Jellyfin, Plex, and Navidrome).

It permanently eliminates messy tags, rogue artist cards, unorganized folders, and low-quality duplicates by enforcing strict taxonomy, audio encoding standards, and directory structures.

👉 **[Interactive Master Process Architecture Diagram & Code Guide (`process_architecture.html`)](process_architecture.html)** — *Clickable end-to-end visual process map with interactive code breakdowns and live tag classifier sandbox.*

---

## ✨ Features

- **🚀 1-Click Intake Workflow:** Drop albums into `_INCOMING` and run `INGEST_NEW_MUSIC.bat` (or `python ingest_new_music.py`).
- **🔍 Pre-Flight Fuzzy Deduplication:** Ingestion checks existing library artist names using fuzzy string matching ($\ge 90\%$). Prevents typos like `Meat Bea Manifesto` or `Alexander Robotnik` from creating duplicate artist cards.
- **🎧 Auto FLAC / Lossless to 320k MP3 Conversion:** Automatically detects uncompressed audio (`.flac`, `.wav`, `.m4a`, `.ogg`, `.aiff`) and converts them to **320 kbps constant bitrate stereo MP3s** (`-c:a libmp3lame -b:a 320k -ac 2`) via `ffmpeg`, transferring 100% of metadata.
- **🧠 Duplicate Album & Quality Upgrade Engine:**
  - **Completeness Rule:** Automatically upgrades incomplete albums to full releases / Deluxe editions if incoming has more tracks.
  - **Quality Rule:** Upgrades lower-bitrate rips to 320 kbps MP3s while discarding inferior duplicates.
- **🏷️ Strict 2-Tier Genre Taxonomy:** Replaces cluttered genre tags with a clean `Main Genre; Subgenre` hierarchy (e.g. `Rock; Metal`, `Electronic; Techno`).
- **🔤 Acronym & Stylization Whitelist:** Preserves legitimate acronyms (`MDFMK`, `MASTER BOOT RECORD`, `KMFDM`, `2Pac`, `OMD`, `UB40`, `AFX`, `RJD2`, `U2`, `XTC`, `B12`, `154`, `69`, `16B`, `Alt-J`).
- **🔢 Track-Prefix Stripping:** Cleans accidental track numbers from artist fields (e.g., `01 culture club` $\rightarrow$ `Culture Club`, `01 - 12 - Uberzone` $\rightarrow$ `Uberzone`).
- **🖼️ Media Asset & Artwork Migration:** Automatically moves cover art, booklets, and images (`.jpg`, `.jpeg`, `.png`, `.webp`, `.pdf`) into the destination album directory and removes leftover junk (`.nfo`, `.m3u`, `.sfv`, `.cue`, `.log`).
- **🧹 Guaranteed Clean Staging:** Completely prunes all empty folders and non-audio junk from `_INCOMING` after every successful run.
- **🔄 Library-Wide Deduplication Engine:** Run `python unify_and_deduplicate_artists.py` anytime to scan all libraries, cluster duplicates, and execute safe two-step Windows folder merges.
- **🧹 Jellyfin Ghost Artist Purge Engine:** Run `sudo python3 clean_jellyfin_db.py` directly on the server to automatically purge orphaned 0-track ghost artist cards left behind in Jellyfin's SQLite database (`jellyfin.db`), complete with automatic pre-run backups.

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

### 1. Ingesting New Music
1. Drop your new music folders or tracks into:
   ```text
   <Music Root>/_INCOMING
   ```
2. Double-click **`INGEST_NEW_MUSIC.bat`** (or run `python ingest_new_music.py`).
3. In your Jellyfin/Plex dashboard, click **"Scan All Libraries"**.

### 2. Running Library-Wide Deduplication
To audit and merge duplicates across your existing libraries:
```bash
python unify_and_deduplicate_artists.py
```

### 3. Purging Jellyfin Ghost Artists from the Database
If Jellyfin retains empty ghost artist cards (e.g. after casing changes or removed albums):
```bash
# On your server host (or inside Docker):
docker stop jellyfin
sudo python3 clean_jellyfin_db.py
docker start jellyfin
```
The script will automatically back up your database, identify all 0-song ghost records, delete them, and optimize SQLite.

### 4. Real-Time Bandcamp Release Watcher (Jellyfin Webhook)
Automatically detects when you listen to **3 songs from any artist in 24 hours**, checks your collection, and queries Bandcamp for newer or unowned releases:

```bash
# Start on Linux via systemd (runs 24/7 in background):
sudo systemctl enable --now jellyfin_bandcamp

# Or run interactively:
python jellyfin_listener.py config.json

# Test an artist or simulate plays via CLI:
python test_integration.py --test-bandcamp "Artist Name"
python test_integration.py --simulate-plays "Artist Name" --count 3

# Manage muted artists & ignored releases:
python test_integration.py --list-ignored
python test_integration.py --ignore-artist "Artist Name"
python test_integration.py --ignore-release "Artist Name" "Album Title"
```

#### ⚙️ Jellyfin Webhook Configuration (Docker Host Networking)
1. **Restart Jellyfin Docker:** If you just installed the Webhook plugin, restart the container so it initializes: `sudo docker restart jellyfin`.
2. **Add Destination:** Go to **Dashboard $\rightarrow$ Plugins $\rightarrow$ Webhook**, and click **Add Generic Destination**.
3. **Webhook URL:** When Jellyfin runs in Docker, `localhost` loops back into the container. Point it to your server host IP:
   ```text
   http://192.168.8.241:5055/webhook  (or http://172.17.0.1:5055/webhook)
   ```
4. **Events & Types:**
   - **Notification Type:** Check `Playback Stop` (and/or `Playback Start`).
   - **Item Type:** Check `Audio` (or select `Songs` and `Albums`).
   - **Send All Properties:** Check the box ✅.

#### 🧠 Intelligent Matching & Discovery Engine
- **Suffix & Suffix Protection:** Unlike naive substring matchers, the engine recognizes that `ii`, `2`, `Live`, `Remix`, `Deluxe`, `Dub`, and `Instrumental` represent distinct releases, preventing sequels (e.g. *The Universe Smiles Upon You ii*) from being falsely skipped if you own the original album.
- **Recent Era Window:** Always checks for unowned releases from the last 2–3 years, so live releases and EPs aren't hidden just because you own an album from the current year.
- **7-Day Cooldown & Recurring Nudges:** Enforces a 7-day cooldown per artist. After 7 days, if you listen to that artist again, it will nudge you again about new music unless you explicitly muted it.
- **Interactive Action Buttons (ntfy):** Tappable buttons directly on your phone's push notification card:
  - `[ Open Bandcamp ]`: Opens the album page directly in your browser.
  - `[ Ignore Release ]`: Permanently mutes that specific release.
  - `[ Mute Artist ]`: Permanently mutes that artist from future scans.

---

## 📖 Master Documentation
For the full taxonomy list, library bucket mappings, and artist rules, refer to [STANDARDIZATION_GUIDE.md](STANDARDIZATION_GUIDE.md).

---

## 📋 Roadmap & Next Up
- [ ] **Cloudflare REST API Auto-IP Updating (Dynamic DNS):** Automatic public IP detection and DNS record synchronization for `chrisgrants.net`. See full technical design in [TODO.md](TODO.md).
