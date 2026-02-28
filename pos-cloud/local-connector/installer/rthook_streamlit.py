# PyInstaller runtime hook for streamlit.
# Runs BEFORE any user code or streamlit imports.
#
# ROOT CAUSE of the "localhost:3000 refused to connect" bug:
#   streamlit/config.py defines global.developmentMode like this:
#
#       return (
#           "site-packages" not in __file__   # config.py's own __file__
#           and "dist-packages" not in __file__
#           ...
#       )
#
#   In a PyInstaller bundle, config.py lives at _MEIPASS/streamlit/config.py —
#   no "site-packages" in the path — so streamlit thinks it's running from
#   source and sets developmentMode=True.
#   With developmentMode=True, server.py redirects ALL requests to
#   localhost:3000 (Node dev server) instead of serving the bundled React UI.
#
# FIX: force global.developmentMode=False before anything else runs.
#   supplier_bill_tool.py also sets this in worker mode, but the rthook runs
#   even earlier (before user code) and guards against any other entry path.

import sys


def _patch():
    if not getattr(sys, 'frozen', False):
        return
    try:
        import streamlit.config as _cfg
        _cfg.set_option("global.developmentMode", False)
        print("[rthook] global.developmentMode forced to False", flush=True)
    except Exception as e:
        print(f"[rthook] WARNING: could not set developmentMode: {e}", flush=True)


_patch()
