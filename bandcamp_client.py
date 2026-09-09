import urllib.request
import urllib.parse
import urllib.error
import re
import json
import html
import unicodedata
import datetime

import difflib

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '', text)

def parse_release_year(date_str):
    if not date_str:
        return None
    # Matches "27 Jun 2025" or "2025-06-27"
    m = re.search(r'\b(19\d\d|20\d\d)\b', str(date_str))
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None

def normalize_title(title):
    if not title:
        return ""
    title = unicodedata.normalize('NFKD', title)
    title = re.sub(r'[\u0300-\u036f]', '', title)
    title = re.sub(r'\b(19\d\d|20\d\d)\b', '', title)
    title = re.sub(r'[\(\)\[\]\{\}\-_:;!?,."\']', '', title)
    return title.strip().lower()

def is_album_match(t1, t2):
    n1 = normalize_title(t1)
    n2 = normalize_title(t2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    special = {'ii', 'iii', 'iv', '2', '3', 'live', 'remix', 'remixes', 'deluxe', 'instrumental', 'dub', 'acoustic', 'part', 'ep'}
    w1, w2 = set(n1.split()), set(n2.split())
    if (w1 - w2) & special or (w2 - w1) & special:
        return False
    return difflib.SequenceMatcher(None, n1, n2).ratio() >= 0.92

class BandcampClient:
    def __init__(self, tracker=None):
        self.tracker = tracker

    def _fetch_url(self, url, timeout=10):
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return resp.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            if e.code != 404:
                # Log non-404 errors if needed
                pass
        except Exception:
            pass
        return None

    def resolve_artist_url(self, artist_name):
        """
        Attempts to resolve an artist name to their Bandcamp base URL.
        First checks tracker DB cache, then tries intelligent slug patterns.
        """
        if self.tracker:
            cached_url = self.tracker.get_bandcamp_url(artist_name)
            if cached_url:
                return cached_url

        slug = slugify(artist_name)
        if not slug:
            return None

        # Generate candidate subdomains
        candidates = [slug]
        # If starts with 'the', also try without 'the' and vice versa
        if slug.startswith('the') and len(slug) > 3:
            candidates.append(slug[3:])
        else:
            candidates.append(f"the{slug}")

        candidates.append(f"{slug}music")
        candidates.append(f"{slug}official")
        candidates.append(f"{slug}band")

        for cand in candidates:
            test_url = f"https://{cand}.bandcamp.com"
            music_page = f"{test_url}/music"
            html_content = self._fetch_url(music_page, timeout=6)
            if html_content:
                if self.tracker:
                    self.tracker.save_bandcamp_url(artist_name, test_url)
                return test_url

        return None

    def get_discography(self, base_url, max_details=10):
        """
        Scrapes releases from the artist's Bandcamp /music page.
        Fetches individual release pages to extract rich JSON-LD details.
        """
        music_url = f"{base_url.rstrip('/')}/music"
        html_content = self._fetch_url(music_url)
        if not html_content:
            return []

        # Find items in music-grid or release lists
        # Extracts: data-item-id, href, and title
        pattern = re.compile(
            r'<li[^>]+data-item-id=[\'"]([^\'"]+)[\'"][^>]*>.*?<a href=[\'"]([^\'"]+)[\'"].*?<p class=[\'"]title[\'"]>\s*(.*?)\s*</p>',
            re.DOTALL
        )
        matches = pattern.findall(html_content)

        # Fallback if page is a single album page directly
        if not matches and ('class="trackView"' in html_content or 'application/ld+json' in html_content):
            album_detail = self._parse_album_page(base_url)
            return [album_detail] if album_detail else []

        releases = []
        for item_id, rel_href, raw_title in matches:
            # Clean title (remove nested span tags like artist override)
            cleaned_title = re.sub(r'<[^>]+>', '', raw_title).strip()
            cleaned_title = html.unescape(cleaned_title)

            # Build full URL
            if rel_href.startswith('http'):
                full_url = rel_href
            else:
                full_url = f"{base_url.rstrip('/')}{rel_href}"

            releases.append({
                "item_id": item_id,
                "title": cleaned_title,
                "url": full_url
            })

        # Fetch detailed metadata (dates, artwork) for the most recent releases
        detailed_releases = []
        for rel in releases[:max_details]:
            detail = self._parse_album_page(rel["url"])
            if detail:
                # Merge and keep best title
                detail["item_id"] = rel.get("item_id")
                detailed_releases.append(detail)
            else:
                detailed_releases.append({
                    "title": rel["title"],
                    "url": rel["url"],
                    "year": None,
                    "date_published": None,
                    "cover_art": None,
                    "artist": None
                })

        return detailed_releases

    def _parse_album_page(self, album_url):
        html_content = self._fetch_url(album_url)
        if not html_content:
            return None

        # Look for application/ld+json script tag
        ld_match = re.search(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', html_content, re.DOTALL)
        if ld_match:
            try:
                data = json.loads(ld_match.group(1))
                pub_date = data.get('datePublished')
                year = parse_release_year(pub_date)
                cover = data.get('image')
                artist_data = data.get('byArtist', {})
                artist_name = artist_data.get('name') if isinstance(artist_data, dict) else None

                return {
                    "title": html.unescape(data.get('name', '')),
                    "url": album_url,
                    "year": year,
                    "date_published": pub_date,
                    "cover_art": cover,
                    "artist": artist_name,
                    "description": data.get('description', '')[:300] if data.get('description') else None
                }
            except Exception:
                pass

        # Fallback meta tags if ld+json not found
        title_m = re.search(r'<meta property=[\'"]og:title[\'"] content=[\'"]([^\'"]+)[\'"]', html_content)
        title = html.unescape(title_m.group(1)) if title_m else ""
        img_m = re.search(r'<meta property=[\'"]og:image[\'"] content=[\'"]([^\'"]+)[\'"]', html_content)
        img = img_m.group(1) if img_m else None

        return {
            "title": title,
            "url": album_url,
            "year": None,
            "date_published": None,
            "cover_art": img,
            "artist": None
        }

    def find_new_releases(self, artist_name, owned_albums=None, latest_owned_year=None, notify_mode="newer_only", ignored_titles=None):
        """
        Checks Bandcamp discography against user's owned albums and ignored titles.
        Returns list of new releases to notify about.
        """
        base_url = self.resolve_artist_url(artist_name)
        if not base_url:
            return {"status": "artist_not_found", "artist": artist_name, "releases": []}

        discography = self.get_discography(base_url)
        if not discography:
            return {"status": "no_releases_found", "artist": artist_name, "bandcamp_url": base_url, "releases": []}

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
            "bandcamp_url": base_url,
            "latest_owned_year": latest_owned_year,
            "releases": new_candidates
        }
