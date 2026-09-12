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

EXACT_OVERRIDES = {
    "master boot record": "MASTER BOOT RECORD",
    "circuit des yeux": "Circuit des Yeux",
    "alabaster deplume": "Alabaster DePlume",
    "misfits": "Misfits",
    "the misfits": "Misfits",
    "2pac": "2Pac",
    "sunn o": "Sunn O)))",
    "sunn o)))": "Sunn O)))",
    "neu": "Neu!",
    "neu!": "Neu!",
    "alt-j": "Alt-J",
    "alt - j": "Alt-J",
    "acdc": "AC/DC",
    "ac/dc": "AC/DC",
    "outkast": "OutKast",
    "מזמור": "Mizmor",
    "jane's addiction": "Jane's Addiction",
    "janes addiction": "Jane's Addiction",
    "stars of the lid": "Stars of the Lid",
    "bob marley & the wailers": "Bob Marley & The Wailers"
}

FOREIGN_ALIASES = {
    "מזמור": "Mizmor"
}

DO_NOT_MERGE_PAIRS = {
    frozenset(['live', 'olive']),
    frozenset(['mesh', 'nmesh'])
}

def strip_accents(s):
    if not s: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn').strip()

def normalize_for_sim(s):
    s = strip_accents(s).lower()
    if s in FOREIGN_ALIASES:
        s = FOREIGN_ALIASES[s].lower()
    s = re.sub(r'^(the|a|an)\s+', '', s)
    s = re.sub(r'\b(and)\b', '&', s)
    s = re.sub(r'[^\w\s]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def to_canonical_case(name):
    if not name: return ""
    name_str = strip_accents(name)
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
            title_words.append(w.upper())
        elif is_entire_string_upper:
            if len(w) <= 3 and (not any(v in w_lower for v in 'aeiou') or w_lower in ['dva', 'u2']):
                title_words.append(w)
            else:
                title_words.append(w.capitalize())
        elif w.isupper() and 2 <= len(w) <= 5:
            title_words.append(w)
        else:
            title_words.append(w.capitalize())

    return ' '.join(title_words)

def pick_canonical_from_cluster(cluster):
    for name in cluster:
        nl = name.lower()
        norm = re.sub(r'[^\w\s]', '', nl).strip()
        if norm in EXACT_OVERRIDES:
            return EXACT_OVERRIDES[norm]
        if nl in EXACT_OVERRIDES:
            return EXACT_OVERRIDES[nl]
        if name in FOREIGN_ALIASES:
            return FOREIGN_ALIASES[name]

    the_candidates = [n for n in cluster if re.match(r'^The\s+', n, re.IGNORECASE)]
    if the_candidates:
        return to_canonical_case(the_candidates[0])
    
    return to_canonical_case(max(cluster, key=len))

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

    if cur_p == des_p:
        return

    try:
        if os.path.exists(temp_p): shutil.rmtree(temp_p, ignore_errors=True)
        os.rename(cur_p, temp_p)
        os.rename(temp_p, des_p)
    except Exception as e:
        print(f"Rename error for {current_name}: {e}")

def run_deduplication(target_libraries=None, execute=True):
    print("====================================================================")
    print("   Acronym-Aware Fuzzy Artist Deduplication & Casing Engine         ")
    print("====================================================================")

    libs_to_process = target_libraries if target_libraries else LIBRARIES
    total_merges = 0
    total_case_fixes = 0

    for lib in libs_to_process:
        lib_dir = os.path.join(ROOT, lib)
        if not os.path.exists(lib_dir): continue

        print(f"\n--- Scanning Library: {lib} ---")
        folders = [d for d in os.listdir(lib_dir) if os.path.isdir(os.path.join(lib_dir, d))]
        folders = [d for d in folders if d.lower() not in ["compilations", "_incoming", "soundtracks"]]

        # 1. Multi-folder cluster detection
        clusters = []
        visited = set()

        for i in range(len(folders)):
            f1 = folders[i]
            if f1 in visited: continue
            norm1 = normalize_for_sim(f1)
            if not norm1: continue

            cluster = [f1]
            for j in range(i + 1, len(folders)):
                f2 = folders[j]
                if f2 in visited: continue
                norm2 = normalize_for_sim(f2)
                if not norm2: continue

                if frozenset([norm1, norm2]) in DO_NOT_MERGE_PAIRS:
                    continue

                is_exact_norm = (norm1 == norm2)
                is_exact_ci = (f1.lower() == f2.lower())
                ratio = difflib.SequenceMatcher(None, norm1, norm2).ratio()
                is_fuzzy = ratio >= 0.88 and abs(len(norm1) - len(norm2)) <= 2

                if is_exact_norm or is_exact_ci or is_fuzzy:
                    cluster.append(f2)
                    visited.add(f2)

            if len(cluster) > 1:
                visited.add(f1)
                clusters.append(cluster)

        for cl in clusters:
            canonical = pick_canonical_from_cluster(cl)
            print(f"  [Cluster Merged] {cl} -> Canonical: '{canonical}'")
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

        # 2. Standalone folder self-healing casing check
        current_folders = [d for d in os.listdir(lib_dir) if os.path.isdir(os.path.join(lib_dir, d))]
        for folder in current_folders:
            if folder.lower() in ["compilations", "_incoming", "soundtracks"]: continue
            canonical = to_canonical_case(folder)
            if folder != canonical and folder.lower() == canonical.lower():
                print(f"  [Casing Auto-Corrected] '{folder}' -> '{canonical}'")
                total_case_fixes += 1
                if execute:
                    two_step_rename(lib_dir, folder, canonical)

    print(f"\n====================================================================")
    print(f"Deduplication Complete! Merged {total_merges} clusters, corrected {total_case_fixes} casing misalignments.")
    print("====================================================================")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--lib", type=str, help="Specific library to process")
    args = parser.parse_args()

    target = [args.lib] if args.lib else None
    run_deduplication(target_libraries=target, execute=True)
