"""
TallySync Setup Wizard
Configures Supabase connection, writes config.ini, and schedules 3 daily sync tasks.
Run this once on the client's Tally PC after installation.
"""
import configparser
import os
import subprocess
import sys
import tkinter as tk
from tkinter import font, messagebox, ttk

# Determine install directory (works both frozen and as script)
if getattr(sys, 'frozen', False):
    # TallySyncSetup.exe lives in {app}\TallySyncSetup\
    # but config.ini and all scripts live in the parent {app}\
    _INSTALL_DIR = os.path.dirname(os.path.dirname(sys.executable))
else:
    _INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))

_CONFIG_PATH = os.path.join(_INSTALL_DIR, "config.ini")
_SYNC_EXE    = os.path.join(_INSTALL_DIR, "tally_sync", "tally_sync.exe")

SYNC_TIMES = [("11:00", "TallySync_11AM"), ("15:00", "TallySync_3PM"), ("18:00", "TallySync_6PM")]

BG      = "#1e1e2e"
FG      = "#cdd6f4"
ACCENT  = "#89b4fa"
SUCCESS = "#a6e3a1"
ERROR   = "#f38ba8"
ENTRY_BG = "#313244"
BTN_BG  = "#89b4fa"
BTN_FG  = "#1e1e2e"


class SetupWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TallySync Setup")
        self.geometry("560x460")
        self.resizable(False, False)
        self.configure(bg=BG)

        # Try to set a window icon if available
        ico = os.path.join(_INSTALL_DIR, "icon.ico")
        if os.path.exists(ico):
            self.iconbitmap(ico)

        self._build_header()
        self._container = tk.Frame(self, bg=BG)
        self._container.pack(fill="both", expand=True, padx=30, pady=10)

        self._frames = {}
        for F in (PageConfig, PageTest, PageSchedule, PageDone):
            frame = F(self._container, self)
            self._frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self._container.grid_rowconfigure(0, weight=1)
        self._container.grid_columnconfigure(0, weight=1)

        self.show(PageConfig)

    def _build_header(self):
        hdr = tk.Frame(self, bg=ACCENT, height=5)
        hdr.pack(fill="x")
        tk.Label(
            self, text="🔄  TallySync Setup",
            bg=BG, fg=ACCENT,
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(18, 0))

    def show(self, page_class):
        frame = self._frames[page_class]
        frame.on_show()
        frame.tkraise()


class _Page(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)
        self.controller = controller

    def on_show(self):
        pass

    def _label(self, text, size=11, bold=False, fg=FG):
        style = "bold" if bold else "normal"
        return tk.Label(self, text=text, bg=BG, fg=fg,
                        font=("Segoe UI", size, style))

    def _entry(self, show=None):
        e = tk.Entry(self, bg=ENTRY_BG, fg=FG, insertbackground=FG,
                     relief="flat", font=("Segoe UI", 10), show=show)
        e.configure(highlightthickness=1, highlightbackground=ACCENT,
                    highlightcolor=ACCENT)
        return e

    def _button(self, text, command, bg=BTN_BG, fg=BTN_FG):
        return tk.Button(self, text=text, command=command,
                         bg=bg, fg=fg, relief="flat",
                         font=("Segoe UI", 10, "bold"),
                         padx=16, pady=6, cursor="hand2",
                         activebackground=ACCENT, activeforeground=BTN_FG)


