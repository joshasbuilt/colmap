@echo off
cd /d "%~dp0"
echo.
echo ========================================
echo   360 NAVIGATION SERVER
echo ========================================
echo   Directory: %CD%
echo   URL: http://localhost:8000
echo ========================================
echo.
echo Starting server...
echo Press Ctrl+C to stop
echo.
python -m http.server 8000
pause



