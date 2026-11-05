import os
import sys
import shutil
import subprocess
import re
from mutagen.easyid3 import EasyID3
import mutagen

ROOT_DIR = r"\\CHRISGRANTS\files\Media\Books\Audiobooks"
INCOMING_DIR = os.path.join(ROOT_DIR, "_INCOMING")

def get_audio_tags(filepath):
    tags = {'author': 'Unknown Author', 'title': 'Unknown Title', 'genre': 'Misc Fiction'}
    try:
        if filepath.lower().endswith('.mp3'):
            try: audio = EasyID3(filepath)
            except: audio = mutagen.File(filepath, easy=True)
            if audio:
                tags['author'] = audio.get('artist', audio.get('albumartist', [tags['author']]))[0]
                tags['title'] = audio.get('album', audio.get('title', [tags['title']]))[0]
                tags['genre'] = audio.get('genre', [tags['genre']])[0]
        else:
            audio = mutagen.File(filepath)
            if audio:
                if 'artist' in audio: tags['author'] = str(audio['artist'][0])
                elif '\xa9ART' in audio: tags['author'] = str(audio['\xa9ART'][0])
                if 'album' in audio: tags['title'] = str(audio['album'][0])
                elif '\xa9alb' in audio: tags['title'] = str(audio['\xa9alb'][0])
                if 'genre' in audio: tags['genre'] = str(audio['genre'][0])
                elif '\xa9gen' in audio: tags['genre'] = str(audio['\xa9gen'][0])
    except Exception as e:
        pass
    return tags

def clean_name(name):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name.strip()

def optimize_audiobook(src_filepath):
    """
    Optimizes the audiobook file: converts to 64k mono MP3 if not already standard,
    or just returns the path if it's already an optimal format (like m4b).
    """
    ext = os.path.splitext(src_filepath)[1].lower()
    if ext == '.mp3':
        # Audiobooks are typically fine as MP3, we might want to standardize bitrate
        return src_filepath
    
    tags = get_audio_tags(src_filepath)
    base_no_ext = os.path.splitext(src_filepath)[0]
    out_path = f"{base_no_ext}_optimized.mp3"
    
    print(f"    -> Optimizing audio quality for: {os.path.basename(src_filepath)}")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", src_filepath,
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "64k",
        "-ac", "1",
        out_path
    ]
    try:
        subprocess.run(cmd, check=True)
        try: os.remove(src_filepath)
        except: pass
        return out_path
    except Exception as e:
        print(f"    [!] Error optimizing {src_filepath}: {e}")
        return src_filepath

def get_author_books(genre_dir, author):
    books = []
    if not os.path.exists(genre_dir):
        return books
    for item in os.listdir(genre_dir):
        item_path = os.path.join(genre_dir, item)
        if not os.path.isdir(item_path): continue
        if item.lower() == author.lower():
            for sub in os.listdir(item_path):
                if os.path.isdir(os.path.join(item_path, sub)):
                    books.append(sub)
        m = re.match(r'^(.*?)\s*\((.*?)\)$', item)
        if m and m.group(2).lower() == author.lower():
            books.append(m.group(1).strip())
    return books

def process_incoming():
    print("==========================================================")
    print("    Audiobook Server Ingestion & Optimization Engine      ")
    print("==========================================================")
    
    if not os.path.exists(INCOMING_DIR):
        os.makedirs(INCOMING_DIR, exist_ok=True)
        print(f"Created staging directory: {INCOMING_DIR}")
        return

    incoming_files = []
    for root, dirs, files in os.walk(INCOMING_DIR):
        for f in files:
            if f.lower().endswith(('.mp3', '.m4a', '.m4b', '.ogg', '.flac', '.wav')):
                incoming_files.append(os.path.join(root, f))

    if not incoming_files:
        print(f"No audio files found in: {INCOMING_DIR}")
        return

    dirs_map = {}
    for fp in incoming_files:
        d = os.path.dirname(fp)
        dirs_map.setdefault(d, []).append(fp)

    for d, files in dirs_map.items():
        sample_file = files[0]
        tags = get_audio_tags(sample_file)
        author = clean_name(tags.get('author', 'Unknown Author'))
        title = clean_name(tags.get('title', os.path.basename(d)))
        genre = clean_name(tags.get('genre', 'Misc Fiction'))
        
        genre_dir = os.path.join(ROOT_DIR, genre)
        os.makedirs(genre_dir, exist_ok=True)
        
        # Check existing author books to decide structure
        existing_books = get_author_books(genre_dir, author)
        
        # Determine destination folder structure
        # If > 0 existing books, use Author / Title
        if len(existing_books) > 0 or len(dirs_map) > 1: # Just an assumption if multiple ingested
            dest_dir = os.path.join(genre_dir, author, title)
        else:
            # Single book format: Title (Author)
            dest_dir = os.path.join(genre_dir, f"{title} ({author})")
            
        print(f"\nIngesting: '{title}' by '{author}' -> {dest_dir}")
        os.makedirs(dest_dir, exist_ok=True)
        
        # Optimize and move
        for fp in files:
            opt_fp = optimize_audiobook(fp)
            new_file_name = clean_name(os.path.basename(opt_fp))
            dest_fp = os.path.join(dest_dir, new_file_name)
            shutil.move(opt_fp, dest_fp)
            print(f"  -> Placed: {new_file_name}")
            
        # Clean up source dir if it's empty
        try:
            if not os.listdir(d):
                os.rmdir(d)
        except: pass

if __name__ == "__main__":
    process_incoming()
