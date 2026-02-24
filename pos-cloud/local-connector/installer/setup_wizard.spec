# PyInstaller spec for TallySyncSetup.exe
# Build command: pyinstaller installer\setup_wizard.spec
# (run from the local-connector\ directory)

import os
SRC = os.path.abspath(".")   # local-connector/

a = Analysis(
    [os.path.join(SRC, "setup_wizard.py")],
    pathex=[SRC],
    binaries=[],
    datas=[],
    hiddenimports=[
        "psycopg2",
        "psycopg2._psycopg",
        "psycopg2.extensions",
        "tkinter",
        "tkinter.ttk",
        "tkinter.font",
        "tkinter.messagebox",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "pandas"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TallySyncSetup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # windowed — no console, pure GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TallySyncSetup",  # output folder: dist\TallySyncSetup\
)
