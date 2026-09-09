import os
import sys
import re
import argparse
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = r"\\CHRISGRANTS\files\Media\Music Albums"

VALID_NUMERIC_BANDS = {
    "2pac", "10cc", "311", "16 volt", "9 lazy 9", "2 bad mice", "1 giant leap",
    "16 bit lolitas", "16 bit lolita's", "51 days", "2 player", "3 phase", "12 gauge",
    "702", "808 state", "404.zero", "65daysofstatic", "100 gecs", "24kgo1dn",
    "23 skidoo", "4hero", "2 brothers on the 4th floor", "b12", "154", "69", "16b",
    "2350 broadway", "u2", "m83", "blink-182", "sum 41", "30 seconds to mars"
}

BAD_ARTIST_PATTERNS = [
    re.compile(r"^\d{1,3}$"),              # '01', '02', '101', etc.
    re.compile(r"^\d{1,3}_+$"),            # '05_', '06_', '07_'
    re.compile(r"^\[.*\]$"),               # '[notag]', '[bonus Track]'
    re.compile(r"^[A-Za-z]$"),             # Single character 'A', 'B'
]

def is_bad_artist(artist_str):
    if not artist_str:
        return True
    s = artist_str.strip()
    norm = re.sub(r'[^\w\s]', '', s.lower()).strip()
    if norm in VALID_NUMERIC_BANDS or s.lower() in VALID_NUMERIC_BANDS:
        return False
    if norm in ("various artists", "various"):
        return False
    for pat in BAD_ARTIST_PATTERNS:
        if pat.match(s):
            return True
    if s.lower() in ("unknown", "unknown artist", "<unknown>", "<unbekannt>", "no artist"):
        return True
    # Check for vinyl catalog prefixes like "[wag 029] Cobblestone Jazz" or track number prefixes like "205 Pato Banton"
    if s.startswith('[') and ']' in s:
        return True
    if re.match(r'^\d{2,4}\s+[A-Za-z]', s):
        return True
    return False

def resolve_clean_artist(filepath, current_artist, current_albumartist, current_album, current_title):
    fname = os.path.splitext(os.path.basename(filepath))[0]
    parent_dir = os.path.basename(os.path.dirname(filepath))
    grandparent_dir = os.path.basename(os.path.dirname(os.path.dirname(filepath)))

    # 1. Check for vinyl / release catalog prefix e.g. '[wag 029] Cobblestone Jazz - ...'
    m_bracket = re.match(r'^\[[^\]]+\]\s*(.+)$', current_artist)
    if m_bracket:
        extracted = m_bracket.group(1).strip()
        if ' - ' in extracted:
            extracted = extracted.split(' - ')[0].strip()
        return extracted, "Stripped release/catalog bracket prefix"

    # 2. Check for track number prefixed to artist e.g. '205 Pato Banton Feat. ...'
    m_num_prefix = re.match(r'^\d{2,4}\s+([A-Za-z].+)$', current_artist)
    if m_num_prefix:
        return m_num_prefix.group(1).strip(), "Stripped track number prefix from artist"

    # 3. Known Classical Works (e.g. Beethoven Septet movements tagged as 01, 02...)
    full_text = f"{fname} {current_title} {current_album}".lower()
    if "septet in e-flat major" in full_text or "beethoven" in full_text:
        return "Ludwig van Beethoven", "Identified classical composer from work title"

    # 4. Check for artist in bracketed compilation pattern e.g. 'Various Artists - (08) [Delphic] Counterpoint'
    m_brack_art = re.search(r'\[([^\]]+)\]\s*(.+)', fname)
    if m_brack_art:
        cand_art = m_brack_art.group(1).strip()
        if cand_art and not is_bad_artist(cand_art) and len(cand_art) > 1:
            return cand_art, f"Extracted artist '{cand_art}' from filename brackets"

    # 5. Check for artist in title or filename with ' - ' separator
    for source in [fname, current_title]:
        if source and ' - ' in source:
            parts = source.split(' - ')
            cand_left = parts[0].strip()
            cand_clean = re.sub(r'^\d+[\s\.\-_]+', '', cand_left)
            cand_clean = re.sub(r'^[a-d]\d*[\s\.\-_]+', '', cand_clean, flags=re.IGNORECASE).strip()
            if cand_clean and not is_bad_artist(cand_clean) and len(cand_clean) > 2 and cand_clean.lower() != "various artists":
                return cand_clean, f"Extracted artist '{cand_clean}' from '{source}'"

    # 6. Check parent / grandparent directories if not generic
    for folder in [grandparent_dir, parent_dir]:
        folder_lower = folder.lower()
        if folder_lower not in ("compilations", "soundtracks", "soundtracks & holiday", "ambient rarities", "electronic rarities", "industrial rarities", "soundtracks rarities", "[notag]"):
            f_clean = re.sub(r'^\[[^\]]+\]\s*', '', folder)
            # If folder is 'Halo III' inside 'Soundtracks & Holiday', artist is 'Halo'
            if 'halo' in folder_lower:
                return "Halo", "Soundtrack artist inherited as Halo"
            if ' - ' in f_clean:
                f_art = f_clean.split(' - ')[0].strip()
                if f_art and not is_bad_artist(f_art):
                    return f_art, f"Inherited artist from folder structure '{folder}'"
            elif f_clean and not is_bad_artist(f_clean):
                return f_clean, f"Inherited artist from directory name '{folder}'"

    # 7. Fallback to AlbumArtist if valid and not a compilation
    if current_albumartist and not is_bad_artist(current_albumartist):
        if current_albumartist.lower() not in ("various artists", "various") or "compilations" in filepath.lower():
            return current_albumartist, "Inherited valid AlbumArtist tag"

    # 8. Safe Default
    return "Various Artists", "Defaulted to Various Artists"

