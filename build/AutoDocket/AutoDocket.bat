@echo off
echo ========================================
echo   Auto Docket - Starting...
echo ========================================
echo.
echo   Server: http://127.0.0.1:8000
echo   Browser will open automatically.
echo   Press Ctrl+C to stop.
echo.
cd /d "%~dp0app"
"%~dp0python\python.exe" launcher.py
pause
