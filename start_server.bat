@echo off
title God of War Ragnarok Checklist Server
cd /d "%~dp0"
echo ============================================================
echo   God of War Ragnarok - 100%% Checklist Local Server
echo ============================================================
echo.
echo Open on this PC:
echo   http://localhost:8080
echo.
echo Open on your Android phone (connected to the same Wi-Fi):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=* delims= " %%b in ("%%a") do (
        echo   http://%%b:8080
    )
)
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================
python -m http.server 8080 --bind 0.0.0.0

