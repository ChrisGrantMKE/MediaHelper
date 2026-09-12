import os
import sys
import json
import argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playback_tracker import PlaybackTracker
from library_inspector import LibraryInspector
from bandcamp_client import BandcampClient
from notifier import NotificationEngine

def load_config(config_path="config.json"):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def test_bandcamp(artist_name, config):
    print(f"\n=======================================================")
    print(f"🎵 Testing Bandcamp Scraping for: '{artist_name}'")
    print(f"=======================================================")
    tracker = PlaybackTracker("media_tracker.db")
    bc = BandcampClient(tracker=tracker)
    
    url = bc.resolve_artist_url(artist_name)
    print(f"🌐 Resolved Bandcamp URL: {url}")
    if not url:
        print("❌ Could not resolve Bandcamp URL automatically.")
        return

    print("📥 Fetching discography...")
    discography = bc.get_discography(url)
    print(f"Found {len(discography)} releases:")
    for r in discography[:8]:
        date = r.get('date_published') or (str(r.get('year')) if r.get('year') else "No date")
        print(f"  • {r.get('title')} ({date}) -> {r.get('url')}")

def test_library(artist_name, config):
    print(f"\n=======================================================")
    print(f"📁 Testing Library Inspector for: '{artist_name}'")
    print(f"=======================================================")
    lib = LibraryInspector(
        root_dirs=config.get("library", {}).get("root_dirs", []),
        jellyfin_db_path=config.get("library", {}).get("jellyfin_db_path")
    )
    res = lib.inspect_artist(artist_name)
    print(f"Source: {res.get('source')}")
    print(f"Owned Albums Count: {len(res.get('owned_albums', []))}")
    print(f"Latest Release Year: {res.get('latest_year')}")
    for a in res.get('owned_albums', [])[:10]:
        print(f"  • {a.get('title')} ({a.get('year')})")

def simulate_plays(artist_name, count, config):
    print(f"\n=======================================================")
    print(f"▶️ Simulating {count} Play(s) for: '{artist_name}'")
    print(f"=======================================================")
    tracker = PlaybackTracker("media_tracker.db")
    lib = LibraryInspector(
        root_dirs=config.get("library", {}).get("root_dirs", []),
        jellyfin_db_path=config.get("library", {}).get("jellyfin_db_path")
    )
    bc = BandcampClient(tracker=tracker)
    notifier = NotificationEngine(config=config)

    min_plays = config.get("tracking", {}).get("min_plays_per_day", 3)
    notify_mode = config.get("tracking", {}).get("notify_mode", "newer_only")

    for i in range(1, count + 1):
        res = tracker.record_play(
            artist=artist_name,
            album="Simulated Album",
            track=f"Simulated Track {i}",
            user_name="Chris",
            min_plays=min_plays
        )
        print(f"Play #{i}: Count = {res['play_count']}/{min_plays} | Trigger? {res['should_trigger']} | Cooldown? {res['in_cooldown']}")

        if res["should_trigger"]:
            print(f"\n🔥 THRESHOLD REACHED! Running discovery pipeline...")
            lib_info = lib.inspect_artist(artist_name)
            owned = lib_info.get("owned_albums", [])
            latest_year = lib_info.get("latest_year")
            print(f"📁 Owned albums: {len(owned)}, Newest year: {latest_year}")

            bc_res = bc.find_new_releases(
                artist_name=artist_name,
                owned_albums=owned,
                latest_owned_year=latest_year,
                notify_mode=notify_mode,
                notified_titles=res.get("notified_releases", [])
            )

            new_rels = bc_res.get("releases", [])
            print(f"🌐 Bandcamp Status: {bc_res.get('status')}")
            print(f"🎉 New Releases Found: {len(new_rels)}")
            for r in new_rels:
                print(f"   - {r.get('title')} ({r.get('date_published') or r.get('year')}) -> {r.get('url')}")

            if new_rels:
                dispatch = notifier.dispatch(artist_name, new_rels, bandcamp_url=bc_res.get("bandcamp_url"))
                print(f"📬 Dispatched: {dispatch}")
                tracker.mark_notified(artist_name, new_rels)
            else:
                tracker.mark_checked_without_notification(artist_name)