def read_tags_safe(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    info = {'artist': '', 'albumartist': '', 'album': '', 'title': ''}
    try:
        audio = mutagen.File(filepath, easy=True)
        if audio:
            info['artist'] = audio.get('artist', [''])[0]
            info['albumartist'] = audio.get('albumartist', [''])[0]
            info['album'] = audio.get('album', [''])[0]
            info['title'] = audio.get('title', [''])[0]
    except Exception:
        pass
    return info

def write_artist_tag(filepath, new_artist):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.mp3':
            try: audio = EasyID3(filepath)
            except mutagen.id3.ID3NoHeaderError:
                audio = mutagen.File(filepath, easy=True)
                audio.add_tags()
            audio['artist'] = new_artist
            audio.save()
        elif ext == '.flac':
            audio = FLAC(filepath)
            audio['artist'] = new_artist
            audio.save()
        elif ext in ('.m4a', '.mp4'):
            audio = MP4(filepath)
            audio.tags['\xa9ART'] = new_artist
            audio.save()
        elif ext == '.ogg':
            audio = OggVorbis(filepath)
            audio['artist'] = new_artist
            audio.save()
        return True
    except Exception as e:
        print(f"    [!] Error writing tags to {filepath}: {e}")
        return False

def scan_and_clean(target_path, dry_run=True):
    print("====================================================================")
    print("           TRACK ARTIST SANITIZATION & CATALOG REPAIR ENGINE         ")
    print("====================================================================")
    print(f"Target Directory : {target_path}")
    print(f"Execution Mode   : {'DRY RUN (Preview Only)' if dry_run else 'LIVE (Writing Changes to Tags)'}\n")

    candidates = []

    for root, dirs, files in os.walk(target_path):
        for f in files:
            if f.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg')):
                fp = os.path.join(root, f)
                info = read_tags_safe(fp)
                art = info['artist']
                if is_bad_artist(art):
                    new_art, reason = resolve_clean_artist(fp, art, info['albumartist'], info['album'], info['title'])
                    candidates.append({
                        'filepath': fp,
                        'filename': f,
                        'old_artist': art,
                        'new_artist': new_art,
                        'reason': reason,
                        'album': info['album'],
                        'title': info['title']
                    })

    print(f"Found {len(candidates)} track(s) with malformed/numbered artist tags.\n")

    for idx, c in enumerate(candidates, start=1):
        rel = c['filepath'].replace(ROOT_DIR, "")
        print(f"[{idx}] {rel}")
        print(f"    Title     : {c['title']}")
        print(f"    Old Artist: '{c['old_artist']}'")
        print(f"    New Artist: '{c['new_artist']}'  <-- ({c['reason']})")
        
        if not dry_run:
            success = write_artist_tag(c['filepath'], c['new_artist'])
            if success:
                print("    Status    : [UPDATED]")
            else:
                print("    Status    : [FAILED]")
        print()

    print("====================================================================")
    print(f"Summary: {len(candidates)} file(s) evaluated.")
    if dry_run and candidates:
        print("To apply these changes, rerun with: --write")
    print("====================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit and repair malformed track-level artist tags.")
    parser.add_argument("--path", default=os.path.join(ROOT_DIR, "Ambient Classical & Jazz"), help="Directory path to scan")
    parser.add_argument("--write", action="store_true", help="Apply tag modifications directly to audio files")
    args = parser.parse_args()

    scan_and_clean(args.path, dry_run=(not args.write))
