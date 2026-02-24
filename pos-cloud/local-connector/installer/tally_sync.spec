# PyInstaller spec for tally_sync.exe
# Build command: pyinstaller installer\tally_sync.spec
# (run from the local-connector\ directory)

import os
SRC = os.path.abspath(".")   # local-connector/

a = Analysis(
    [os.path.join(SRC, "tally_connector.py")],
    pathex=[SRC],
    binaries=[],
    datas=[],
    hiddenimports=[
        "psycopg2",
        "psycopg2._psycopg",
        "psycopg2.extensions",
        "requests",
        "urllib3",
        "charset_normalizer",
        "certifi",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="tally_sync",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,          # show console window so log output is visible
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
    name="tally_sync",     # output folder: dist\tally_sync\
)
