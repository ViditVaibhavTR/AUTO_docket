@echo off
REM Docket Alert Automation Runner
REM This script sets up the environment and runs the automation

echo Starting Docket Alert Automation...
echo.

REM Set PYTHONPATH to current directory
set PYTHONPATH=.

REM Run the automation
python src\main.py

echo.
echo Automation completed. Check logs\ and screenshots\ directories for results.
pause
