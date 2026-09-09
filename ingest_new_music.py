import os
import sys
import re
import difflib
import shutil
import subprocess
import unicodedata
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
import mutagen

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = r"\\CHRISGRANTS\files\Media\Music Albums"
INCOMING_DIR = os.path.join(ROOT_DIR, "_INCOMING")

LIBRARIES = [
    "Ambient Classical & Jazz",
    "Electronic",
    "Metal Industrial",
    "Reggae & World",
    "Rock & Pop",
    "Soundtracks & Holiday"
]

GENRE_MAP = {
    # Ambient & Modern Minimalist (High Precedence)
    "dark ambient": "Ambient; Dark Ambient",
    "space ambient": "Ambient; Space Ambient",
    "ambient techno": "Ambient; Atmospheric",
    "ambient dub": "Ambient; Atmospheric",
    "ambient house": "Ambient; Atmospheric",
    "downtempo ambient": "Ambient; Atmospheric",
    "chillout": "Ambient; Atmospheric",
    "chill": "Ambient; Atmospheric",
    "soundscape": "Ambient; Atmospheric",
    "field recording": "Ambient; Atmospheric",
    "field recordings": "Ambient; Atmospheric",
    "isolationist": "Ambient; Atmospheric",
    "generative": "Ambient; Atmospheric",
    "modular": "Ambient; Atmospheric",
    "ethereal": "Ambient; Atmospheric",
    "environmental": "Ambient; Atmospheric",
    "new age": "Ambient; Space Ambient",
    "space": "Ambient; Space Ambient",
    "drone": "Ambient; Drone",
    "atmospheric": "Ambient; Atmospheric",
    "krautrock": "Ambient; Space Ambient",
    "berlin school": "Ambient; Space Ambient",
    "japanese ambient": "Ambient; Atmospheric",
    "balearic": "Ambient; Atmospheric",
    "illbient": "Ambient; Atmospheric",
    "fourth world": "Ambient; Atmospheric",
    "ambient": "Ambient; Atmospheric",

    # Classical & Neo-Classical
    "baroque": "Classical; Baroque",
    "romantic": "Classical; Romantic",
    "minimalism": "Classical; Minimalism",
    "modern classical": "Classical; Contemporary Classical",
    "neo-classical": "Classical; Contemporary Classical",
    "contemporary classical": "Classical; Contemporary Classical",
    "classical": "Classical; Contemporary Classical",

    # Jazz
    "bebop": "Jazz; Bebop",
    "cool jazz": "Jazz; Cool Jazz",
    "post-bop": "Jazz; Post-Bop",
    "modal jazz": "Jazz; Modal Jazz",
    "modal": "Jazz; Modal Jazz",
    "fusion": "Jazz; Fusion",
    "jazz": "Jazz; Cool Jazz",

    # Electronic
    "techno": "Electronic; Techno",
    "house": "Electronic; House",
    "trance": "Electronic; Trance",
    "drum & bass": "Electronic; Drum & Bass",
    "dnb": "Electronic; Drum & Bass",
    "breakbeat": "Electronic; Breakbeat",
    "downtempo": "Electronic; Downtempo",
    "idm": "Electronic; IDM",
    "hardcore": "Electronic; Hardcore & Industrial",
    "industrial": "Electronic; Hardcore & Industrial",
    "electronic": "Electronic; IDM",
    "electronica": "Electronic; IDM",
    
    # Rock
    "alternative": "Rock; Alternative Rock",
    "classic rock": "Rock; Classic Rock",
    "hard rock": "Rock; Hard Rock",
    "punk": "Rock; Punk",
    "indie rock": "Rock; Indie Rock",
    "industrial metal": "Rock; Industrial Metal",
    "black metal": "Rock; Metal",
    "death metal": "Rock; Metal",
    "thrash metal": "Rock; Metal",
    "doom metal": "Rock; Metal",
    "heavy metal": "Rock; Metal",
    "metal": "Rock; Metal",
    "prog": "Rock; Progressive Rock",
    "rock": "Rock; Classic Rock",

    # Pop
    "synthpop": "Pop; Synthpop",
    "indie pop": "Pop; Indie Pop",
    "dream pop": "Pop; Dream Pop",
    "dance": "Pop; Dance-Pop",
    "pop": "Pop; Dance-Pop",

    # Folk & Country
    "americana": "Folk & Country; Americana",
    "bluegrass": "Folk & Country; Bluegrass",
    "folk": "Folk & Country; Contemporary Folk",
    "country": "Folk & Country; Alt-Country",

    # R&B & Soul
    "r&b": "R&B & Soul; Contemporary R&B",
    "funk": "R&B & Soul; Funk",
    "motown": "R&B & Soul; Motown",
    "soul": "R&B & Soul; Neo-Soul",
    "reggae": "R&B & Soul; Neo-Soul",
    
    # Hip-Hop
    "hip hop": "Hip-Hop; East Coast Hip-Hop",
    "hip-hop": "Hip-Hop; East Coast Hip-Hop",
    "rap": "Hip-Hop; East Coast Hip-Hop",
    "trap": "Hip-Hop; Trap",
}

