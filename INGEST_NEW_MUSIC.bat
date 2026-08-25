@echo off
title Music Server Ingestion Engine
cd /d "%~dp0"

echo ====================================================================
echo             Music Ingestion ^& Standardization Engine
echo ====================================================================
echo.

python "%~dp0ingest_new_music.py"

echo.
echo ====================================================================
echo Ingestion process finished.
echo ====================================================================
echo.
pause
