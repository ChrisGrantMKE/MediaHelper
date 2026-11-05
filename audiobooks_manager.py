import os
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
        if filepath.endswith('.mp3'):
            try: audio = EasyID3(filepath)
            except: audio = mutagen.File(filepath, easy=True)
            if audio:
                tags['author'] = audio.get('artist', audio.get('albumartist', [tags['author']]))[0]
                tags['title'] = audio.get('album', audio.get('title', [tags['title']]))[0]
                tags['genre'] = audio.get('genre', [tags['genre']])[0]
        # For m4b/m4a, etc., basic mutagen extraction
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

def standardize_library(dry_run=True):
    print("--- STANDARDIZING EXISTING LIBRARY ---")
    
    genres = [d for d in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, d)) and d != "_INCOMING"]
    
    for genre in genres:
        genre_path = os.path.join(ROOT_DIR, genre)
        
        # Step 1: Process READ / UNREAD folders
        for status in ['READ', 'UNREAD', '!unread']:
            status_dir = os.path.join(genre_path, status)
            if os.path.exists(status_dir):
                for book_folder in os.listdir(status_dir):
                    book_path = os.path.join(status_dir, book_folder)
                    if os.path.isdir(book_path):
                        clean_status = "UNREAD" if status == "!unread" else status
                        new_book_path = os.path.join(genre_path, book_folder)
                        new_status_path = os.path.join(new_book_path, clean_status)
                        
                        if dry_run:
                            print(f"[DRY RUN] Status Move: {book_path} -> {new_book_path} (nested in {clean_status})")
                        else:
                            if not os.path.exists(new_book_path):
                                os.makedirs(new_book_path, exist_ok=True)
                            os.makedirs(new_status_path, exist_ok=True)
                            for f in os.listdir(book_path):
                                shutil.move(os.path.join(book_path, f), os.path.join(new_status_path, f))
                            shutil.rmtree(book_path)
                
                if not dry_run and not os.listdir(status_dir):
                    os.rmdir(status_dir)

if __name__ == "__main__":
    import sys
    dry = '--execute' not in sys.argv
    standardize_library(dry_run=dry)