KNOWN_AMBIENT_ARTISTS = {
    "susumu yokota", "lusine", "ludwig a.f. rohrscheid", "ludwig af rohrscheid", "ludwig a.f.",
    "h. takahashi", "h.takahashi", "david edren", "alabaster deplume", "studio",
    "brian eno", "harold budd", "stars of the lid", "william basinski", "biosphere",
    "steve roach", "robert rich", "tim hecker", "fennesz", "loscil", "chihei hatakeyama",
    "hiroshi yoshimura", "midori takada", "satoshi ashikawa", "klaus schulze",
    "tangerine dream", "popol vuh", "manuel gottsching", "eluvium", "grouper",
    "julianna barwick", "aphex twin - selected ambient works"
}

KNOWN_JAZZ_ARTISTS = {
    "miles davis", "john coltrane", "bill evans", "thelonious monk", "charles mingus",
    "herbie hancock", "wayne shorter", "chet baker", "dave brubeck", "ahmad jamal",
    "the ahmad jamal trio", "sonny rollins", "art blakey", "al di meola", "chick corea",
    "keith jarrett", "pat metheny", "sun ra", "pharoah sanders", "kamasi washington",
    "yussef kamaal", "domi & jd beck"
}

KNOWN_CLASSICAL_ARTISTS = {
    "johann sebastian bach", "j.s. bach", "bach", "ludwig van beethoven", "beethoven",
    "wolfgang amadeus mozart", "mozart", "chopin", "debussy", "ravel", "tchaikovsky",
    "brahms", "vivaldi", "philip glass", "steve reich", "max richter", "ludovico einaudi",
    "olafur arnalds", "nils frahm", "arvo part", "joep beving"
}

VALID_NUMERIC_BANDS = {
    "2pac", "10cc", "311", "16 volt", "9 lazy 9", "2 bad mice", "1 giant leap",
    "16 bit lolitas", "16 bit lolita's", "51 days", "2 player", "3 phase", "12 gauge",
    "702", "808 state", "404.zero", "65daysofstatic", "100 gecs", "24kgo1dn",
    "23 skidoo", "4hero", "2 brothers on the 4th floor", "b12", "154", "69", "16b"
}

EXACT_OVERRIDES = {
    "bauhaus": "Bauhaus",
    "2pac": "2Pac",
    "the cure": "The Cure",
    "joy division": "Joy Division",
    "outkast": "OutKast",
    "rjd2": "RJD2",
    "devo": "Devo",
    "boards of canada": "Boards of Canada",
    "aphex twin": "Aphex Twin",
    "u2": "U2",
    "nightmares on wax": "Nightmares on Wax",
    "afx": "AFX",
    "dj food": "DJ Food",
    "billie holiday": "Billie Holiday",
    "bob marley the wailers": "Bob Marley & The Wailers",
    "bob marley & the wailers": "Bob Marley & The Wailers",
    "pan sonic": "Pan Sonic",
    "prefuse 73": "Prefuse 73",
    "various artists": "Various Artists",
    "omd": "OMD",
    "ub40": "UB40",
    "the special aka": "The Special A.K.A.",
    "the specials": "The Specials",
    "dr. hook": "Dr. Hook",
    "the human league": "The Human League",
    "soul ii soul": "Soul II Soul",
    "culture club": "Culture Club",
    "hot chocolate": "Hot Chocolate",
    "talking heads": "Talking Heads",
    "technotronic": "Technotronic",
    "whitesnake": "Whitesnake",
    "duran duran": "Duran Duran",
    "sinead o'connor": "Sinead O'Connor",
    "xtc": "XTC",
    "sunn o": "Sunn O)))",
    "sunn o)))": "Sunn O)))",
    "neu": "Neu!",
    "neu!": "Neu!",
    "pj harvey": "PJ Harvey",
    "cj bolland": "CJ Bolland",
    "kmfdm": "KMFDM",
    "mdfmk": "MDFMK",
    "master boot record": "MASTER BOOT RECORD",
    "inxs": "INXS",
    "acdc": "AC/DC",
    "ac/dc": "AC/DC",
    "alexander robotnick": "Alexander Robotnick",
    "air liquide": "Air Liquide",
    "alabaster deplume": "Alabaster DePlume",
    "meat beat manifesto": "Meat Beat Manifesto",
    "alt-j": "Alt-J",
    "alt - j": "Alt-J",
    "the chemical brothers": "The Chemical Brothers",
    "fatboy slim": "Fatboy Slim",
    "traci lords": "Traci Lords",
    "clock dva": "Clock DVA",
    "add n to (x)": "Add N to (X)",
    "circuit des yeux": "Circuit des Yeux",
    "rs tangent": "RS Tangent",
    "misfits": "Misfits",
    "the misfits": "Misfits",
    "מזמור": "Mizmor"
}

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.pdf'}
JUNK_EXTENSIONS = {'.nfo', '.txt', '.m3u', '.m3u8', '.sfv', '.cue', '.url', '.log', '.ini', '.db', '.ds_store'}

