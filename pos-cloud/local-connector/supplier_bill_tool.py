"""
supplier_bill_tool.py — Entry point for the frozen SupplierBillTool.exe.

Runs in two modes depending on command-line arguments:

  Normal (no args):
      Shows a tkinter status window and starts a streamlit worker subprocess
      (which is this same exe called with --streamlit-worker), then opens
      the browser automatically once the server is ready.

  Worker (--streamlit-worker PATH):
      Called by the launcher above.  Runs the Streamlit app at PATH directly
      without showing any GUI window.
"""

import sys
import os

_WORKER_FLAG = "--streamlit-worker"

# ── Streamlit worker mode ──────────────────────────────────────────────────────
# This branch runs in the subprocess started by the launcher below.

if _WORKER_FLAG in sys.argv:
    idx = sys.argv.index(_WORKER_FLAG)
    _app_script = sys.argv[idx + 1]

    # Bypass streamlit's click CLI (unreliable in frozen bundles).
    # Call bootstrap.run() directly — but its signature changed across versions,
    # so we inspect it at runtime and call with positional args accordingly.
    import inspect
    from streamlit.web.bootstrap import run as _st_run

    _params    = list(inspect.signature(_st_run).parameters.keys())
    _flag_opts = {"server.headless": True, "server.port": 8501,
                  "browser.gatherUsageStats": False}

    if len(_params) >= 4:
        # 4-arg form: (main_script_path, command_line|is_hello, args, flag_options)
        _second = False if _params[1] == "is_hello" else ""
        _st_run(_app_script, _second, [], _flag_opts)
    else:
        # 3-arg form: (main_script_path, args, flag_options)
        _st_run(_app_script, [], _flag_opts)
    sys.exit(0)

# ── Launcher GUI mode ──────────────────────────────────────────────────────────

import subprocess
import threading
import webbrowser
import urllib.request
import tempfile
import shutil
import tkinter as tk
from tkinter import ttk

APP_URL  = "http://localhost:8501"
MAX_WAIT = 60      # seconds to wait for Streamlit to become responsive

# Windows flag: hide console window of the worker subprocess
CREATE_NO_WINDOW = 0x08000000

BG       = "#1e1e2e"
FG       = "#cdd6f4"
ACCENT   = "#89b4fa"
SUCCESS  = "#a6e3a1"
ERROR    = "#f38ba8"
BTN_BG   = "#89b4fa"
BTN_FG   = "#1e1e2e"
ENTRY_BG = "#313244"


def _get_app_script() -> str:
    """Return a file-system path to pdf_import_app.py that the worker can run."""
    if getattr(sys, 'frozen', False):
        # Extract the bundled script to a writable temp location
        src = os.path.join(sys._MEIPASS, "pdf_import_app.py")
        dst = os.path.join(tempfile.gettempdir(), "tallysync_pdf_app.py")
        shutil.copy2(src, dst)
        return dst
    # Dev mode: script lives next to this file
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_import_app.py")


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Supplier Bill Tool")
        self.geometry("380x260")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Window icon
        if getattr(sys, 'frozen', False):
            ico = os.path.join(sys._MEIPASS, "icon.ico")
        else:
            ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(ico):
            self.iconbitmap(ico)

        self._process = None
        self._ready   = False
        self._stopped = False

        self._build_ui()
        self._start_worker()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        tk.Frame(self, bg=ACCENT, height=4).pack(fill="x")

        tk.Label(
            self, text="\U0001f9fe  Supplier Bill Tool",
            bg=BG, fg=ACCENT, font=("Segoe UI", 15, "bold"),
        ).pack(pady=(18, 4))

        self._status_var = tk.StringVar(value="Starting up\u2026")
        self._status_lbl = tk.Label(
            self, textvariable=self._status_var,
            bg=BG, fg=FG, font=("Segoe UI", 10),
        )
        self._status_lbl.pack(pady=(4, 8))

        style = ttk.Style(self)
        style.theme_use("default")
        style.configure(
            "Teal.Horizontal.TProgressbar",
            troughcolor=ENTRY_BG, background=ACCENT,
            bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT,
        )
        self._progress = ttk.Progressbar(
            self, style="Teal.Horizontal.TProgressbar",
            length=300, mode="indeterminate",
        )
        self._progress.pack(pady=(0, 18))
        self._progress.start(12)

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(pady=4)

        self._open_btn = tk.Button(
            btn_frame, text="\U0001f310  Open Browser",
            bg=BTN_BG, fg=BTN_FG, relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14, pady=6, cursor="hand2",
            activebackground=ACCENT, activeforeground=BTN_FG,
            command=self._open_browser, state="disabled",
        )
        self._open_btn.grid(row=0, column=0, padx=6)

        self._stop_btn = tk.Button(
            btn_frame, text="\u23f9  Stop",
            bg=ENTRY_BG, fg=FG, relief="flat",
            font=("Segoe UI", 10),
            padx=14, pady=6, cursor="hand2",
            command=self._on_close,
        )
        self._stop_btn.grid(row=0, column=1, padx=6)

        tk.Label(
            self, text="Keep this window open while using the browser.",
            bg=BG, fg="#6c7086", font=("Segoe UI", 8),
        ).pack(pady=(12, 0))

    # ── Streamlit worker subprocess ───────────────────────────────────────────

    def _start_worker(self):
        """Start this same exe as a streamlit worker subprocess."""
        app_script = _get_app_script()
        cmd = [sys.executable, _WORKER_FLAG, app_script]

        if getattr(sys, 'frozen', False):
            cwd = os.path.dirname(sys.executable)
        else:
            cwd = os.path.dirname(os.path.abspath(__file__))

        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception as e:
            self._set_error(f"Could not start tool: {e}")
            return

        threading.Thread(target=self._poll_ready, daemon=True).start()

    def _poll_ready(self):
        """Poll localhost:8501 until Streamlit responds or we time out."""
        import time
        for _ in range(MAX_WAIT):
            if self._stopped:
                return
            try:
                urllib.request.urlopen(APP_URL, timeout=2)
                self.after(0, self._on_ready)
                return
            except Exception:
                pass
            time.sleep(1)

        self.after(0, lambda: self._set_error(
            "Tool took too long to start.\nPlease close and try again."
        ))

    def _on_ready(self):
        self._ready = True
        self._progress.stop()
        s = ttk.Style(self)
        s.configure("Teal.Horizontal.TProgressbar", background=SUCCESS)
        self._progress.configure(mode="determinate", value=100)

        self._status_var.set("\u2705  Ready \u2014 browser is opening\u2026")
        self._status_lbl.configure(fg=SUCCESS)
        self._open_btn.configure(state="normal")
        self._open_browser()

        self.after(1500, lambda: self._status_var.set("\u2705  Running \u2014 use the browser tab"))

    def _open_browser(self):
        webbrowser.open(APP_URL)

    def _set_error(self, msg: str):
        self._progress.stop()
        self._status_var.set(f"\u274c  {msg}")
        self._status_lbl.configure(fg=ERROR)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def _on_close(self):
        self._stopped = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
        self.destroy()


if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
