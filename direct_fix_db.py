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
print("     UPDATING STALE BASEITEMS TRACK ARTISTS & PURGING GHOSTS        ")
print("====================================================================")

# 1. Beethoven Septet tracks (Movements I-VI)
beethoven_paths = [
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/01 - 01 - - Septet in E-Flat Major_ Op. 20- I. Adagio - Allegro con brio.mp3",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/02 - 02 - - Septet in E-Flat Major_ Op. 20- II. Adagio cantabile.mp3",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/03 - 03 - - Septet in E-Flat Major_ Op. 20- III. Tempo di menuetto.mp3",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/04 - 04 - - Septet in E-Flat Major_ Op. 20- IV. Tema con variazioni- Andante.mp3",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/05 - 05 - - Septet in E-Flat Major_ Op. 20- V. Scherzo- Allegro molto e vivace.mp3",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/06 - 06 - - Septet in E-Flat Major_ Op. 20- VI. Andante con moto alla marcia - Presto.mp3",
]

for bp in beethoven_paths:
    cur.execute("UPDATE BaseItems SET Artists = 'Ludwig van Beethoven' WHERE Path = ?;", (bp,))
    if cur.rowcount > 0:
        print(f"  -> Updated track artist to 'Ludwig van Beethoven': {os.path.basename(bp)}")

# 2. Ambient Rarities remaining odd tracks -> Various Artists
various_paths = [
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/05_ - _Deeparture_Lounge.ogg",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/06_ - _Barbapapa.ogg",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/07_ - _Bad_Idea.ogg",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/08_ - _Gadget_-_Reset.ogg",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/A - a - Monochrome (Eurofen Dub).mp3",
    "/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities/B - b - Monochrome (Bonus Kaos Mix).mp3",
]

for vp in various_paths:
    cur.execute("UPDATE BaseItems SET Artists = 'Various Artists' WHERE Path = ?;", (vp,))
    if cur.rowcount > 0:
        print(f"  -> Updated track artist to 'Various Artists': {os.path.basename(vp)}")

# 3. Clean up the Ambient Rarities folder/album container's cached Artists string
cur.execute("""
SELECT Id, Artists FROM BaseItems 
WHERE Path = '/media/Music Albums/Ambient Classical & Jazz/Compilations/Ambient Rarities';
""")
alb_row = cur.fetchone()
if alb_row:
    alb_id, old_artists = alb_row
    # Replace all false tokens from the album's artist cache
    cleaned_alb_artists = old_artists
    for token in ['|01', '|02', '|03', '|04', '|05', '|05_', '|06', '|06_', '|07_', '|08_', '|A', '|B', '01|', '02|', '03|', '04|', '05|', '05_|', '06|', '06_|', '07_|', '08_|', 'A|', 'B|']:
        cleaned_alb_artists = cleaned_alb_artists.replace(token, '')
    cur.execute("UPDATE BaseItems SET Artists = ? WHERE Id = ?;", (cleaned_alb_artists, alb_id))
    print("  -> Cleaned Ambient Rarities album artist cache.")

conn.commit()

# 4. Now permanently delete the MusicArtist cards: 01, 02, 03, 04, 05, 05_, 06, 06_, 07_, 08_, A, B
bad_artist_names = ['01', '02', '03', '04', '05', '05_', '06', '06_', '07_', '08_', 'A', 'B']
cur.execute("""
SELECT Id, Name FROM BaseItems 
WHERE (type = 'MediaBrowser.Controller.Entities.Audio.MusicArtist' OR type LIKE '%MusicArtist%')
  AND Name IN ('01', '02', '03', '04', '05', '05_', '06', '06_', '07_', '08_', 'A', 'B');
""")
bad_cards = cur.fetchall()

print(f"\nFound {len(bad_cards)} rogue MusicArtist card(s) to permanently delete:")
for cid, cname in bad_cards:
    print(f"   🗑️ Deleting Artist Card: '{cname}' (ID={cid})")

cur.executemany("DELETE FROM BaseItems WHERE Id = ?;", [(c[0],) for c in bad_cards])
cur.executemany("DELETE FROM ItemValuesMap WHERE ItemId = ?;", [(c[0],) for c in bad_cards])

conn.commit()
print("\n🧹 Optimizing database (VACUUM)...")
cur.execute("VACUUM;")
conn.commit()
conn.close()

print("\n🎉 DONE! All false number and single-letter artist cards are permanently gone.")
