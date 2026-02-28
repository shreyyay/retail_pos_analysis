# PyInstaller spec for SupplierBillTool.exe
# Bundles: supplier_bill_tool.py (launcher+worker), streamlit, pdfplumber, groq,
#          and all local modules (config, pdf_extractor, llm_parser, tally_importer)
#          plus pdf_import_app.py as a data file (run by the streamlit worker).
#
# Build command (from local-connector\ directory):
#   pyinstaller installer\supplier_bill_tool.spec --distpath dist --workpath build\supplier_bill_tool

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files

SRC = os.path.abspath(".")   # local-connector/

datas     = []
binaries  = []
hiddenimports = []

# ── Collect streamlit and all its dependencies ────────────────────────────────
for pkg in ("streamlit", "pdfplumber", "groq",
            "pdfminer", "PIL", "pypdf",
            "httpx", "httpcore", "anyio", "h11",
            "altair", "pandas", "numpy", "pyarrow",
            "click", "rich", "tenacity", "validators",
            "tornado", "watchdog", "packaging",
            "requests", "urllib3", "charset_normalizer", "certifi",
            "attr", "attrs"):
    try:
        tmp = collect_all(pkg)
        datas        += tmp[0]
        binaries     += tmp[1]
        hiddenimports += tmp[2]
    except Exception:
        pass

# ── Explicitly include streamlit's static UI assets ──────────────────────────
# collect_all('streamlit') often misses the static/ dir in newer versions.
# Without index.html, streamlit falls back to a Node dev server (port 3000).
#
# CRITICAL: server.py is at streamlit/web/server/server.py.
# It computes the static path as Path(__file__).parent.parent/"static"
#   = streamlit/web/static/
# BUT the installed package may have the React UI files at streamlit/static/
# (older pip builds) rather than streamlit/web/static/.
#
# Strategy: find wherever index.html lives in the package, then bundle it to
# BOTH its original location AND streamlit/web/static/ so that server.py's
# inline path computation always finds index.html.
import streamlit as _st_pkg
import pathlib as _pl
_st_pkg_dir = _pl.Path(_st_pkg.__file__).parent  # site-packages/streamlit/
_found_static = False
for _idx in _st_pkg_dir.rglob("static/index.html"):
    _static_dir = _idx.parent          # directory containing index.html
    _rel = _static_dir.relative_to(_st_pkg_dir.parent)  # relative to site-packages/
    _rel_str = str(_rel).replace("\\", "/")
    # Bundle to original location
    datas += [(str(_static_dir), _rel_str)]
    print(f"[spec] Added streamlit static (original):  {_static_dir}  ->  {_rel_str}")
    # ALSO bundle to streamlit/web/static/ — where server.py (at web/server/server.py)
    # always looks via Path(__file__).parent.parent/"static".
    # This handles packages where the React UI is in streamlit/static/ (old layout)
    # but server.py uses the new web/ layout.
    if _rel_str != "streamlit/web/static":
        datas += [(str(_static_dir), "streamlit/web/static")]
        print(f"[spec] Added streamlit static (web/static): {_static_dir}  ->  streamlit/web/static")
    _found_static = True
if not _found_static:
    print("[spec] WARNING: streamlit static/index.html not found — UI will be broken")

# ── Include pdf_import_app.py as a data file ─────────────────────────────────
# The worker subprocess copies it from sys._MEIPASS to a temp path and runs it.
datas += [(os.path.join(SRC, "pdf_import_app.py"), ".")]

# ── Window icon (if present) ──────────────────────────────────────────────────
_ico = os.path.join(SRC, "icon.ico")
if os.path.exists(_ico):
    datas += [(_ico, ".")]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(SRC, "supplier_bill_tool.py")],
    pathex=[SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        # Local modules imported by pdf_import_app.py (bundled as Python modules)
        "config",
        "pdf_extractor",
        "llm_parser",
        "tally_importer",
        # Extras that collect_all sometimes misses
        "psycopg2",
        "psycopg2._psycopg",
        "psycopg2.extensions",
        "tkinter",
        "tkinter.ttk",
        "streamlit.web.cli",
        "streamlit.web.bootstrap",
        "streamlit.runtime.scriptrunner",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join("installer", "rthook_streamlit.py")],
    excludes=["matplotlib"],
    noarchive=True,   # keeps __file__ as real disk paths so streamlit finds its static assets
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SupplierBillTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # windowed — no black console window
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
    name="SupplierBillTool",    # output folder: dist\SupplierBillTool\
)