def strip_accents(text):
    if not text: return text
    text = str(text)
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return text.strip()

def clean_filename_str(s):
    if not s: return "Unknown"
    s = strip_accents(s)
    s = re.sub(r'[<>:"/\\|?*]', '_', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.rstrip('. ')
    return s if s else "Unknown"

def to_standard_title_case(name):
    if not name: return "Unknown Artist"
    name_str = clean_filename_str(name)
    norm = re.sub(r'[^\w\s]', '', name_str.lower()).strip()
    
    if norm in EXACT_OVERRIDES:
        return EXACT_OVERRIDES[norm]
    if name_str.lower() in EXACT_OVERRIDES:
        return EXACT_OVERRIDES[name_str.lower()]

    minor_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 'of', 'on', 'or', 'the', 'to', 'with', 'vs', 'feat'}
    honorifics = {'mr', 'ms', 'dr', 'st', 'jr', 'sr', 'vs'}
    is_entire_string_upper = name_str.isupper() and len(name_str.split()) > 1
    words = name_str.split(' ')
    title_words = []
    for idx, w in enumerate(words):
        w_lower = w.lower()
        if w_lower in honorifics:
            title_words.append(w.capitalize())
        elif w_lower in minor_words:
            if idx == 0:
                title_words.append(w.capitalize())
            else:
                title_words.append(w_lower)
        elif len(w) == 2 and not any(v in w_lower for v in 'aeiouy'):
            # 2-letter non-vowel words like 'dj', 'mc', 'rs', 'tv', 'uk' are always uppercase acronyms
            title_words.append(w.upper())
        elif is_entire_string_upper:
            # Entire string was ALL CAPS: keep short acronyms, title-case regular words
            if len(w) <= 3 and (not any(v in w_lower for v in 'aeiou') or w_lower in ['dva', 'u2']):
                title_words.append(w)
            else:
                title_words.append(w.capitalize())
        elif w.isupper() and 2 <= len(w) <= 5:
            # Preserves mixed-case acronyms like 'RS Tangent', 'Clock DVA', 'MDFMK', 'KMFDM'
            title_words.append(w)
        else:
            title_words.append(w.capitalize())
    return ' '.join(title_words)

