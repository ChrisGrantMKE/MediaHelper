@echo off
title Jellyfin Bandcamp Release Watcher
echo ========================================================
echo   Starting Jellyfin - Bandcamp Release Watcher
echo ========================================================
echo   Port: 5055
echo   Endpoint: http://localhost:5055/webhook
echo   Health:   http://localhost:5055/health
echo ========================================================
python jellyfin_listener.py config.json
pause
