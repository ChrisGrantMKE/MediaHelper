@echo off
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
chcp 65001 >nul
cd /d "C:\code\ebook2audiobook"
python_env\python.exe app.py --headless --ebook "C:\code\MediaHelper\The Intentional Father\The Intentional Father - Jon Tyson.epub" --voice "C:\code\ebook2audiobook\NEW\Danny_clip_2.mp3" --tts_engine XTTS --device CUDA --language eng --output_format mp3 --output_dir "C:\code\MediaHelper\The Intentional Father"