def clean_artist_name(name, target_lib=None):
    if not name: return "Unknown Artist"
    name_str = strip_accents(name).strip()
    if name_str.lower() in ["<unbekannt>", "unbekannt", "<unknown>", "unknown"]:
        return "Various Artists"

    # Invert 'Last, First' (e.g. 'Yokota, Susumu' -> 'Susumu Yokota', 'Budd, Harold' -> 'Harold Budd')
    m_inv = re.match(r'^([A-Z][a-zA-Z\.\'\-]+),\s+([A-Z][a-zA-Z\.\'\-]+)$', name_str)
    if m_inv:
        name_str = f"{m_inv.group(2)} {m_inv.group(1)}"

    # Strip vinyl/catalog brackets (e.g. '[wag 029] Cobblestone Jazz' -> 'Cobblestone Jazz')
    m_brack = re.match(r'^\[[^\]]+\]\s*(.+)$', name_str)
    if m_brack:
        name_str = m_brack.group(1).strip()
        if ' - ' in name_str:
            name_str = name_str.split(' - ')[0].strip()

    # Strip track number prefix from artist name (e.g. '205 Pato Banton' -> 'Pato Banton')
    m_num_prefix = re.match(r'^\d{2,4}\s+([A-Za-z].+)$', name_str)
    if m_num_prefix:
        name_str = m_num_prefix.group(1).strip()

    norm_lower = re.sub(r'[^\w\s]', '', name_str.lower()).strip()
    if norm_lower in VALID_NUMERIC_BANDS:
        return name_str

    # Accidental pure-number, movement, or trailing underscore tag (e.g. '03', '05_', '12') that is not a valid band
    if re.match(r'^\d{1,3}_*$', name_str) or re.match(r'^[A-Za-z]\d{1,2}$', name_str) or re.match(r'^[A-Za-z]$', name_str):
        return "Unknown Artist"

    m = re.match(r'^\s*(\d{1,2}|[A-Z]\d{1,2}|\d{1,2}-\d{1,2})[\s\.\-_]+(.+)$', name_str)
    if m:
        cand = m.group(2).strip()
        cand_norm = re.sub(r'[^\w\s]', '', cand.lower()).strip()
        if cand_norm in VALID_NUMERIC_BANDS:
            candidate = cand
        else:
            candidate = to_standard_title_case(cand)
    else:
        candidate = to_standard_title_case(name_str)

    if target_lib:
        lib_dir = os.path.join(ROOT_DIR, target_lib)
        if os.path.exists(lib_dir):
            existing_artists = [d for d in os.listdir(lib_dir) if os.path.isdir(os.path.join(lib_dir, d))]
            
            def norm_art(s):
                s = strip_accents(s).lower()
                if s == "מזמור": return "mizmor"
                s = re.sub(r'^(the|a|an)\s+', '', s)
                s = re.sub(r'\b(and)\b', '&', s)
                s = re.sub(r'[^\w\s]', '', s)
                return re.sub(r'\s+', ' ', s).strip()

            cand_norm = norm_art(candidate)

            for ex in existing_artists:
                if ex.lower() in ["compilations", "_incoming", "soundtracks"]: continue
                ex_norm = norm_art(ex)

                # Hard protection against false positives
                if frozenset([cand_norm, ex_norm]) in {frozenset(['live', 'olive']), frozenset(['mesh', 'nmesh'])}:
                    continue

                if cand_norm == ex_norm:
                    return ex

                ratio = difflib.SequenceMatcher(None, cand_norm, ex_norm).ratio()
                if ratio >= 0.90 and abs(len(cand_norm) - len(ex_norm)) <= 2:
                    print(f"    [Fuzzy Match] Ingested '{candidate}' matched existing '{ex}' ({ratio*100:.1f}%) -> Using: '{ex}'")
                    return ex

    return candidate

def map_genre(genre_str, artist=None, album=None, filepath=None):
    # 1. Check known artist directories for high-confidence classification
    if artist:
        a_lower = strip_accents(artist).lower().strip()
        a_norm = re.sub(r'[^\w\s]', '', a_lower)
        if a_lower in KNOWN_AMBIENT_ARTISTS or a_norm in KNOWN_AMBIENT_ARTISTS or any(k in a_lower for k in ["brian eno", "stars of the lid", "tangerine dream", "klaus schulze", "susumu yokota", "lusine"]):
            if any(k in a_lower for k in ["space", "tangerine dream", "klaus schulze", "rohrscheid", "apollo"]):
                return "Ambient; Space Ambient"
            return "Ambient; Atmospheric"
        if a_lower in KNOWN_JAZZ_ARTISTS or a_norm in KNOWN_JAZZ_ARTISTS:
            return "Jazz; Fusion"
        if a_lower in KNOWN_CLASSICAL_ARTISTS or a_norm in KNOWN_CLASSICAL_ARTISTS:
            return "Classical; Contemporary Classical"

    # 2. Check genre tag, album name, and filepath against GENRE_MAP
    search_context = []
    if genre_str: search_context.append(str(genre_str).lower())
    if album: search_context.append(str(album).lower())
    if filepath: search_context.append(str(filepath).lower())
    full_context = " ".join(search_context)

    for k, v in GENRE_MAP.items():
        if k in full_context:
            return v

    return None

def infer_library(genre, artist, album, filepath):
    if not genre:
        return None

    g_lower = genre.lower()
    p_lower = filepath.lower() if filepath else ""
    a_lower = strip_accents(artist).lower().strip() if artist else ""

    if a_lower in KNOWN_AMBIENT_ARTISTS or a_lower in KNOWN_JAZZ_ARTISTS or a_lower in KNOWN_CLASSICAL_ARTISTS:
        return "Ambient Classical & Jazz"

    if any(x in g_lower for x in ["ambient", "classical", "jazz", "baroque", "romantic", "drone", "bebop"]):
        return "Ambient Classical & Jazz"
    if any(x in g_lower for x in ["techno", "house", "trance", "drum & bass", "breakbeat", "idm", "downtempo", "electronic"]):
        return "Electronic"
    if any(x in g_lower for x in ["metal", "industrial"]):
        return "Metal Industrial"
    if any(x in g_lower for x in ["reggae", "world", "folk", "americana", "bluegrass"]):
        return "Reggae & World"
    if any(x in p_lower for x in ["soundtrack", "ost", "holiday", "christmas", "score"]):
        return "Soundtracks & Holiday"
    if any(x in g_lower for x in ["rock", "pop", "hip-hop", "rap", "punk", "indie", "r&b", "soul", "funk"]):
        return "Rock & Pop"

    return None

