import sqlite3
import os
import shutil
import datetime

db_path = "/home/chris/jellyfin/config/data/jellyfin.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    exit(1)

print("====================================================================")
print("              JELLYFIN GHOST ARTIST DIAGNOSTIC & CLEANER            ")
print("====================================================================")
print(f"📁 Database: {db_path}")

# 1. Backup
bak = f"{db_path}.bak_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(db_path, bak)
print(f"🛡️  Safety backup created: {bak}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Inspect ItemValues and ItemValuesMap
cur.execute("PRAGMA table_info(ItemValues);")
iv_cols = [c[1] for c in cur.fetchall()]
print(f"ItemValues columns: {iv_cols}")

cur.execute("PRAGMA table_info(ItemValuesMap);")
ivm_cols = [c[1] for c in cur.fetchall()]
print(f"ItemValuesMap columns: {ivm_cols}")

cur.execute("PRAGMA table_info(BaseItems);")
bi_cols = [c[1] for c in cur.fetchall()]
print(f"BaseItems columns: {bi_cols[:12]}...")

# 2. Get all distinct artist names that are ACTUALLY referenced by individual audio tracks
print("\nScanning BaseItems for all artists referenced by actual audio tracks...")
# In Jellyfin:
# - Individual audio tracks have type = 'MediaBrowser.Controller.Entities.Audio.Audio'
# - Parent albums or folders have type LIKE '%MusicAlbum%' or '%Folder%'
# - We filter strictly to individual audio tracks that have audio file paths
cur.execute("""
SELECT DISTINCT Artists 
FROM BaseItems 
WHERE type = 'MediaBrowser.Controller.Entities.Audio.Audio'
  AND (Path LIKE '%.mp3' OR Path LIKE '%.flac' OR Path LIKE '%.ogg' OR Path LIKE '%.m4a' OR Path LIKE '%.wav');
""")
audio_rows = cur.fetchall()

active_artist_names = set()
for r in audio_rows:
    for val in r:
        if val:
            val_str = str(val)
            for part in val_str.replace('[', '').replace(']', '').replace('"', '').split('|'):
                clean = part.strip()
                if clean:
                    active_artist_names.add(clean)

print(f"Found {len(active_artist_names)} unique active artist names referenced across individual audio tracks.")

# 3. Find all MusicArtist rows in BaseItems
cur.execute("""
SELECT Id, Name, type 
FROM BaseItems 
WHERE type = 'MediaBrowser.Controller.Entities.Audio.MusicArtist'
   OR type LIKE '%MusicArtist%';
""")
all_artist_rows = cur.fetchall()
print(f"Total MusicArtist rows in database: {len(all_artist_rows)}")

# 4. Compare and find ghost artists
sample_targets = ['01', '02', '03', '04', '05', '05_', '06', '06_', '07_', '08_', 'notag', 'wag 029', 'bonus track', 'bauhaus', 'va']
print("\n--- Inspecting Target/Suspicious Artists ---")

ghosts_to_delete = []

for art_id, name, atype in all_artist_rows:
    name_str = str(name).strip()
    is_active = (name_str in active_artist_names)
    
    nl = name_str.lower()
    if nl in ('01', '02', '03', '04', '05', '06', '07', '08', '05_', '06_', '07_', '08_', 'a', 'b', '[notag]', 'va') or any(t in nl for t in ['wag 029', 'bonus track']):
        status = "ACTIVE (Has Songs in BaseItems!)" if is_active else "GHOST (0 Songs)"
        print(f"  • '{name_str}' (ID={art_id}) -> Status: {status}")

    if not is_active:
        ghosts_to_delete.append((art_id, name_str))

print(f"\n====================================================================")
print(f"Total ghost artists with ZERO audio tracks across the entire library: {len(ghosts_to_delete)}")
print("====================================================================")

for gid, gname in ghosts_to_delete[:30]:
    print(f"   🗑️ Ghost: '{gname}' (ID={gid})")
if len(ghosts_to_delete) > 30:
    print(f"   ... and {len(ghosts_to_delete) - 30} more.")

if ghosts_to_delete:
    print(f"\nDeleting {len(ghosts_to_delete)} ghost artists from BaseItems...")
    cur.executemany("DELETE FROM BaseItems WHERE Id = ?", [(g[0],) for g in ghosts_to_delete])
    
    # Also clean orphan mappings if table exists
    if "ItemValuesMap" in ivm_cols:
        cur.executemany("DELETE FROM ItemValuesMap WHERE ItemId = ?", [(g[0],) for g in ghosts_to_delete])
    if "AncestorIds" in ivm_cols:
        cur.executemany("DELETE FROM AncestorIds WHERE ItemId = ?", [(g[0],) for g in ghosts_to_delete])
        
    conn.commit()
    print("🧹 Optimizing database (VACUUM)...")
    cur.execute("VACUUM;")
    conn.commit()
    print("🎉 All ghost artists have been permanently eliminated from Jellyfin!")
else:
    print("No ghost artists found.")

conn.close()
print("Done! You can now restart Jellyfin.")
