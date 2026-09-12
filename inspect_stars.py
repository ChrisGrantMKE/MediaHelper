import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = "/home/chris/jellyfin/config/data/jellyfin.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("====================================================================")
print("             INSPECTING STARS OF THE LID IN JELLYFIN.DB             ")
print("====================================================================")

# 1. Check MusicArtist entries
cur.execute("""
SELECT Id, Name, type 
FROM BaseItems 
WHERE (type = 'MediaBrowser.Controller.Entities.Audio.MusicArtist' OR type LIKE '%MusicArtist%')
  AND lower(Name) = 'stars of the lid';
""")
artist_rows = cur.fetchall()
print(f"\nFound {len(artist_rows)} MusicArtist row(s) in BaseItems:")
for r in artist_rows:
    print(f"  • ID: {r[0]} | Name: '{r[1]}'")

# 2. Check all Audio tracks in BaseItems with Stars of the Lid
cur.execute("""
SELECT Id, Name, Path, Artists, AlbumArtists
FROM BaseItems 
WHERE (type = 'MediaBrowser.Controller.Entities.Audio.Audio' OR type LIKE '%Audio%')
  AND (lower(Artists) LIKE '%stars of the lid%' OR lower(AlbumArtists) LIKE '%stars of the lid%');
""")
track_rows = cur.fetchall()
print(f"\nFound {len(track_rows)} Audio track(s) matching Stars of the Lid:")
artist_tag_counts = {}
for tr in track_rows:
    art = tr[3]
    artist_tag_counts[art] = artist_tag_counts.get(art, 0) + 1

for tag, cnt in artist_tag_counts.items():
    print(f"  • Artists: '{tag}' -> {cnt} tracks")

# 3. Check MusicAlbum rows
cur.execute("""
SELECT Id, Name, Path, Artists, AlbumArtists
FROM BaseItems 
WHERE type LIKE '%MusicAlbum%'
  AND (lower(Artists) LIKE '%stars of the lid%' OR lower(AlbumArtists) LIKE '%stars of the lid%');
""")
album_rows = cur.fetchall()
print(f"\nFound {len(album_rows)} MusicAlbum row(s):")
for al in album_rows:
    print(f"  • Album: '{al[1]}' | Artists: '{al[3]}' | AlbumArtists: '{al[4]}' | Path: '{al[2]}'")

conn.close()
