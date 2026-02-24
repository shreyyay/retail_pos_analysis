@echo off
REM ============================================================
REM  TallySync Installer Build Script
REM  Run this on a Windows machine from the local-connector\ dir
REM  Requires: Python 3.11+, Inno Setup 6
REM ============================================================

echo [1/4] Installing Python build dependencies...
pip install pyinstaller psycopg2-binary requests

echo.
echo [2/4] Building tally_sync.exe...
pyinstaller installer\tally_sync.spec --distpath dist --workpath build\tally_sync
if errorlevel 1 (
    echo ERROR: tally_sync build failed.
    pause & exit /b 1
)

echo.
echo [3/4] Building TallySyncSetup.exe (setup wizard)...
pyinstaller installer\setup_wizard.spec --distpath dist --workpath build\setup_wizard
if errorlevel 1 (
    echo ERROR: setup_wizard build failed.
    pause & exit /b 1
)

echo.
echo [4/4] Creating Windows installer with Inno Setup...
set INNO="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO% set INNO="C:\Program Files\Inno Setup 6\ISCC.exe"
if not exist %INNO% (
    echo ERROR: Inno Setup 6 not found.
    echo Download from: https://jrsoftware.org/isdl.php
    pause & exit /b 1
)
%INNO% installer\TallySyncInstaller.iss
if errorlevel 1 (
    echo ERROR: Inno Setup build failed.
    pause & exit /b 1
)

echo.
echo ============================================================
echo  SUCCESS: installer\Output\TallySyncInstaller.exe is ready.
echo  Send this single file to each client store.
echo ============================================================
pause
