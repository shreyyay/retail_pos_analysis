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

    # Find the static directory that actually contains index.html.
    # Location varies by streamlit version:
    #   older: streamlit/static/
    #   newer: streamlit/web/static/
    st_static = None
    for candidate in meipass.rglob("static/index.html"):
        if "streamlit" in str(candidate):
            st_static = candidate.parent
            print(f"[rthook] Found streamlit static at: {st_static}")
            break

    if st_static is None:
        print(f"[rthook] ERROR: streamlit static/index.html not found anywhere under {meipass}")
        # List what IS in the bundle under streamlit/ for diagnosis
        st_dir = meipass / "streamlit"
        if st_dir.exists():
            for p in sorted(st_dir.iterdir()):
                print(f"[rthook]   {p.name}/")
        return

    # Import server module and patch _STATIC_PATH before it is used.
    # NOTE: any boolean cached at import time (e.g. _IS_DEV_SERVER) also
    # needs to be reset. We patch both the variable and any derived booleans.
    try:
        import streamlit.web.server.server as _srv
        old = getattr(_srv, '_STATIC_PATH', None)
        _srv._STATIC_PATH = st_static
        print(f"[rthook] server._STATIC_PATH: {old} -> {st_static}")

        # Reset any module-level cached boolean that was derived from _STATIC_PATH
        # before our patch (evaluated during module import).
        for _attr in dir(_srv):
            if "dev" in _attr.lower() or "node" in _attr.lower():
                print(f"[rthook]   found attr: {_attr} = {getattr(_srv, _attr, '?')}")

    except Exception as e:
        print(f"[rthook] Could not patch server._STATIC_PATH: {e}")


_patch()
