import os
import re
import sqlite3
import unicodedata

LIBRARIES = [
    "Ambient Classical & Jazz",
    "Electronic",
    "Metal Industrial",
    "Reggae & World",
    "Rock & Pop",
    "Soundtracks & Holiday"
]

def normalize_name(s):
    if not s:
        return ""
    # Normalize unicode
    s = unicodedata.normalize('NFKD', s)
    s = re.sub(r'[\u0300-\u036f]', '', s)
    # Remove leading articles for matching
    s = re.sub(r'^(the|a|an)\s+', '', s.strip(), flags=re.IGNORECASE)
    # Lowercase and strip punctuation
    s = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    return s

def extract_year_from_album_name(album_name):
    # Matches (2023) Album, [2023] Album, 2023 - Album, or Album (2023)
    m = re.search(r'\b(19\d\d|20\d\d)\b', album_name)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None

class LibraryInspector:
    def __init__(self, root_dirs=None, jellyfin_db_path=None):
        self.root_dirs = root_dirs or []
        self.jellyfin_db_path = jellyfin_db_path

    def inspect_artist(self, artist_name):
        """
        Returns {
            'artist': artist_name,
            'owned_albums': [{'title': '...', 'year': 2023, 'path': '...'}],
            'latest_year': 2023,
            'source': 'filesystem' | 'jellyfin_db' | 'none'
        }
        """
        # Try Jellyfin DB first if file exists
        if self.jellyfin_db_path and os.path.exists(self.jellyfin_db_path):
            result = self._inspect_via_db(artist_name)
            if result and result.get('owned_albums'):
                return result

        # Fallback to filesystem search
        return self._inspect_via_filesystem(artist_name)

    def _inspect_via_db(self, artist_name):
        owned = []
        norm_target = normalize_name(artist_name)
        try:
            conn = sqlite3.connect(self.jellyfin_db_path)
            cur = conn.cursor()
            # In Jellyfin BaseItems, music albums are type 'MediaBrowser.Controller.Entities.Audio.MusicAlbum'
            cur.execute("""
            SELECT Name, ProductionYear, Path, Artists, AlbumArtists 
            FROM BaseItems 
            WHERE type LIKE '%MusicAlbum%'
            """)
            rows = cur.fetchall()
            conn.close()

            for name, year, path, artists, album_artists in rows:
                candidates = f"{artists or ''} {album_artists or ''}"
                if norm_target in normalize_name(candidates):
                    y = int(year) if year and str(year).isdigit() else extract_year_from_album_name(name or "")
                    owned.append({
                        "title": name or os.path.basename(path or ""),
                        "year": y,
                        "path": path or ""
                    })
        except Exception as e:
            # Fallback to filesystem
            pass

        years = [a['year'] for a in owned if a['year']]
        latest_year = max(years) if years else None
        return {
            'artist': artist_name,
            'owned_albums': owned,
            'latest_year': latest_year,
            'source': 'jellyfin_db' if owned else 'none'
        }

    def _inspect_via_filesystem(self, artist_name):
        owned = []
        norm_target = normalize_name(artist_name)

        for root in self.root_dirs:
            if not os.path.exists(root):
                continue

            for lib in LIBRARIES:
                lib_path = os.path.join(root, lib)
                if not os.path.isdir(lib_path):
                    continue

                try:
                    for artist_folder in os.listdir(lib_path):
                        if normalize_name(artist_folder) == norm_target:
                            artist_full_path = os.path.join(lib_path, artist_folder)
                            if os.path.isdir(artist_full_path):
                                for album_item in os.listdir(artist_full_path):
                                    album_path = os.path.join(artist_full_path, album_item)
                                    if os.path.isdir(album_path):
                                        year = extract_year_from_album_name(album_item)
                                        owned.append({
                                            "title": album_item,
                                            "year": year,
                                            "path": album_path
                                        })
                except Exception:
                    continue

        years = [a['year'] for a in owned if a['year']]
        latest_year = max(years) if years else None

        return {
            'artist': artist_name,
            'owned_albums': owned,
            'latest_year': latest_year,
            'source': 'filesystem' if owned else 'none'
        }
