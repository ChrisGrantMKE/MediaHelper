@echo off
chcp 65001 > nul
echo ===================================================
echo   Linda Recordings - Audio Compression & Transcription
echo ===================================================
echo.
python "%~dp0process_linda_recordings.py" --source "W:\New folder" --output "W:\Linda Recordings" --model medium --device cuda
pause
