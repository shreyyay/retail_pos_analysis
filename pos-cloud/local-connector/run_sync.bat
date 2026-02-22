@echo off
REM Tally to Cloud nightly sync — schedule via Windows Task Scheduler at 10:00 PM
REM Setup: pip install -r requirements.txt, then edit config.ini
cd /d "%~dp0"
python tally_connector.py