def prompt_user_for_library(album_name, artist_name, genre):
    print(f"\n[?] Could not automatically determine the destination library for:")
    print(f"    Artist: {artist_name}")
    print(f"    Album : {album_name}")
    print(f"    Genre : {genre}")
    print("Please choose a destination library:")
    for idx, lib in enumerate(LIBRARIES, start=1):
        print(f"  [{idx}] {lib}")
    
    while True:
        try:
            choice = input("Enter choice (1-6) [Default: 5 (Rock & Pop)]: ").strip()
            if not choice:
                return "Rock & Pop"
            val = int(choice)
            if 1 <= val <= len(LIBRARIES):
                return LIBRARIES[val - 1]
        except (ValueError, EOFError):
            return "Rock & Pop"

def read_and_clean_tags(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    tags = {'artist': None, 'albumartist': None, 'album': None, 'title': None, 'track': None, 'genre': None}
    try:
        if ext == '.mp3':
            try: audio = EasyID3(filepath)
            except mutagen.id3.ID3NoHeaderError:
                audio = mutagen.File(filepath, easy=True)
                audio.add_tags()
            tags['artist'] = audio.get('artist', [None])[0]
            tags['albumartist'] = audio.get('albumartist', [None])[0]
            tags['album'] = audio.get('album', [None])[0]
            tags['title'] = audio.get('title', [None])[0]
            tags['genre'] = audio.get('genre', [None])[0]
            trkn = audio.get('tracknumber', [None])[0]
            if trkn: tags['track'] = trkn.split('/')[0]
        elif ext == '.flac':
            audio = FLAC(filepath)
            tags['artist'] = audio.get('artist', [None])[0]
            tags['albumartist'] = audio.get('albumartist', [None])[0]
            tags['album'] = audio.get('album', [None])[0]
            tags['title'] = audio.get('title', [None])[0]
            tags['genre'] = audio.get('genre', [None])[0]
            trkn = audio.get('tracknumber', [None])[0]
            if trkn: tags['track'] = trkn.split('/')[0]
        elif ext in ['.m4a', '.mp4']:
            audio = MP4(filepath)
            tags['artist'] = audio.tags.get('\xa9ART', [None])[0]
            tags['albumartist'] = audio.tags.get('aART', [None])[0]
            tags['album'] = audio.tags.get('\xa9alb', [None])[0]
            tags['title'] = audio.tags.get('\xa9nam', [None])[0]
            tags['genre'] = audio.tags.get('\xa9gen', [None])[0]
            trkn = audio.tags.get('trkn')
            if trkn: tags['track'] = str(trkn[0][0])
        elif ext == '.ogg':
            audio = OggVorbis(filepath)
            tags['artist'] = audio.get('artist', [None])[0]
            tags['albumartist'] = audio.get('albumartist', [None])[0]
            tags['album'] = audio.get('album', [None])[0]
            tags['title'] = audio.get('title', [None])[0]
            tags['genre'] = audio.get('genre', [None])[0]
    except Exception:
        pass
    return tags

def write_tags(filepath, tags):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.mp3':
            try: audio = EasyID3(filepath)
            except mutagen.id3.ID3NoHeaderError:
                audio = mutagen.File(filepath, easy=True)
                audio.add_tags()
            if tags.get('artist'): audio['artist'] = tags['artist']
            if tags.get('albumartist'): audio['albumartist'] = tags['albumartist']
            if tags.get('album'): audio['album'] = tags['album']
            if tags.get('title'): audio['title'] = tags['title']
            if tags.get('genre'): audio['genre'] = tags['genre']
            if tags.get('track'): audio['tracknumber'] = str(tags['track'])
            audio.save()
        elif ext == '.flac':
            audio = FLAC(filepath)
            if tags.get('artist'): audio['artist'] = tags['artist']
            if tags.get('albumartist'): audio['albumartist'] = tags['albumartist']
            if tags.get('album'): audio['album'] = tags['album']
            if tags.get('title'): audio['title'] = tags['title']
            if tags.get('genre'): audio['genre'] = tags['genre']
            if tags.get('track'): audio['tracknumber'] = str(tags['track'])
            audio.save()
        elif ext in ['.m4a', '.mp4']:
            audio = MP4(filepath)
            if tags.get('artist'): audio.tags['\xa9ART'] = tags['artist']
            if tags.get('albumartist'): audio.tags['aART'] = tags['albumartist']
            if tags.get('album'): audio.tags['\xa9alb'] = tags['album']
            if tags.get('title'): audio.tags['\xa9nam'] = tags['title']
            if tags.get('genre'): audio.tags['\xa9gen'] = tags['genre']
            audio.save()
        elif ext == '.ogg':
            audio = OggVorbis(filepath)
            if tags.get('artist'): audio['artist'] = tags['artist']
            if tags.get('albumartist'): audio['albumartist'] = tags['albumartist']
            if tags.get('album'): audio['album'] = tags['album']
            if tags.get('title'): audio['title'] = tags['title']
            if tags.get('genre'): audio['genre'] = tags['genre']
            audio.save()
    except Exception as e:
        print(f"Error saving tags on {filepath}: {e}")

def convert_to_320_mp3(src_filepath):
    ext = os.path.splitext(src_filepath)[1].lower()
    if ext == '.mp3':
        return src_filepath

    tags = read_and_clean_tags(src_filepath)
    base_no_ext = os.path.splitext(src_filepath)[0]
    out_mp3_path = f"{base_no_ext}.mp3"

    print(f"    -> Converting FLAC/Lossless to 320k MP3: {os.path.basename(src_filepath)}")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", src_filepath,
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "320k",
        "-ac", "2",
        out_mp3_path
    ]

    try:
        subprocess.run(cmd, check=True)
        write_tags(out_mp3_path, tags)
        try: os.remove(src_filepath)
        except Exception: pass
        return out_mp3_path
    except Exception as e:
        print(f"    [!] Error converting {src_filepath} to MP3: {e}")
        return src_filepath

