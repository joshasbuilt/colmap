@echo off
echo ========================================
echo Starting Server from joshscript_aframe
echo ========================================
echo.
echo Current Directory: %CD%
echo.
echo Files here:
dir /b *.html *.json
echo.
echo --- STARTING SERVER NOW ---
echo.
python -m http.server 8000
