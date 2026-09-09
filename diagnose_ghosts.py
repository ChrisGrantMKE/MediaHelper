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

targets = ['01', '02', '03', '04', '05', '06', '05_', '06_', '07_', '08_', 'A', 'B', 'VA', 'Va']

print("====================================================================")
print("       EXACT AUDIO TRACK INSPECTION FOR NUMBERED/MALFORMED ARTISTS  ")
print("====================================================================")

for t in targets:
    cur.execute("""
    SELECT Id, Name, Path, Artists, AlbumArtists
    FROM BaseItems 
    WHERE (type = 'MediaBrowser.Controller.Entities.Audio.Audio' OR type LIKE '%Audio%')
      AND (
          Artists = ? 
          OR Artists LIKE ? 
          OR Artists LIKE ? 
          OR Artists LIKE ?
          OR AlbumArtists = ?
          OR AlbumArtists LIKE ?
      )
    LIMIT 3;
    """, (t, f"%|{t}|%", f"{t}|%", f"%|{t}", t, f"%{t}%"))
    
    rows = cur.fetchall()
    if rows:
        print(f"\n[!] Target '{t}' IS REFERENCED BY audio item(s) in BaseItems:")
        for r in rows:
            print(f"    • Track Title : {r[1]}")
            print(f"      Disk Path   : {r[2]}")
            print(f"      Artists     : {r[3]}")
            print(f"      AlbumArtists: {r[4]}")
    else:
        print(f"[-] Target '{t}' has NO audio items matching.")

conn.close()
