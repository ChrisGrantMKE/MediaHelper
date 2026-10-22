import urllib.request
import urllib.parse
import urllib.error
import re
import json
import html
import unicodedata
import datetime
import difflib
import logging

logger = logging.getLogger("DiscogsClient")

from bandcamp_client import normalize_title, is_album_match, parse_release_year

USER_AGENT = "MediaHelperReleaseChecker/1.0"

def clean_discogs_artist_title(title):
    if not title:
        return ""
    # Strips Discogs duplicate suffixes like "Artist (2)", "Band (15)"
    return re.sub(r'\s*\(\d+\)$', '', title).strip()

class DiscogsClient:
    def __init__(self, token=None, user_agent=None, tracker=None):
        self.token = token
        self.user_agent = user_agent or USER_AGENT
        self.tracker = tracker

    def _fetch_api(self, url, timeout=10):
        headers = {
            'User-Agent': self.user_agent
        }
        if self.token:
            headers['Authorization'] = f"Discogs token={self.token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    raw = resp.read().decode('utf-8', errors='replace')
                    return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code not in (404,):
                logger.warning(f"Discogs API HTTP error {e.code} for {url}: {e.reason}")
        except urllib.error.URLError as e:
            logger.warning(f"Discogs API URL error for {url}: {e.reason}")
        except Exception as e:
            logger.warning(f"Discogs API fetch error for {url}: {e}")
        return None

    def resolve_artist(self, artist_name):
        """
        Resolves an artist name to their Discogs artist ID and URL.
        Checks tracker DB cache first, then queries Discogs Search API.
        """
        if self.tracker:
            cached = self.tracker.get_discogs_artist(artist_name)
            if cached:
                return {
                    "artist_id": cached["discogs_id"],
                    "artist_name": artist_name,
                    "discogs_url": cached["discogs_url"]
                }

        q = urllib.parse.quote(artist_name.strip())
        search_url = f"https://api.discogs.com/database/search?q={q}&type=artist"
        data = self._fetch_api(search_url)
        if not data or not data.get("results"):
            return None

        results = data.get("results", [])
        norm_target = normalize_title(artist_name)

        matched = None
        for r in results[:10]:
            title = r.get("title", "")
            clean_title = clean_discogs_artist_title(title)
            if normalize_title(clean_title) == norm_target:
                matched = r
                break

        # Fallback to top result if no exact normalized match
        if not matched and results:
            matched = results[0]

        if not matched:
            return None

        artist_id = matched.get("id")
        discogs_url = f"https://www.discogs.com/artist/{artist_id}"

        if self.tracker and artist_id:
            self.tracker.save_discogs_artist(artist_name, artist_id, discogs_url)

        return {
            "artist_id": artist_id,
            "artist_name": matched.get("title"),
            "discogs_url": discogs_url
        }

    def get_discography(self, artist_id, max_releases=50):
        """
        Fetches artist releases from Discogs, filters for primary/main releases,
        and deduplicates masters vs individual pressings.
        """
        url = f"https://api.discogs.com/artists/{artist_id}/releases?sort=year&sort_order=desc&per_page={max_releases}"
        data = self._fetch_api(url)
        if not data or not data.get("releases"):
            return []

        raw_releases = data.get("releases", [])

        # Step 1: Collect masters and main releases
        # Prefer master records where available to avoid duplicate pressings
        seen_titles = set()
        unique_releases = []

        for r in raw_releases:
            # We only want albums/EPs where the artist is Main (not remix, appearance, producer)
            role = r.get("role", "Main")
            if role != "Main":
                continue

            raw_title = r.get("title", "").strip()
            if not raw_title:
                continue

            norm_t = normalize_title(raw_title)
            if not norm_t or norm_t in seen_titles:
                continue

            seen_titles.add(norm_t)

            rtype = r.get("type", "release")
            rid = r.get("id")
            web_url = f"https://www.discogs.com/{rtype}/{rid}"

            year = r.get("year")
            try:
                year = int(year) if year else None
            except (ValueError, TypeError):
                year = None

            unique_releases.append({
                "id": rid,
                "title": raw_title,
                "url": web_url,
                "year": year,
                "date_published": str(year) if year else None,
                "cover_art": r.get("thumb"),
                "artist": r.get("artist"),
                "type": rtype,
                "source": "discogs"
            })

        return unique_releases

    def find_new_releases(self, artist_name, owned_albums=None, latest_owned_year=None, notify_mode="newer_only", ignored_titles=None):
        """
        Checks Discogs discography against user's owned albums and ignored titles.
        Returns list of new unowned releases.
        """
        artist_info = self.resolve_artist(artist_name)
        if not artist_info:
            return {"status": "artist_not_found", "artist": artist_name, "releases": []}

        artist_id = artist_info["artist_id"]
        discogs_url = artist_info["discogs_url"]

        discography = self.get_discography(artist_id)
        if not discography:
            return {"status": "no_releases_found", "artist": artist_name, "discogs_url": discogs_url, "releases": []}

        new_candidates = []
        current_year = datetime.datetime.now().year

        for release in discography:
            rel_title = release.get("title", "")
            rel_year = release.get("year")

            # Check if owned in user's library
            is_owned = any(is_album_match(rel_title, a.get('title', '')) for a in (owned_albums or []))
            if is_owned:
                continue

            # Check if explicitly ignored by user
            is_ignored = any(is_album_match(rel_title, ign) for ign in (ignored_titles or []))
            if is_ignored:
                continue

            if notify_mode == "newer_only":
                # Alert if release year is >= latest owned year, OR within last 2-3 years and unowned!
                if rel_year and (rel_year >= (latest_owned_year or 0) or rel_year >= (current_year - 2)):
                    new_candidates.append(release)
                elif not rel_year:
                    new_candidates.append(release)
            else:
                # notify_mode == "all_missing"
                new_candidates.append(release)

        return {
            "status": "success",
            "artist": artist_name,
            "discogs_url": discogs_url,
            "discogs_id": artist_id,
            "latest_owned_year": latest_owned_year,
            "releases": new_candidates
        }