def get_track_quality_info(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.mp3':
            m = MP3(filepath)
            br = m.info.bitrate // 1000
            return br, f"MP3 ({br} kbps)"
        elif ext == '.flac':
            return 320, "FLAC (Converted to 320k MP3)"
        elif ext in ['.m4a', '.mp4']:
            m = MP4(filepath)
            br = m.info.bitrate // 1000 if hasattr(m.info, 'bitrate') else 256
            return br, f"AAC ({br} kbps)"
        elif ext == '.ogg':
            o = OggVorbis(filepath)
            br = o.info.bitrate // 1000 if hasattr(o.info, 'bitrate') else 192
            return br, f"OGG ({br} kbps)"
    except Exception:
        pass
    return 128, "MP3 (Unknown bitrate)"

def evaluate_album_quality(file_list):
    if not file_list:
        return 0, "No files"
    scores = []
    descriptions = set()
    for fp in file_list:
        sc, desc = get_track_quality_info(fp)
        scores.append(sc)
        descriptions.add(desc)
    avg_score = sum(scores) / len(scores)
    summary_desc = ", ".join(sorted(descriptions))
    return avg_score, summary_desc

def migrate_media_assets(src_dir, dest_dir):
    if not os.path.exists(src_dir): return
    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        ext = os.path.splitext(item)[1].lower()
        if os.path.isfile(src_item):
            if ext in IMAGE_EXTENSIONS:
                dest_item = os.path.join(dest_dir, item)
                if not os.path.exists(dest_item):
                    try:
                        shutil.move(src_item, dest_item)
                        print(f"  -> Migrated artwork: {item}")
                    except: pass
                else:
                    try: os.remove(src_item)
                    except: pass
            elif ext in JUNK_EXTENSIONS:
                try: os.remove(src_item)
                except: pass

def clean_entire_incoming_directory():
    for root, dirs, files in os.walk(INCOMING_DIR, topdown=False):
        for f in files:
            fp = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            if ext not in {'.mp3', '.flac', '.m4a', '.ogg', '.wav'}:
                try: os.remove(fp)
                except: pass
        for d in dirs:
            dp = os.path.join(root, d)
            try:
                if not os.listdir(dp): os.rmdir(dp)
            except: pass

def print_ascii_destination_tree(dest_dir, single_file_name=None):
    """
    Renders a clean ASCII folder tree diagram from the Media Albums root
    down to the final destination folder and files.
    """
    rel_path = os.path.relpath(dest_dir, ROOT_DIR)
    parts = rel_path.split(os.sep)

    print("\n  =======================================================")
    print("  📁 Destination Tree from Media Root:")
    print("  Music Albums/")
    indent = "  "
    for idx, part in enumerate(parts):
        is_last = (idx == len(parts) - 1)
        prefix = "└── " if is_last else "├── "
        indent += "    "
        print(f"{indent[:-4]}{prefix}{part}/")

    # List files in the destination
    file_indent = indent + "    "
    if single_file_name:
        print(f"{file_indent[:-4]}└── 🎵 {single_file_name}")
    elif os.path.exists(dest_dir):
        files_in_dest = sorted(os.listdir(dest_dir))
        for f_idx, fname in enumerate(files_in_dest):
            if os.path.isdir(os.path.join(dest_dir, fname)):
                continue
            is_last_file = (f_idx == len(files_in_dest) - 1)
            f_prefix = "└── " if is_last_file else "├── "
            ext = os.path.splitext(fname)[1].lower()
            icon = "🖼️ " if ext in IMAGE_EXTENSIONS else "🎵 "
            print(f"{file_indent[:-4]}{f_prefix}{icon}{fname}")
    print("  =======================================================\n")

def main():
    print("==========================================================")
    print("    Music Server Ingestion & Auto-Standardization Engine  ")
    print("==========================================================")
    
    if not os.path.exists(INCOMING_DIR):
        os.makedirs(INCOMING_DIR, exist_ok=True)
        print(f"Created staging directory: {INCOMING_DIR}")
        return

    raw_incoming = []
    for root, dirs, files in os.walk(INCOMING_DIR):
        for f in files:
            if f.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg', '.wav', '.aiff', '.ape')):
                fp = os.path.join(root, f)
                try:
                    if os.path.getsize(fp) == 0:
                        print(f"    [!] Skipping & removing corrupt 0-byte file: {f}")
                        os.remove(fp)
                        continue
                except: pass
                raw_incoming.append(fp)

    if not raw_incoming:
        clean_entire_incoming_directory()
        print(f"No audio files found in: {INCOMING_DIR}")
        return

    converted_files = []
    has_non_mp3 = any(not fp.lower().endswith('.mp3') for fp in raw_incoming)
    if has_non_mp3:
        print("\n--- Converting Incoming Lossless/Non-MP3 Files to 320 KBPS Stereo MP3 ---")
        for fp in raw_incoming:
            if not fp.lower().endswith('.mp3'):
                new_fp = convert_to_320_mp3(fp)
                converted_files.append(new_fp)
            else:
                converted_files.append(fp)
    else:
        converted_files = raw_incoming

    print(f"\nFound {len(converted_files)} 320k MP3 tracks to ingest.\n")

    dirs_map = {}
    for fp in converted_files:
        d = os.path.dirname(fp)
        dirs_map.setdefault(d, []).append(fp)

    total_ingested = 0
    total_replaced = 0
    total_skipped = 0

    for d, files in dirs_map.items():
        sample_file = files[0]
        sample_tags = read_and_clean_tags(sample_file)
        raw_art = sample_tags.get('artist') or "Unknown Artist"
        alb = strip_accents(sample_tags.get('album') or os.path.basename(d))
        gen = map_genre(sample_tags.get('genre'), artist=raw_art, album=alb, filepath=sample_file)

        target_lib = infer_library(gen, raw_art, alb, sample_file)
        if not target_lib:
            target_lib = prompt_user_for_library(alb, raw_art, gen)
            if not gen:
                lib_defaults = {
                    "Ambient Classical & Jazz": "Ambient; Atmospheric",
                    "Electronic": "Electronic; IDM",
                    "Metal Industrial": "Rock; Metal",
                    "Reggae & World": "R&B & Soul; Neo-Soul",
                    "Rock & Pop": "Rock; Alternative Rock",
                    "Soundtracks & Holiday": "Soundtracks & Holiday; Soundtrack"
                }
                gen = lib_defaults.get(target_lib, "Ambient; Atmospheric")

        art = clean_artist_name(raw_art, target_lib=target_lib)

        is_comp = "various" in art.lower() or "compilation" in d.lower()
        album_artist = "Various Artists" if is_comp else art

        safe_artist_dir = clean_filename_str(album_artist)
        safe_album_dir = clean_filename_str(alb)
        dest_dir = os.path.join(ROOT_DIR, target_lib, safe_artist_dir, safe_album_dir)

        print(f"\nEvaluating Album: '{alb}' by '{art}' -> [{target_lib}]")

        if os.path.exists(dest_dir):
            existing_files = [os.path.join(dest_dir, f) for f in os.listdir(dest_dir) 
                              if f.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg', '.wav'))]
            
            if existing_files:
                incoming_score, incoming_desc = evaluate_album_quality(files)
                existing_score, existing_desc = evaluate_album_quality(existing_files)
                
                incoming_count = len(files)
                existing_count = len(existing_files)

                print(f"  [!] Album already exists on server:")
                print(f"      - Incoming : {incoming_count} tracks | Quality: {incoming_desc} (Score: {incoming_score:.1f})")
                print(f"      - Existing : {existing_count} tracks | Quality: {existing_desc} (Score: {existing_score:.1f})")

                if incoming_count > existing_count:
                    print(f"  --> UPGRADE: Incoming version has MORE tracks ({incoming_count} vs {existing_count}).")
                    print(f"      Deleting old version and replacing with complete incoming release...")
                    shutil.rmtree(dest_dir)
                    os.makedirs(dest_dir, exist_ok=True)
                    total_replaced += 1
                elif existing_count > incoming_count:
                    print(f"  --> KEEP EXISTING: Existing version has MORE tracks ({existing_count} vs {incoming_count}).")
                    print(f"      Retaining current album and discarding incomplete incoming files...")
                    for fp in files:
                        try: os.remove(fp)
                        except: pass
                    migrate_media_assets(d, dest_dir)
                    total_skipped += incoming_count
                    continue
                else:
                    if incoming_score > existing_score:
                        print(f"  --> UPGRADE: Incoming version has HIGHER audio quality ({incoming_desc} vs {existing_desc}).")
                        print(f"      Deleting lower-quality version and replacing with incoming...")
                        shutil.rmtree(dest_dir)
                        os.makedirs(dest_dir, exist_ok=True)
                        total_replaced += 1
                    else:
                        print(f"  --> KEEP EXISTING: Existing version is equal/higher quality ({existing_desc} vs {incoming_desc}).")
                        print(f"      Retaining current album and discarding incoming duplicate...")
                        for fp in files:
                            try: os.remove(fp)
                            except: pass
                        migrate_media_assets(d, dest_dir)
                        total_skipped += incoming_count
                        continue

        os.makedirs(dest_dir, exist_ok=True)

        for filepath in files:
            tags = read_and_clean_tags(filepath)
            raw_track_artist = tags.get('artist') or art
            track_artist = clean_artist_name(raw_track_artist, target_lib=target_lib)
            track_title = strip_accents(tags.get('title') or os.path.splitext(os.path.basename(filepath))[0])

            # If track artist resolved to Unknown Artist or is invalid, deduce from title/filename or fallback to album artist
            if track_artist == "Unknown Artist" or not track_artist:
                fname = os.path.splitext(os.path.basename(filepath))[0]
                full_text = f"{fname} {track_title} {alb}".lower()
                if "septet in e-flat major" in full_text or "beethoven" in full_text:
                    track_artist = "Ludwig van Beethoven"
                elif ' - ' in track_title:
                    cand = track_title.split(' - ')[0].strip()
                    cand = re.sub(r'^\d+[\s\.\-_]+', '', cand).strip()
                    if cand and len(cand) > 2:
                        track_artist = clean_artist_name(cand, target_lib=target_lib)
                elif ' - ' in fname:
                    cand = fname.split(' - ')[0].strip()
                    cand = re.sub(r'^\d+[\s\.\-_]+', '', cand).strip()
                    if cand and len(cand) > 2:
                        track_artist = clean_artist_name(cand, target_lib=target_lib)
                
                # Final fallback
                if track_artist == "Unknown Artist" or not track_artist:
                    track_artist = album_artist if album_artist != "Various Artists" else "Various Artists"

            track_num = tags.get('track')
            track_genre = map_genre(tags.get('genre'), artist=track_artist, album=alb, filepath=filepath) or gen

            updated_tags = {
                'artist': track_artist,
                'albumartist': album_artist,
                'album': alb,
                'title': track_title,
                'track': track_num,
                'genre': track_genre
            }
            write_tags(filepath, updated_tags)

            ext = os.path.splitext(filepath)[1]
            if track_num and str(track_num).isdigit():
                dest_filename = f"{int(track_num):02d} - {clean_filename_str(track_title)}{ext}"
            else:
                dest_filename = f"{clean_filename_str(track_title)}{ext}"

            dest_path = os.path.join(dest_dir, dest_filename)
            if os.path.exists(dest_path):
                b, e = os.path.splitext(dest_filename)
                dest_path = os.path.join(dest_dir, f"{b}_dup{e}")

            shutil.move(filepath, dest_path)
            total_ingested += 1
            print(f"  -> Ingested: {dest_filename}")

        migrate_media_assets(d, dest_dir)

        # Print the ASCII tree diagram showing the exact destination structure
        single_file = dest_filename if len(files) == 1 and d == INCOMING_DIR else None
        print_ascii_destination_tree(dest_dir, single_file_name=single_file)

    clean_entire_incoming_directory()

    print(f"\n==========================================================")
    print(f"  Ingestion Summary:")
    print(f"    - Ingested / Standardized : {total_ingested} tracks (320 kbps MP3)")
    if total_replaced > 0:
        print(f"    - Upgraded Duplicate Albums: {total_replaced} albums replaced with better version")
    if total_skipped > 0:
        print(f"    - Skipped Inferior Dupes   : {total_skipped} tracks discarded (existing was better)")
    print(f"  _INCOMING folder is now 100% clean and empty.")
    print(f"  Remember to trigger a 'Scan All Libraries' in Jellyfin.")
    print(f"==========================================================")

if __name__ == "__main__":
    main()
