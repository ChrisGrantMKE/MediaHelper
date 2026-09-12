import sqlite3
import os
import sys
import shutil
import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = "/home/chris/jellyfin/config/data/jellyfin.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    exit(1)

# 1. Backup
bak = f"{db_path}.bak_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(db_path, bak)
print(f"🛡️  Safety backup created: {bak}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

CANONICAL = "Stars of the Lid"
VARIANT = "Stars Of The Lid"

print(f"\nConsolidating '{VARIANT}' -> '{CANONICAL}' in Jellyfin DB...")

# Update Audio tracks
cur.execute("UPDATE BaseItems SET Artists = replace(Artists, ?, ?) WHERE Artists LIKE ?;", 
            (VARIANT, CANONICAL, f"%{VARIANT}%"))
print(f"  • Updated Artists on {cur.rowcount} track(s)")

cur.execute("UPDATE BaseItems SET AlbumArtists = replace(AlbumArtists, ?, ?) WHERE AlbumArtists LIKE ?;", 
            (VARIANT, CANONICAL, f"%{VARIANT}%"))
print(f"  • Updated AlbumArtists on {cur.rowcount} track(s)")

# Update MusicAlbum rows
cur.execute("UPDATE BaseItems SET Artists = replace(Artists, ?, ?) WHERE type LIKE '%MusicAlbum%' AND Artists LIKE ?;", 
            (VARIANT, CANONICAL, f"%{VARIANT}%"))
print(f"  • Updated Artists on {cur.rowcount} album(s)")

cur.execute("UPDATE BaseItems SET AlbumArtists = replace(AlbumArtists, ?, ?) WHERE type LIKE '%MusicAlbum%' AND AlbumArtists LIKE ?;", 
            (VARIANT, CANONICAL, f"%{VARIANT}%"))
print(f"  • Updated AlbumArtists on {cur.rowcount} album(s)")

# Find the MusicArtist card for "Stars Of The Lid"
cur.execute("""
SELECT Id, Name FROM BaseItems 
WHERE (type = 'MediaBrowser.Controller.Entities.Audio.MusicArtist' OR type LIKE '%MusicArtist%')
  AND Name = ?;
""", (VARIANT,))
variant_cards = cur.fetchall()

for cid, cname in variant_cards:
    print(f"  🗑️ Deleting duplicate MusicArtist card: '{cname}' (ID={cid})")
    cur.execute("DELETE FROM BaseItems WHERE Id = ?;", (cid,))
    try:
        cur.execute("DELETE FROM ItemValuesMap WHERE ItemId = ?;", (cid,))
    except: pass
    try:
        cur.execute("DELETE FROM AncestorIds WHERE ItemId = ?;", (cid,))
    except: pass

conn.commit()
print("🧹 Running VACUUM...")
cur.execute("VACUUM;")
conn.commit()
conn.close()

print("\n🎉 Done! 'Stars Of The Lid' is now completely merged into 'Stars of the Lid'.")
