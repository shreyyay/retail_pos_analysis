# PyInstaller runtime hook for streamlit.
# Runs BEFORE any user code or streamlit imports.
# Patches _STATIC_PATH so streamlit finds its bundled UI assets in sys._MEIPASS.

import sys
import os
import pathlib


def _patch():
    if not getattr(sys, 'frozen', False):
        return

    meipass = pathlib.Path(sys._MEIPASS)
    st_static = meipass / "streamlit" / "static"

    if not st_static.is_dir():
        # Log the problem so the worker log shows it
        print(f"[rthook] WARNING: streamlit/static not found in bundle at {st_static}")
        # Try to find it anywhere under meipass
        for candidate in meipass.rglob("index.html"):
            if candidate.parent.name == "static":
                st_static = candidate.parent
                print(f"[rthook] Found static at: {st_static}")
                break
        else:
            print(f"[rthook] ERROR: No streamlit/static/index.html found in bundle")
            return

    print(f"[rthook] Patching streamlit static path -> {st_static}")

    # Import and patch the server module BEFORE streamlit evaluates _STATIC_PATH
    # at module level. This is the earliest point we can intercept it.
    try:
        import streamlit.web.server.server as _srv
        _srv._STATIC_PATH = st_static
        print(f"[rthook] Patched server._STATIC_PATH OK")
    except Exception as e:
        print(f"[rthook] Could not patch server._STATIC_PATH: {e}")

    # Also set env var as belt-and-suspenders for any other path lookups
    os.environ["STREAMLIT_STATIC_PATH"] = str(st_static)


_patch()