def show_status():
    print(f"\n=======================================================")
    print(f"📊 Media Tracker Status & Cache")
    print(f"=======================================================")
    tracker = PlaybackTracker("media_tracker.db")
    with tracker._get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM play_events")
        total_plays = cur.fetchone()[0]
        print(f"Total Logged Plays: {total_plays}")

        cur.execute("SELECT artist, last_notified_at, notified_releases FROM artist_notifications")
        rows = cur.fetchall()
        print(f"\nTracked Artists with Notifications ({len(rows)}):")
        for artist, last_notified, releases in rows:
            print(f"  • {artist} | Last Notified: {last_notified} | Releases: {releases}")

        cur.execute("SELECT artist, bandcamp_url FROM artist_bandcamp_map")
        rows = cur.fetchall()
        print(f"\nCached Bandcamp URLs ({len(rows)}):")
        for artist, url in rows:
            print(f"  • {artist} -> {url}")

    list_ignored()

def list_ignored():
    tracker = PlaybackTracker("media_tracker.db")
    print(f"\n=======================================================")
    print(f"🚫 Muted Artists & Ignored Releases")
    print(f"=======================================================")
    artists = tracker.get_ignored_artists()
    print(f"Muted Artists ({len(artists)}):")
    for a in artists:
        until_str = f" | Muted until: {a['mute_until']}" if a.get('mute_until') else " | Indefinite"
        print(f"  • {a['artist']} (since {a['created_at']}{until_str})")

    releases = tracker.get_ignored_releases()
    print(f"\nIgnored Releases ({len(releases)}):")
    for r in releases:
        print(f"  • {r['artist']} — {r['release_title']} (since {r['created_at']})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediaHelper Bandcamp Tracker Test Utility")
    parser.add_argument("--test-bandcamp", type=str, help="Test Bandcamp search and scraping for artist")
    parser.add_argument("--test-library", type=str, help="Test owned albums and latest release year for artist")
    parser.add_argument("--simulate-plays", type=str, help="Simulate plays for artist")
    parser.add_argument("--count", type=int, default=3, help="Number of plays to simulate (default 3)")
    parser.add_argument("--status", action="store_true", help="Show database tracker status")
    parser.add_argument("--ignore-artist", type=str, help="Permanently mute an artist from notifications")
    parser.add_argument("--unignore-artist", type=str, help="Unmute an artist")
    parser.add_argument("--ignore-release", nargs=2, metavar=("ARTIST", "RELEASE"), help="Ignore a specific release")
    parser.add_argument("--unignore-release", nargs=2, metavar=("ARTIST", "RELEASE"), help="Unignore a specific release")
    parser.add_argument("--list-ignored", action="store_true", help="List all muted artists and ignored releases")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")

    args = parser.parse_args()
    config = load_config(args.config)
    tracker = PlaybackTracker("media_tracker.db")

    if args.ignore_artist:
        tracker.ignore_artist(args.ignore_artist)
        print(f"🚫 Artist '{args.ignore_artist}' is now muted.")
    elif args.unignore_artist:
        tracker.unignore_artist(args.unignore_artist)
        print(f"✅ Artist '{args.unignore_artist}' is now unmuted.")
    elif args.ignore_release:
        artist, release = args.ignore_release
        tracker.ignore_release(artist, release)
        print(f"🚫 Release '{release}' by '{artist}' is now ignored.")
    elif args.unignore_release:
        artist, release = args.unignore_release
        tracker.unignore_release(artist, release)
        print(f"✅ Release '{release}' by '{artist}' is now unignored.")
    elif args.list_ignored:
        list_ignored()
    elif args.test_bandcamp:
        test_bandcamp(args.test_bandcamp, config)
    elif args.test_library:
        test_library(args.test_library, config)
    elif args.simulate_plays:
        simulate_plays(args.simulate_plays, args.count, config)
    elif args.status:
        show_status()
    else:
        parser.print_help()
