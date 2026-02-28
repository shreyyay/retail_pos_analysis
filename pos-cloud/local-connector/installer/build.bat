@echo off
REM ============================================================
REM  TallySync Installer Build Script
REM  Can be run from anywhere — double-click or call from CMD
REM  Requires: Python 3.11+, Inno Setup 6
REM ============================================================

REM Always run from the local-connector\ directory (parent of this file)
cd /d "%~dp0.."
echo Working directory: %CD%

echo [1/5] Installing Python build dependencies...
pip install pyinstaller ^
    psycopg2-binary requests ^
    pdfplumber groq ^
    streamlit pandas pyarrow altair watchdog validators pillow pdfminer.six
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause & exit /b 1
)

echo.
echo [2/5] Building tally_sync.exe...
python -m PyInstaller installer\tally_sync.spec --distpath dist --workpath build\tally_sync
if errorlevel 1 (
    echo ERROR: tally_sync build failed.
    pause & exit /b 1
)

echo.
echo [3/5] Building TallySyncSetup.exe (setup wizard)...
python -m PyInstaller installer\setup_wizard.spec --distpath dist --workpath build\setup_wizard
if errorlevel 1 (
    echo ERROR: setup_wizard build failed.
    pause & exit /b 1
)

echo.
echo [4/5] Building SupplierBillTool.exe (PDF import tool)...
echo       This step takes several minutes — streamlit has many dependencies.
python -m PyInstaller installer\supplier_bill_tool.spec --distpath dist --workpath build\supplier_bill_tool
if errorlevel 1 (
    echo ERROR: SupplierBillTool build failed.
    pause & exit /b 1
)

echo.
echo [5/5] Creating Windows installer with Inno Setup...
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
