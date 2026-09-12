import os
import sys
import json
import logging
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playback_tracker import PlaybackTracker
from library_inspector import LibraryInspector
from bandcamp_client import BandcampClient
from notifier import NotificationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("JellyfinBandcampListener")

def load_config(config_path="config.json"):
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse {config_path}: {e}")
    return {}

HTML_CONFIRMATION_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #121212;
            color: #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 80vh;
            margin: 0;
            padding: 20px;
        }}
        .card {{
            background: #1e1e1e;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 30px;
            max-width: 450px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        h2 {{ color: #4ade80; margin-top: 0; }}
        p {{ line-height: 1.6; font-size: 16px; }}
        .badge {{
            display: inline-block;
            background: #2a2a2a;
            color: #fff;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: bold;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h2>{heading}</h2>
        <div class="badge">{item}</div>
        <p>{message}</p>
    </div>
</body>
</html>
"""

class WebhookHandler(BaseHTTPRequestHandler):
    tracker = None
    library = None
    bandcamp = None
    notifier = None
    config = None

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path in ("/health", "/status", "/"):
            status_data = {
                "status": "healthy",
                "service": "Jellyfin Bandcamp Release Watcher",
                "port": self.config.get("server", {}).get("port", 5055)
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        # Ignore Artist endpoint (Temporary Mute, default 180 days / ~6 months)
        if path == "/ignore_artist":
            artist = params.get("artist", [""])[0]
            if not artist:
                self._set_headers(400, "text/html")
                self.wfile.write(b"Missing artist parameter.")
                return
            
            raw_days = params.get("days", [None])[0]
            default_days = self.config.get("tracking", {}).get("artist_mute_days", 180) if self.config else 180
            try:
                mute_days = int(raw_days) if raw_days is not None else default_days
            except ValueError:
                mute_days = default_days

            self.tracker.ignore_artist(artist, mute_days=mute_days)
            duration_desc = f"{mute_days} days (~6 months)" if mute_days == 180 else (f"{mute_days} days" if mute_days else "indefinitely")
            logger.info(f"🚫 [Mute] Artist '{artist}' has been muted for {duration_desc}.")
            html_out = HTML_CONFIRMATION_TEMPLATE.format(
                title="Artist Muted",
                heading="🚫 Artist Muted",
                item=artist,
                message=f"Bandcamp notifications for <b>{artist}</b> have been paused for <b>{duration_desc}</b>."
            )
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(html_out.encode("utf-8"))
            return

        # Unignore Artist endpoint
        if path == "/unignore_artist":
            artist = params.get("artist", [""])[0]
            if artist:
                self.tracker.unignore_artist(artist)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "unmuted", "artist": artist}).encode("utf-8"))
            return

        # Ignore Release endpoint
        if path == "/ignore_release":
            artist = params.get("artist", [""])[0]
            release = params.get("release", [""])[0]
            if not artist or not release:
                self._set_headers(400, "text/html")
                self.wfile.write(b"Missing artist or release parameter.")
                return
            self.tracker.ignore_release(artist, release)
            logger.info(f"🚫 [Ignore] Release '{release}' by '{artist}' has been ignored.")
            html_out = HTML_CONFIRMATION_TEMPLATE.format(
                title="Release Ignored",
                heading="🚫 Release Ignored",
                item=f"{artist} — {release}",
                message=f"You will no longer be alerted about <b>{release}</b>."
            )
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(html_out.encode("utf-8"))
            return

        # List Ignored endpoint
        if path == "/ignored":
            data = {
                "ignored_artists": self.tracker.get_ignored_artists(),
                "ignored_releases": self.tracker.get_ignored_releases()
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="replace")

        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        # POST /ignore_artist
        if path == "/ignore_artist":
            artist = payload.get("artist") or params.get("artist", [""])[0]
            if artist:
                raw_days = payload.get("days") or params.get("days", [None])[0]
                default_days = self.config.get("tracking", {}).get("artist_mute_days", 180) if self.config else 180
                try:
                    mute_days = int(raw_days) if raw_days is not None else default_days
                except ValueError:
                    mute_days = default_days

                self.tracker.ignore_artist(artist, mute_days=mute_days)
                logger.info(f"🚫 [Mute] Artist '{artist}' has been muted for {mute_days} days via POST.")
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "muted", "artist": artist, "mute_days": mute_days}).encode("utf-8"))
                return
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "artist required"}).encode("utf-8"))
            return

        # POST /ignore_release
        if path == "/ignore_release":
            artist = payload.get("artist") or params.get("artist", [""])[0]
            release = payload.get("release") or params.get("release", [""])[0]
            if artist and release:
                self.tracker.ignore_release(artist, release)
                logger.info(f"🚫 [Ignore] Release '{release}' by '{artist}' ignored via POST.")
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "ignored", "artist": artist, "release": release}).encode("utf-8"))
                return
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "artist and release required"}).encode("utf-8"))
            return

        # Manual test endpoint
        if path == "/test_artist":
            artist = payload.get("artist")
            if not artist:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "artist required"}).encode("utf-8"))
                return
            result = self.process_artist_trigger(artist, force=True)
            self._set_headers(200)
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        # Handle Jellyfin Webhook
        res = self.handle_jellyfin_event(payload)
        self._set_headers(200)
        self.wfile.write(json.dumps(res).encode("utf-8"))

    def handle_jellyfin_event(self, payload):
        event_type = payload.get("NotificationType") or payload.get("event") or ""
        item_type = payload.get("ItemType") or payload.get("item_type") or ""

        # Filter out video/book items (e.g. Movies, TV Episodes)
        ignored_video_types = ("movie", "episode", "series", "season", "video", "book", "trailer")
        if item_type and any(v in item_type.lower() for v in ignored_video_types):
            return {"status": "ignored", "reason": f"ItemType '{item_type}' is not audio"}

        artist = (
            payload.get("Artist") or
            payload.get("AlbumArtist") or
            payload.get("Artists") or
            payload.get("series") or
            ""
        )

        if isinstance(artist, list):
            artist = artist[0] if artist else ""

        item_obj = payload.get("Item")
        if isinstance(item_obj, dict):
            if not artist:
                artists_list = item_obj.get("Artists") or item_obj.get("AlbumArtists")
                if isinstance(artists_list, list) and artists_list:
                    artist = artists_list[0]
                elif isinstance(artists_list, str):
                    artist = artists_list
            track = item_obj.get("Name")
            album = item_obj.get("Album")
        else:
            track = payload.get("Name") or payload.get("item")
            album = payload.get("Album")

        user = payload.get("NotificationUsername") or payload.get("user")

        if not artist or artist.strip() in ("", "Various Artists"):
            return {"status": "ignored", "reason": "No valid artist found in payload"}

        artist = artist.strip()

        # Check if artist is muted in config.json
        config_ignored = [a.lower() for a in self.config.get("ignored_artists", [])]
        if artist.lower() in config_ignored:
            logger.info(f"🔇 Artist '{artist}' is in config ignored list. Skipping.")
            return {"status": "ignored", "reason": "Artist muted in config"}

        logger.info(f"🎵 Playback detected: Artist='{artist}', Track='{track}', Album='{album}', User='{user}'")

        # 1. Record play in tracker
        tracking_cfg = self.config.get("tracking", {})
        min_plays = tracking_cfg.get("min_plays_per_day", 3)
        window_hours = tracking_cfg.get("window_hours", 24)
        cooldown_days = tracking_cfg.get("cooldown_days", 7)

        track_res = self.tracker.record_play(
            artist=artist,
            album=album,
            track=track,
            user_name=user,
            min_plays=min_plays,
            window_hours=window_hours,
            cooldown_days=cooldown_days
        )

        if track_res.get("is_ignored"):
            logger.info(f"🔇 Artist '{artist}' is muted in database. Skipping.")
            return {"status": "ignored", "reason": "Artist muted in database"}

        logger.info(f"📊 Play count for '{artist}': {track_res['play_count']}/{min_plays} in {window_hours}h window (Cooldown: {track_res['in_cooldown']})")

        # 2. Check if triggered
        if track_res["should_trigger"]:
            logger.info(f"🔥 Threshold reached for '{artist}'! Starting library & Bandcamp analysis in background...")
            threading.Thread(
                target=self.process_artist_trigger,
                args=(artist,),
                daemon=True
            ).start()
            return {"status": "triggered", "artist": artist, "play_count": track_res["play_count"]}

        return {"status": "recorded", "artist": artist, "play_count": track_res["play_count"]}

    def process_artist_trigger(self, artist, force=False):
        try:
            logger.info(f"🔍 Inspecting library for artist '{artist}'...")
            lib_info = self.library.inspect_artist(artist)
            owned_albums = lib_info.get("owned_albums", [])
            latest_year = lib_info.get("latest_year")

            logger.info(f"📁 Owned albums for '{artist}': {len(owned_albums)} (Newest year: {latest_year})")

            # Collect ignored releases for this artist
            db_ignored = self.tracker.get_ignored_releases(artist)
            ignored_titles = [r["release_title"] for r in db_ignored]
            
            # Also merge config-level ignored releases
            cfg_ignored = self.config.get("ignored_releases", {}).get(artist, [])
            all_ignored = list(set(ignored_titles + cfg_ignored))

            # Query Bandcamp
            tracking_cfg = self.config.get("tracking", {})
            notify_mode = tracking_cfg.get("notify_mode", "newer_only")

            logger.info(f"🌐 Querying Bandcamp for '{artist}'...")
            bc_res = self.bandcamp.find_new_releases(
                artist_name=artist,
                owned_albums=owned_albums,
                latest_owned_year=latest_year,
                notify_mode=notify_mode,
                ignored_titles=all_ignored
            )

            status = bc_res.get("status")
            new_releases = bc_res.get("releases", [])
            bc_url = bc_res.get("bandcamp_url")

            if status == "artist_not_found":
                logger.warning(f"⚠️ Bandcamp page not found for '{artist}'")
                return {"status": "artist_not_found", "artist": artist}

            if not new_releases:
                logger.info(f"✅ No new unowned releases found for '{artist}' (already up-to-date or ignored).")
                self.tracker.mark_checked_without_notification(artist)
                return {"status": "up_to_date", "artist": artist, "bandcamp_url": bc_url}

            logger.info(f"🎉 FOUND {len(new_releases)} NEW RELEASE(S) FOR '{artist}'!")
            for r in new_releases:
                logger.info(f"   - {r.get('title')} ({r.get('date_published', r.get('year'))}) -> {r.get('url')}")

            # Callback URL for action buttons (Ignore Release / Mute Artist)
            callback_url = self.config.get("server", {}).get("callback_url")

            # Dispatch notifications
            dispatch_results = self.notifier.dispatch(
                artist,
                new_releases,
                bandcamp_url=bc_url,
                callback_url=callback_url
            )
            logger.info(f"📬 Notification dispatch results: {dispatch_results}")

            # Update tracker cooldown
            self.tracker.mark_notified(artist, new_releases)

            return {
                "status": "notified",
                "artist": artist,
                "bandcamp_url": bc_url,
                "releases_found": len(new_releases),
                "releases": new_releases,
                "dispatch": dispatch_results
            }
        except Exception as e:
            logger.error(f"❌ Error processing trigger for '{artist}': {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

def run_server(config_path="config.json"):
    config = load_config(config_path)
    server_cfg = config.get("server", {})
    host = server_cfg.get("host", "0.0.0.0")
    port = int(server_cfg.get("port", 5055))

    tracker = PlaybackTracker(db_path="media_tracker.db")
    library = LibraryInspector(
        root_dirs=config.get("library", {}).get("root_dirs", []),
        jellyfin_db_path=config.get("library", {}).get("jellyfin_db_path")
    )
    bandcamp = BandcampClient(tracker=tracker)
    notifier = NotificationEngine(config=config)

    # Attach instances to handler class
    WebhookHandler.tracker = tracker
    WebhookHandler.library = library
    WebhookHandler.bandcamp = bandcamp
    WebhookHandler.notifier = notifier
    WebhookHandler.config = config

    server = HTTPServer((host, port), WebhookHandler)
    logger.info(f"🚀 Jellyfin-Bandcamp Webhook Listener active on http://{host}:{port}")
    logger.info(f"   Webhook Endpoint: http://<server-ip>:{port}/webhook")
    logger.info(f"   Health Check:     http://<server-ip>:{port}/health")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        server.server_close()

if __name__ == "__main__":
    cfg_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    run_server(cfg_file)
