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

paths = [
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/03 - 03 - - Septet in E-Flat Major_ Op. 20- III. Tempo di menuetto.mp3",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/05_ - _Deeparture_Lounge.ogg",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/A - a - Monochrome (Eurofen Dub).mp3"
]

print("Checking exact BaseItems row for Ambient Rarities tracks:")
for p in paths:
    cur.execute("SELECT Id, Name, Path, Artists, AlbumArtists, DateModified FROM BaseItems WHERE Path = ?;", (p,))
    row = cur.fetchone()
    print("\nPath:", p)
    if row:
        print(f"  ID: {row[0]}")
        print(f"  Name: {row[1]}")
        print(f"  Artists: {row[3]}")
        print(f"  AlbumArtists: {row[4]}")
        print(f"  DateModified: {row[5]}")
    else:
        print("  NOT FOUND by exact path. Searching by filename...")
        cur.execute("SELECT Id, Name, Path, Artists, AlbumArtists, DateModified FROM BaseItems WHERE Path LIKE ?;", (f"%{os.path.basename(p)}%",))
        for r in cur.fetchall():
            print(f"  Found: ID={r[0]}, Path={r[2]}, Artists={r[3]}")

conn.close()
