import os
import sys
import re
import difflib
import shutil
import unicodedata
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
import mutagen

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r"\\CHRISGRANTS\files\Media\Music Albums"
LIBRARIES = [
    "Ambient Classical & Jazz",
    "Electronic",
    "Metal Industrial",
    "Reggae & World",
    "Rock & Pop",
    "Soundtracks & Holiday"
]

EXACT_ACRONYMS = {
    "mdfmk": "MDFMK",
    "master boot record": "MASTER BOOT RECORD",
    "kmfdm": "KMFDM",
    "omd": "OMD",
    "ub40": "UB40",
    "afx": "AFX",
    "rjd2": "RJD2",
    "u2": "U2",
    "xtc": "XTC",
    "inxs": "INXS",
    "acdc": "AC/DC",
    "ac/dc": "AC/DC",
    "neu": "Neu!",
    "neu!": "Neu!",
    "sunn o": "Sunn O)))",
    "sunn o)))": "Sunn O)))",
    "2pac": "2Pac",
    "808 state": "808 State",
    "10cc": "10cc",
    "311": "311",
    "16 volt": "16 Volt",
    "404.zero": "404.Zero",
    "b12": "B12",
    "154": "154",
    "69": "69",
    "16b": "16B",
    "9 lazy 9": "9 Lazy 9",
    "16 bit lolitas": "16 Bit Lolitas",
    "16 bit lolita's": "16 Bit Lolitas",
    "alexander robotnick": "Alexander Robotnick",
    "air liquide": "Air Liquide",
    "alabaster deplume": "Alabaster DePlume",
    "meat beat manifesto": "Meat Beat Manifesto"
}

def strip_accents(s):
    if not s: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn').strip()

def normalize_for_sim(s):
    s = strip_accents(s).lower()
    s = re.sub(r'^(the|a|an)\s+', '', s)
    s = re.sub(r'\b(and)\b', '&', s)
    s = re.sub(r'[^\w\s]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def to_canonical_case(name):
    if not name: return ""
    name_str = strip_accents(name)
    norm = re.sub(r'[^\w\s]', '', name_str.lower()).strip()

    if norm in EXACT_ACRONYMS:
        return EXACT_ACRONYMS[norm]
    if name_str.lower() in EXACT_ACRONYMS:
        return EXACT_ACRONYMS[name_str.lower()]

    minor_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 'of', 'on', 'or', 'the', 'to', 'with', 'vs', 'feat'}
    words = name_str.split(' ')
    title_words = []
    for idx, w in enumerate(words):
        w_lower = w.lower()
        if idx > 0 and w_lower in minor_words:
            title_words.append(w_lower)
        else:
            title_words.append(w.capitalize())
    return ' '.join(title_words)

def update_tags(fp, canonical_art):
    ext = os.path.splitext(fp)[1].lower()
    try:
        if ext == '.mp3':
            try: audio = EasyID3(fp)
            except mutagen.id3.ID3NoHeaderError:
                audio = mutagen.File(fp, easy=True)
                audio.add_tags()
            audio['artist'] = canonical_art
            if "compilations" in fp.lower():
                audio['albumartist'] = "Various Artists"
            else:
                audio['albumartist'] = canonical_art
            audio.save()
        elif ext == '.flac':
            audio = FLAC(fp)
            audio['artist'] = canonical_art
            if "compilations" in fp.lower():
                audio['albumartist'] = "Various Artists"
            else:
                audio['albumartist'] = canonical_art
            audio.save()
        elif ext in ['.m4a', '.mp4']:
            audio = MP4(fp)
            audio.tags['\xa9ART'] = canonical_art
            if "compilations" in fp.lower():
                audio.tags['aART'] = "Various Artists"
            else:
                audio.tags['aART'] = canonical_art
            audio.save()
    except Exception:
        pass

