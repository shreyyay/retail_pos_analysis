# PyInstaller runtime hook for streamlit.
# Runs BEFORE any user code or streamlit imports.
# Finds the actual streamlit static dir (with index.html) and patches
# server._STATIC_PATH so streamlit serves its bundled UI instead of
# falling back to a Node dev server on port 3000.

import sys
import os
import pathlib


def _patch():
    if not getattr(sys, 'frozen', False):
        return

    meipass = pathlib.Path(sys._MEIPASS)

    # ── Step 1: Find the correct static directory ──────────────────────────────
    # In newer streamlit (1.12+), UI files live in streamlit/web/static/.
    # In older streamlit they were in streamlit/static/.
    # Search for web/static/index.html FIRST (more specific), then fall back.
    st_static = None

    # Preferred: streamlit/web/static/index.html
    for candidate in meipass.rglob("web/static/index.html"):
        if "streamlit" in str(candidate):
            st_static = candidate.parent
            print(f"[rthook] Found streamlit web/static at: {st_static}")
            break

    # Fallback: any static/index.html under the streamlit tree
    if st_static is None:
        for candidate in meipass.rglob("static/index.html"):
            if "streamlit" in str(candidate):
                st_static = candidate.parent
                print(f"[rthook] Found streamlit static at: {st_static}")
                break

    if st_static is None:
        print(f"[rthook] ERROR: streamlit static/index.html not found under {meipass}")
        # List every index.html in the bundle for diagnosis
        st_dir = meipass / "streamlit"
        if st_dir.exists():
            found = list(st_dir.rglob("index.html"))
            if found:
                for p in found:
                    print(f"[rthook]   index.html at: {p}")
            else:
                print(f"[rthook]   no index.html anywhere under {st_dir}")
        return

    # ── Step 2: Patch server._STATIC_PATH and reset cached dev-mode flags ──────
    try:
        import streamlit.web.server.server as _srv

        # Print __file__ so we can confirm noarchive=True is working
        print(f"[rthook] server.py __file__           = {_srv.__file__}")
        old = getattr(_srv, '_STATIC_PATH', None)
        print(f"[rthook] server._STATIC_PATH (before) = {old}")
        _srv._STATIC_PATH = st_static
        print(f"[rthook] server._STATIC_PATH (after)  = {st_static}")

        # Reset any module-level boolean cached from _STATIC_PATH at import time.
        # e.g. _IS_DEV_SERVER = not (_STATIC_PATH / "index.html").exists()
        for _attr in dir(_srv):
            val = getattr(_srv, _attr, None)
            if isinstance(val, bool) and (
                "dev" in _attr.lower() or "node" in _attr.lower()
            ):
                print(f"[rthook] Resetting {_attr}: {val} -> False")
                setattr(_srv, _attr, False)

    except Exception as e:
        print(f"[rthook] Could not patch server._STATIC_PATH: {e}")


_patch()
