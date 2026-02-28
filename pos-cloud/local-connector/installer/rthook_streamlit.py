# PyInstaller runtime hook for streamlit.
# Runs BEFORE any user code or streamlit imports.
# Ensures streamlit serves its bundled React UI instead of falling back to
# a Node dev server on port 3000.
#
# Root cause: server.py (at streamlit/web/server/server.py) computes the
# static path as Path(__file__).parent.parent/"static" = streamlit/web/static/.
# But the pip-installed package may store the React UI at streamlit/static/.
# The spec now bundles files to BOTH locations.  This hook is belt-and-suspenders:
# it patches the path variable AND any cached boolean, so stale imports can't
# cause a fallback to Node.

import sys
import pathlib


def _patch():
    if not getattr(sys, 'frozen', False):
        return

    meipass = pathlib.Path(sys._MEIPASS)

    # ── Step 1: find the correct static dir ────────────────────────────────────
    # Prefer streamlit/web/static/ (where server.py looks with newer layout).
    st_static = None

    for candidate in meipass.rglob("web/static/index.html"):
        if "streamlit" in str(candidate):
            st_static = candidate.parent
            print(f"[rthook] Found streamlit web/static at: {st_static}", flush=True)
            break

    if st_static is None:
        for candidate in meipass.rglob("static/index.html"):
            if "streamlit" in str(candidate):
                st_static = candidate.parent
                print(f"[rthook] Found streamlit static at: {st_static}", flush=True)
                break

    if st_static is None:
        print(f"[rthook] ERROR: no streamlit static/index.html found under {meipass}", flush=True)
        st_dir = meipass / "streamlit"
        if st_dir.exists():
            hits = list(st_dir.rglob("index.html"))
            for p in hits:
                print(f"[rthook]   index.html at: {p}", flush=True)
            if not hits:
                print(f"[rthook]   (none found)", flush=True)
        return

    # ── Step 2: patch server module ────────────────────────────────────────────
    try:
        import streamlit.web.server.server as _srv

        print(f"[rthook] server.py __file__  = {_srv.__file__}", flush=True)

        # Patch the module-level variable (older streamlit versions use this).
        old = getattr(_srv, '_STATIC_PATH', 'NOT_SET')
        _srv._STATIC_PATH = st_static
        print(f"[rthook] _STATIC_PATH: {old} -> {st_static}", flush=True)

        # Reset any cached boolean that was evaluated from _STATIC_PATH at import
        # time (e.g. _IS_DEV_SERVER = not (_STATIC_PATH/"index.html").exists()).
        for _attr in dir(_srv):
            val = getattr(_srv, _attr, None)
            if isinstance(val, bool) and (
                "dev" in _attr.lower() or "node" in _attr.lower()
            ):
                print(f"[rthook] Resetting {_attr}: {val} -> False", flush=True)
                setattr(_srv, _attr, False)

        # Newer streamlit uses a function (not a module variable) to compute the
        # static dir at runtime. Monkey-patch it to return our known-good path.
        import inspect
        for _fname, _func in inspect.getmembers(_srv, inspect.isfunction):
            try:
                src = inspect.getsource(_func)
            except Exception:
                continue
            if ("static" in src.lower() and
                    ("__file__" in src or "_STATIC_PATH" in src or "index.html" in src)):
                _captured = st_static
                _orig = _func

                def _patched(*a, _p=_captured, **kw):
                    return _p

                setattr(_srv, _fname, _patched)
                print(f"[rthook] Patched function {_fname}() -> {_captured}", flush=True)

    except Exception as e:
        print(f"[rthook] Error during patch: {e}", flush=True)


_patch()