class PageConfig(_Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._label("Step 1 of 3 — Enter Your Details", 13, bold=True).pack(pady=(12, 2))
        self._label("Fill in all fields below, then click Next.",
                    9, fg="#a6adc8").pack(pady=(0, 8))

        # Supabase URL
        self._label("Supabase Database URL", 10, bold=True).pack(anchor="w")
        self._label("Supabase → Connect → Session pooler → copy the connection string",
                    8, fg="#a6adc8").pack(anchor="w")
        self.db_url = self._entry()
        self.db_url.pack(fill="x", pady=(2, 8))
        self.db_url.insert(0, "postgresql://postgres:PASSWORD@db.XXXX.supabase.co:5432/postgres")

        # Store ID
        self._label("Store ID  (short name for this shop, no spaces)", 10, bold=True).pack(anchor="w")
        self.store_id = self._entry()
        self.store_id.pack(fill="x", pady=(2, 8))
        self.store_id.insert(0, "STORE001")

        # Groq AI Key
        self._label("Groq AI Key  (for reading supplier PDF bills)", 10, bold=True).pack(anchor="w")
        self._label("Get a free key at: console.groq.com → API Keys → Create",
                    8, fg="#a6adc8").pack(anchor="w")
        self.groq_key = self._entry(show="*")
        self.groq_key.pack(fill="x", pady=(2, 8))

        # Tally port (de-emphasised)
        self._label("Tally Port  (leave as 9000 unless changed)", 8, fg="#a6adc8").pack(anchor="w")
        self.tally_port = self._entry()
        self.tally_port.pack(fill="x", pady=(2, 12))
        self.tally_port.insert(0, "9000")

        self._button("Next → Test Connection", self._next).pack(side="right")

    def _next(self):
        db_url   = self.db_url.get().strip()
        store_id = self.store_id.get().strip().upper()
        groq_key = self.groq_key.get().strip()
        port     = self.tally_port.get().strip()

        if not db_url or db_url.startswith("postgresql://postgres:PASSWORD"):
            messagebox.showerror("Missing", "Please enter your Supabase Database URL.")
            return
        if not store_id:
            messagebox.showerror("Missing", "Please enter a Store ID (e.g. STORE001).")
            return
        if not groq_key or not groq_key.startswith("gsk_"):
            messagebox.showerror(
                "Missing Groq Key",
                "Please enter your Groq AI key.\n\n"
                "It starts with 'gsk_'.\n"
                "Get one free at: console.groq.com → API Keys → Create"
            )
            return
        if not port.isdigit():
            messagebox.showerror("Invalid", "Tally port must be a number.")
            return

        self.controller._db_url   = db_url
        self.controller._store_id = store_id
        self.controller._groq_key = groq_key
        self.controller._port     = port
        self.controller.show(PageTest)


class PageTest(_Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._label("Step 2 of 3 — Test Database Connection", 13, bold=True).pack(pady=(20, 4))
        self._label("Click the button below to verify the connection to Supabase.",
                    9, fg="#a6adc8").pack(pady=(0, 20))

        self.status_var = tk.StringVar(value="")
        self.status_lbl = self._label("", fg=FG)
        self.status_lbl.pack(pady=10)

        self._button("Test Connection", self._test).pack(pady=6)

        self.next_btn = self._button("Next → Schedule Tasks", self._next,
                                     bg="#313244", fg=FG)
        self.next_btn.pack(side="right", pady=(30, 0))
        self.next_btn.configure(state="disabled")

    def on_show(self):
        self.status_lbl.configure(text="", fg=FG)
        self.next_btn.configure(state="disabled")

    def _test(self):
        self.status_lbl.configure(text="Testing…", fg=FG)
        self.update()
        try:
            import psycopg2
            conn = psycopg2.connect(self.controller._db_url, connect_timeout=10)
            conn.close()
            self.status_lbl.configure(text="✓  Connection successful!", fg=SUCCESS)
            self.next_btn.configure(state="normal", bg=BTN_BG, fg=BTN_FG)
        except Exception as e:
            self.status_lbl.configure(text=f"✗  {e}", fg=ERROR)

    def _next(self):
        self.controller.show(PageSchedule)


class PageSchedule(_Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._label("Step 3 of 3 — Write Config & Schedule Tasks", 13, bold=True).pack(pady=(20, 4))
        self._label(
            "This will:\n"
            "  • Write config.ini with your settings\n"
            "  • Create 3 Windows Task Scheduler entries:\n"
            "       TallySync_11AM  → 11:00 AM daily\n"
            "       TallySync_3PM   → 3:00 PM daily\n"
            "       TallySync_6PM   → 6:00 PM daily",
            9, fg="#a6adc8",
        ).pack(pady=(0, 20), anchor="w")

        self.log = tk.Text(self, height=6, bg=ENTRY_BG, fg=FG,
                           font=("Consolas", 9), relief="flat", state="disabled")
        self.log.pack(fill="x", pady=6)

        self._button("Install", self._install).pack(pady=6)
        self.done_btn = self._button("Finish", lambda: self.controller.show(PageDone),
                                     bg="#313244", fg=FG)
        self.done_btn.pack(side="right", pady=(10, 0))
        self.done_btn.configure(state="disabled")

    def _log(self, msg, color=FG):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.update()

    def _install(self):
        c = self.controller

        # 1. Write config.ini (includes Groq key)
        cfg = configparser.ConfigParser()
        cfg["tally"]    = {"host": "localhost", "port": c._port}
        cfg["supabase"] = {"db_url": c._db_url, "store_id": c._store_id}
        cfg["sync"]     = {"initial_lookback_days": "7", "max_days_per_sync": "30"}
        cfg["groq"]     = {"api_key": c._groq_key, "model": "llama-3.3-70b-versatile"}
        try:
            with open(_CONFIG_PATH, "w") as f:
                cfg.write(f)
            self._log(f"✓  config.ini written to {_CONFIG_PATH}")
        except Exception as e:
            self._log(f"✗  Failed to write config.ini: {e}", ERROR)
            return

        # 2. Create 3 scheduled tasks (Tally sync)
        exe = _SYNC_EXE if os.path.exists(_SYNC_EXE) else os.path.join(_INSTALL_DIR, "tally_sync.exe")
        all_ok = True
        for time_str, task_name in SYNC_TIMES:
            cmd = [
                "schtasks", "/create",
                "/tn", task_name,
                "/tr", f'"{exe}"',
                "/sc", "DAILY",
                "/st", time_str,
                "/rl", "HIGHEST",
                "/f",
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    self._log(f"✓  Task {task_name} scheduled at {time_str}")
                else:
                    self._log(f"✗  Task {task_name}: {result.stderr.strip()}", ERROR)
                    all_ok = False
            except Exception as e:
                self._log(f"✗  Task {task_name}: {e}", ERROR)
                all_ok = False

        # 3. Create Desktop shortcut for Supplier Bill Tool
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, "Supplier Bill Tool.lnk")

            # Prefer the frozen SupplierBillTool.exe (installer mode)
            supplier_exe = os.path.join(_INSTALL_DIR, "SupplierBillTool", "SupplierBillTool.exe")

            if os.path.exists(supplier_exe):
                # Installer mode: shortcut goes directly to SupplierBillTool.exe
                vbs = (
                    f'Set sh = WScript.CreateObject("WScript.Shell")\n'
                    f'Set lnk = sh.CreateShortcut("{shortcut_path}")\n'
                    f'lnk.TargetPath = "{supplier_exe}"\n'
                    f'lnk.Arguments = ""\n'
                    f'lnk.WorkingDirectory = "{os.path.dirname(supplier_exe)}"\n'
                    f'lnk.Description = "Open Supplier Bill Tool"\n'
                    f'lnk.Save\n'
                )
            else:
                # Dev fallback: run launcher.pyw via pythonw.exe
                launcher_path = os.path.join(_INSTALL_DIR, "launcher.pyw")
                pythonw_path  = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                if not os.path.exists(pythonw_path):
                    pythonw_path = sys.executable
                vbs = (
                    f'Set sh = WScript.CreateObject("WScript.Shell")\n'
                    f'Set lnk = sh.CreateShortcut("{shortcut_path}")\n'
                    f'lnk.TargetPath = "{pythonw_path}"\n'
                    f'lnk.Arguments = """{launcher_path}"""\n'
                    f'lnk.WorkingDirectory = "{_INSTALL_DIR}"\n'
                    f'lnk.Description = "Open Supplier Bill Tool"\n'
                    f'lnk.Save\n'
                )
            vbs_path = os.path.join(_INSTALL_DIR, "_create_shortcut.vbs")
            with open(vbs_path, "w") as f:
                f.write(vbs)
            subprocess.run(["cscript", "//nologo", vbs_path], capture_output=True)
            os.remove(vbs_path)
            self._log("✓  Desktop shortcut created: Supplier Bill Tool")
        except Exception as e:
            self._log(f"  (Shortcut creation skipped: {e})", "#a6adc8")

        if all_ok:
            self._log("\nSetup complete! Click Finish.", SUCCESS)
            self.done_btn.configure(state="normal", bg=BTN_BG, fg=BTN_FG)
        else:
            self._log("\nSome tasks failed. Try running as Administrator.", ERROR)


class PageDone(_Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._label("🎉  Setup Complete!", 16, bold=True, fg=SUCCESS).pack(pady=(20, 8))
        self._label(
            "TallySync is installed and ready.\n\n"
            "Daily sales data will sync automatically:\n"
            "  • 11:00 AM  •  3:00 PM  •  6:00 PM\n\n"
            "To add a supplier bill to Tally:\n"
            "  • Double-click  \"Supplier Bill Tool\"  on your Desktop\n"
            "  • A browser tab opens — drop the PDF, check details,\n"
            "    and click  Save to Tally\n\n"
            "That's it! No more manual data entry.",
            10, fg=FG,
        ).pack(pady=8, padx=10, anchor="w")
        self._button("Close", controller.destroy).pack(pady=16)


if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
