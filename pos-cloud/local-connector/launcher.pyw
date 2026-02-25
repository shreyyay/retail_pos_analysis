"""
launcher.pyw — Friendly launcher for the Supplier Bill Tool.

.pyw extension = runs with NO console window on Windows.
Double-click this file (or the Desktop shortcut) to start the tool.

What it does:
  1. Shows a small status window
  2. Starts Streamlit in the background (hidden, no terminal)
  3. Waits until ready, then opens the browser automatically
  4. Lets the user stop cleanly via a button or window close
"""

import os
import sys
import subprocess
import webbrowser
import threading
import tkinter as tk
from tkinter import ttk
import urllib.request

# ── Constants ─────────────────────────────────────────────────────────────────

APP_URL    = "http://localhost:8501"
MAX_WAIT   = 45       # seconds to wait for Streamlit to start
POLL_MS    = 1000     # check every 1 second

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
APP_SCRIPT = os.path.join(BASE_DIR, "pdf_import_app.py")

# Windows flag to hide console window of the subprocess
CREATE_NO_WINDOW = 0x08000000

# ── Colours (matches setup_wizard.py theme) ───────────────────────────────────

BG      = "#1e1e2e"
FG      = "#cdd6f4"
ACCENT  = "#89b4fa"
SUCCESS = "#a6e3a1"
ERROR   = "#f38ba8"
BTN_BG  = "#89b4fa"
BTN_FG  = "#1e1e2e"
ENTRY_BG = "#313244"


# ── Main window ───────────────────────────────────────────────────────────────

class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Supplier Bill Tool")
        self.geometry("380x260")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Try to set icon
        ico = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(ico):
            self.iconbitmap(ico)

        self._process = None
        self._ready   = False
        self._stopped = False
        self._wait_count = 0

        self._build_ui()
        self._start_streamlit()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Accent bar at top
        tk.Frame(self, bg=ACCENT, height=4).pack(fill="x")

        # Title
        tk.Label(
            self, text="🧾  Supplier Bill Tool",
            bg=BG, fg=ACCENT, font=("Segoe UI", 15, "bold"),
        ).pack(pady=(18, 4))

        # Status label
        self._status_var = tk.StringVar(value="Starting up…")
        self._status_lbl = tk.Label(
            self, textvariable=self._status_var,
            bg=BG, fg=FG, font=("Segoe UI", 10),
        )
        self._status_lbl.pack(pady=(4, 8))

        # Progress bar
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

        # Buttons
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(pady=4)

        self._open_btn = tk.Button(
            btn_frame, text="🌐  Open Browser",
            bg=BTN_BG, fg=BTN_FG, relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14, pady=6, cursor="hand2",
            activebackground=ACCENT, activeforeground=BTN_FG,
            command=self._open_browser,
            state="disabled",
        )
        self._open_btn.grid(row=0, column=0, padx=6)

        self._stop_btn = tk.Button(
            btn_frame, text="⏹  Stop",
            bg=ENTRY_BG, fg=FG, relief="flat",
            font=("Segoe UI", 10),
            padx=14, pady=6, cursor="hand2",
            command=self._on_close,
        )
        self._stop_btn.grid(row=0, column=1, padx=6)

        # Hint
        tk.Label(
            self, text="Keep this window open while using the browser.",
            bg=BG, fg="#6c7086", font=("Segoe UI", 8),
        ).pack(pady=(12, 0))

    # ── Streamlit process ─────────────────────────────────────────────────────

    def _start_streamlit(self):
        """Launch streamlit in background with no visible console."""
        python = sys.executable.replace("pythonw.exe", "python.exe")  # need python, not pythonw
        cmd = [python, "-m", "streamlit", "run", APP_SCRIPT,
               "--server.headless", "true",
               "--server.port", "8501",
               "--browser.gatherUsageStats", "false"]
        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=BASE_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception as e:
            self._set_error(f"Could not start tool: {e}")
            return

        # Start polling in a background thread
        threading.Thread(target=self._poll_ready, daemon=True).start()

    def _poll_ready(self):
        """Poll localhost:8501 until Streamlit responds or timeout."""
        for i in range(MAX_WAIT):
            if self._stopped:
                return
            try:
                urllib.request.urlopen(APP_URL, timeout=2)
                # Success — schedule UI update on main thread
                self.after(0, self._on_ready)
                return
            except Exception:
                pass
            self._wait_count = i + 1
            import time; time.sleep(1)

        # Timed out
        self.after(0, lambda: self._set_error(
            "Tool took too long to start.\nMake sure Python and Streamlit are installed."
        ))

    def _on_ready(self):
        """Called on main thread once Streamlit is responsive."""
        self._ready = True
        self._progress.stop()
        self._progress.configure(mode="determinate", value=100,
                                  style="Teal.Horizontal.TProgressbar")

        # Change style to green for done state
        s = ttk.Style(self)
        s.configure("Teal.Horizontal.TProgressbar", background=SUCCESS)
        self._progress["value"] = 100

        self._status_var.set("✅  Ready — browser is opening…")
        self._status_lbl.configure(fg=SUCCESS)
        self._open_btn.configure(state="normal")

        self._open_browser()

        self.after(1500, lambda: self._status_var.set("✅  Running — use the browser tab"))

    def _open_browser(self):
        webbrowser.open(APP_URL)

    def _set_error(self, msg: str):
        self._progress.stop()
        self._status_var.set(f"❌  {msg}")
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


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