def merge_artist_folders(src_dir, dst_dir, canonical_art):
    if not os.path.exists(src_dir): return
    os.makedirs(dst_dir, exist_ok=True)

    for item in os.listdir(src_dir):
        s_item = os.path.join(src_dir, item)
        d_item = os.path.join(dst_dir, item)

        if os.path.isdir(s_item):
            if os.path.exists(d_item):
                for f in os.listdir(s_item):
                    sf = os.path.join(s_item, f)
                    df = os.path.join(d_item, f)
                    if os.path.exists(df):
                        b, e = os.path.splitext(f)
                        df = os.path.join(d_item, f"{b}_dup{e}")
                    shutil.move(sf, df)
                    update_tags(df, canonical_art)
                try: os.rmdir(s_item)
                except: pass
            else:
                shutil.move(s_item, d_item)
                for r, d, fs in os.walk(d_item):
                    for f in fs:
                        if f.lower().endswith(('.mp3', '.flac', '.m4a')):
                            update_tags(os.path.join(r, f), canonical_art)
        elif os.path.isfile(s_item):
            if os.path.exists(d_item):
                b, e = os.path.splitext(item)
                d_item = os.path.join(dst_dir, f"{b}_dup{e}")
            shutil.move(s_item, d_item)
            if d_item.lower().endswith(('.mp3', '.flac', '.m4a')):
                update_tags(d_item, canonical_art)

    for r, d, fs in os.walk(dst_dir):
        for f in fs:
            if f.lower().endswith(('.mp3', '.flac', '.m4a')):
                update_tags(os.path.join(r, f), canonical_art)

    try:
        shutil.rmtree(src_dir)
    except:
        pass

def two_step_rename(parent_dir, current_name, desired_name):
    cur_p = os.path.join(parent_dir, current_name)
    des_p = os.path.join(parent_dir, desired_name)
    temp_p = os.path.join(parent_dir, f"__temp_unify_{re.sub(r'[^a-zA-Z0-9]', '', desired_name)}__")

    if not os.path.exists(cur_p): return
    for r, d, fs in os.walk(cur_p):
        for f in fs:
            if f.lower().endswith(('.mp3', '.flac', '.m4a')):
                update_tags(os.path.join(r, f), desired_name)

    try:
        if os.path.exists(temp_p): shutil.rmtree(temp_p, ignore_errors=True)
        os.rename(cur_p, temp_p)
        os.rename(temp_p, des_p)
    except Exception as e:
        print(f"Rename error for {current_name}: {e}")

def run_library_deduplication(execute=True):
    print("====================================================================")
    print("      Library-Wide Fuzzy Artist Deduplication & Casing Engine       ")
    print("====================================================================")

    total_merges = 0

    for lib in LIBRARIES:
        lib_dir = os.path.join(ROOT, lib)
        if not os.path.exists(lib_dir): continue

        print(f"\n--- Scanning Library: {lib} ---")
        folders = [d for d in os.listdir(lib_dir) if os.path.isdir(os.path.join(lib_dir, d))]
        folders = [d for d in folders if d.lower() not in ["compilations", "_incoming", "soundtracks"]]

        # Find duplicates via normalized similarity
        clusters = []
        visited = set()

        for i in range(len(folders)):
            f1 = folders[i]
            if f1 in visited: continue
            norm1 = normalize_for_sim(f1)
            if len(norm1) < 3: continue

            cluster = [f1]
            for j in range(i + 1, len(folders)):
                f2 = folders[j]
                if f2 in visited: continue
                norm2 = normalize_for_sim(f2)

                ratio = difflib.SequenceMatcher(None, norm1, norm2).ratio()
                is_exact_ci = f1.lower() == f2.lower()
                is_high_sim = ratio >= 0.88 and abs(len(f1) - len(f2)) <= 2

                if is_exact_ci or is_high_sim:
                    cluster.append(f2)
                    visited.add(f2)

            if len(cluster) > 1:
                visited.add(f1)
                clusters.append(cluster)

        # Process clusters
        for cl in clusters:
            # Pick canonical name
            canonical = None
            for name in cl:
                norm = re.sub(r'[^\w\s]', '', name.lower()).strip()
                if norm in EXACT_ACRONYMS:
                    canonical = EXACT_ACRONYMS[norm]
                    break
            if not canonical:
                # Prefer most common / title-cased name
                canonical = to_canonical_case(max(cl, key=len))

            print(f"  [Cluster Found] {cl} -> Canonical: '{canonical}'")
            total_merges += 1

            if execute:
                primary_dir = os.path.join(lib_dir, canonical)
                for variant in cl:
                    variant_dir = os.path.join(lib_dir, variant)
                    if variant != canonical:
                        if os.path.exists(variant_dir):
                            merge_artist_folders(variant_dir, primary_dir, canonical)
                    else:
                        two_step_rename(lib_dir, variant, canonical)

    print(f"\n====================================================================")
    print(f"Library-Wide Deduplication Complete! Processed {total_merges} clusters.")
    print("====================================================================")

if __name__ == "__main__":
    run_library_deduplication(execute=True)
