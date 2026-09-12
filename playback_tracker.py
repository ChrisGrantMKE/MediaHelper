import sqlite3
import os
import json
import datetime
import unicodedata
import re

def normalize_text(s):
    if not s:
        return ""
    s = unicodedata.normalize('NFKD', s)
    s = re.sub(r'[\u0300-\u036f]', '', s)
    return s.strip().lower()

class PlaybackTracker:
    def __init__(self, db_path="media_tracker.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS play_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist TEXT NOT NULL,
                album TEXT,
                track TEXT,
                user_name TEXT,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_play_events_artist_time 
            ON play_events (artist, played_at);
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS artist_notifications (
                artist TEXT PRIMARY KEY,
                last_checked_at TIMESTAMP,
                last_notified_at TIMESTAMP,
                notified_releases TEXT
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS artist_bandcamp_map (
                artist TEXT PRIMARY KEY,
                bandcamp_url TEXT NOT NULL,
                verified INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ignored_artists (
                artist TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mute_until TIMESTAMP
            );
            """)
            # Ensure mute_until column exists if table was created in an earlier schema
            try:
                cur.execute("ALTER TABLE ignored_artists ADD COLUMN mute_until TIMESTAMP;")
            except Exception:
                pass

            cur.execute("""
            CREATE TABLE IF NOT EXISTS ignored_releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist TEXT NOT NULL,
                release_title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(artist, release_title)
            );
            """)
            conn.commit()

    def ignore_artist(self, artist, mute_days=180):
        """
        Mutes an artist for a configurable duration (default: 180 days / ~6 months).
        If mute_days is None or 0, mutes indefinitely.
        """
        artist_clean = artist.strip()
        now = datetime.datetime.now()
        mute_until = (now + datetime.timedelta(days=mute_days)).strftime("%Y-%m-%d %H:%M:%S") if mute_days else None
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO ignored_artists (artist, created_at, mute_until) 
            VALUES (?, ?, ?)
            ON CONFLICT(artist) DO UPDATE SET 
                created_at = excluded.created_at,
                mute_until = excluded.mute_until
            """, (artist_clean, now_str, mute_until))
            conn.commit()
        return True

    def unignore_artist(self, artist):
        artist_clean = artist.strip()
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM ignored_artists WHERE lower(artist) = lower(?)", (artist_clean,))
            conn.commit()
        return True

    def is_artist_ignored(self, artist):
        norm = normalize_text(artist)
        now = datetime.datetime.now()
        expired_to_clean = []

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT artist, mute_until FROM ignored_artists")
            rows = cur.fetchall()
            for r in rows:
                row_artist, mute_until_str = r[0], r[1]
                if normalize_text(row_artist) == norm:
                    if mute_until_str:
                        try:
                            mute_until = datetime.datetime.fromisoformat(mute_until_str.replace("Z", ""))
                            if now > mute_until:
                                expired_to_clean.append(row_artist)
                                continue
                        except Exception:
                            pass
                    return True

            if expired_to_clean:
                for exp in expired_to_clean:
                    cur.execute("DELETE FROM ignored_artists WHERE artist = ?", (exp,))
                conn.commit()

        return False

    def get_ignored_artists(self):
        now = datetime.datetime.now()
        expired_to_clean = []
        active_ignored = []

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT artist, created_at, mute_until FROM ignored_artists ORDER BY artist")
            rows = cur.fetchall()
            for r in rows:
                artist_name, created_at, mute_until_str = r[0], r[1], r[2]
                is_expired = False
                if mute_until_str:
                    try:
                        mute_until = datetime.datetime.fromisoformat(mute_until_str.replace("Z", ""))
                        if now > mute_until:
                            is_expired = True
                            expired_to_clean.append(artist_name)
                    except Exception:
                        pass
                if not is_expired:
                    active_ignored.append({
                        "artist": artist_name,
                        "created_at": created_at,
                        "mute_until": mute_until_str
                    })

            if expired_to_clean:
                for exp in expired_to_clean:
                    cur.execute("DELETE FROM ignored_artists WHERE artist = ?", (exp,))
                conn.commit()

        return active_ignored

    def ignore_release(self, artist, release_title):
        artist_clean = artist.strip()
        title_clean = release_title.strip()
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR IGNORE INTO ignored_releases (artist, release_title) VALUES (?, ?)
            """, (artist_clean, title_clean))
            conn.commit()
        return True

    def unignore_release(self, artist, release_title):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            DELETE FROM ignored_releases WHERE lower(artist) = lower(?) AND lower(release_title) = lower(?)
            """, (artist.strip(), release_title.strip()))
            conn.commit()
        return True

    def get_ignored_releases(self, artist=None):
        with self._get_conn() as conn:
            cur = conn.cursor()
            if artist:
                cur.execute("SELECT artist, release_title, created_at FROM ignored_releases WHERE lower(artist) = lower(?)", (artist.strip(),))
            else:
                cur.execute("SELECT artist, release_title, created_at FROM ignored_releases ORDER BY artist, release_title")
            return [{"artist": r[0], "release_title": r[1], "created_at": r[2]} for r in cur.fetchall()]

    def record_play(self, artist, album=None, track=None, user_name=None, min_plays=3, window_hours=24, cooldown_days=7):
        """
        Records a track play.
        Returns a dict indicating if the artist reached the threshold to trigger a release scan.
        """
        artist_clean = artist.strip()
        now = datetime.datetime.now()
        window_start = now - datetime.timedelta(hours=window_hours)
        cooldown_start = now - datetime.timedelta(days=cooldown_days)

        # Check if artist is explicitly ignored
        if self.is_artist_ignored(artist_clean):
            return {
                "artist": artist_clean,
                "play_count": 0,
                "threshold": min_plays,
                "window_hours": window_hours,
                "in_cooldown": False,
                "is_ignored": True,
                "last_notified": None,
                "notified_releases": [],
                "should_trigger": False
            }

        with self._get_conn() as conn:
            cur = conn.cursor()
            # 1. Insert play event
            cur.execute(
                "INSERT INTO play_events (artist, album, track, user_name, played_at) VALUES (?, ?, ?, ?, ?)",
                (artist_clean, album or "", track or "", user_name or "", now.strftime("%Y-%m-%d %H:%M:%S"))
            )
            
            # 2. Count plays in rolling window
            cur.execute(
                "SELECT COUNT(*) FROM play_events WHERE artist = ? AND played_at >= ?",
                (artist_clean, window_start.strftime("%Y-%m-%d %H:%M:%S"))
            )
            play_count = cur.fetchone()[0]

            # 3. Check cooldown status
            cur.execute(
                "SELECT last_notified_at, notified_releases FROM artist_notifications WHERE artist = ?",
                (artist_clean,)
            )
            row = cur.fetchone()
            in_cooldown = False
            last_notified = None
            notified_releases = []

            if row:
                last_notified_str, notified_json = row
                if last_notified_str:
                    try:
                        last_notified = datetime.datetime.strptime(last_notified_str, "%Y-%m-%d %H:%M:%S")
                        if last_notified > cooldown_start:
                            in_cooldown = True
                    except Exception:
                        pass
                if notified_json:
                    try:
                        notified_releases = json.loads(notified_json)
                    except Exception:
                        pass

            # Trigger condition: reached threshold and not currently in cooldown
            should_trigger = (play_count >= min_plays) and not in_cooldown

            conn.commit()

        return {
            "artist": artist_clean,
            "play_count": play_count,
            "threshold": min_plays,
            "window_hours": window_hours,
            "in_cooldown": in_cooldown,
            "is_ignored": False,
            "last_notified": last_notified.strftime("%Y-%m-%d %H:%M:%S") if last_notified else None,
            "notified_releases": notified_releases,
            "should_trigger": should_trigger
        }

    def mark_notified(self, artist, new_releases_data):
        """
        Updates the cooldown timer and logs the release titles that were notified.
        """
        artist_clean = artist.strip()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT notified_releases FROM artist_notifications WHERE artist = ?",
                (artist_clean,)
            )
            row = cur.fetchone()
            existing = []
            if row and row[0]:
                try:
                    existing = json.loads(row[0])
                except Exception:
                    existing = []

            new_titles = [r.get("title") for r in new_releases_data if r.get("title")]
            combined = list(set(existing + new_titles))

            cur.execute("""
            INSERT INTO artist_notifications (artist, last_checked_at, last_notified_at, notified_releases)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(artist) DO UPDATE SET
                last_checked_at = excluded.last_checked_at,
                last_notified_at = excluded.last_notified_at,
                notified_releases = excluded.notified_releases;
            """, (artist_clean, now_str, now_str, json.dumps(combined)))
            conn.commit()

    def mark_checked_without_notification(self, artist):
        artist_clean = artist.strip()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO artist_notifications (artist, last_checked_at)
            VALUES (?, ?)
            ON CONFLICT(artist) DO UPDATE SET
                last_checked_at = excluded.last_checked_at;
            """, (artist_clean, now_str))
            conn.commit()

    def get_bandcamp_url(self, artist):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT bandcamp_url FROM artist_bandcamp_map WHERE artist = ?", (artist.strip(),))
            row = cur.fetchone()
            return row[0] if row else None

    def save_bandcamp_url(self, artist, url, verified=1):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO artist_bandcamp_map (artist, bandcamp_url, verified, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(artist) DO UPDATE SET
                bandcamp_url = excluded.bandcamp_url,
                verified = excluded.verified,
                updated_at = CURRENT_TIMESTAMP;
            """, (artist.strip(), url.strip(), verified))
            conn.commit()
