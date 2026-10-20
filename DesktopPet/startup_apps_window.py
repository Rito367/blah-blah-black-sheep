"""
startup_apps_window.py
Manager for Windows startup auto-launch and user-configured workspace apps.
Allows adding, toggling, removing, and 1-click launching of apps/URLs on PC boot.
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from pathlib import Path
import themes

STARTUP_FOLDER = Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup"
VBS_FILENAME = "run_pet.vbs"


def get_windows_autostart_status() -> bool:
    """Returns True if the pet is currently registered in the Windows Startup folder."""
    try:
        vbs_path = STARTUP_FOLDER / VBS_FILENAME
        return vbs_path.exists()
    except Exception:
        return False


def set_windows_autostart(enable: bool) -> bool:
    """Creates or removes run_pet.vbs in the Windows Startup folder."""
    try:
        STARTUP_FOLDER.mkdir(parents=True, exist_ok=True)
        vbs_path = STARTUP_FOLDER / VBS_FILENAME

        if enable:
            main_script = (Path(__file__).parent / "main.py").resolve()
            # Silent invisible launcher via Windows Script Host
            content = (
                f'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.Run "pythonw ""{main_script}""", 0, False\n'
            )
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        else:
            if vbs_path.exists():
                vbs_path.unlink()
            return True
    except Exception as e:
        print(f"[Warning] Failed to configure Windows autostart: {e}", file=sys.stderr)
        return False


def launch_target(path_or_url: str) -> bool:
    """Launches an application, shortcut, document, or URL cleanly in the background."""
    target = (path_or_url or "").strip()
    if not target:
        return False

    try:
        # Use Windows native startfile (handles .exe, .lnk, URLs, protocols like spotify:, steam:)
        os.startfile(target)
        return True
    except Exception:
        try:
            # Fallback to subprocess.Popen
            subprocess.Popen(target, shell=True)
            return True
        except Exception as err:
            print(f"[Error] Failed to launch '{target}': {err}", file=sys.stderr)
            return False


def find_preset_path(name: str) -> str | None:
    """Finds installed paths for common popular applications on Windows."""
    presets = {
        "Chrome": [
            r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
            r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
            r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
        ],
        "Discord": [
            r"%LocalAppData%\Discord\Update.exe --processStart Discord.exe",
            r"%LocalAppData%\Programs\Discord\Discord.exe",
        ],
        "VS Code": [
            r"%LocalAppData%\Programs\Microsoft VS Code\Code.exe",
            r"%ProgramFiles%\Microsoft VS Code\Code.exe",
        ],
        "Spotify": [
            r"%APPDATA%\Spotify\Spotify.exe",
            r"%LocalAppData%\Microsoft\WindowsApps\Spotify.exe",
            "spotify:",
        ],
        "Steam": [
            r"%ProgramFiles(x86)%\Steam\steam.exe",
            r"%ProgramFiles%\Steam\steam.exe",
            "steam://open/main",
        ],
        "Notepad": ["notepad.exe"],
        "Calculator": ["calc.exe"],
    }

    candidates = presets.get(name, [])
    for c in candidates:
        if c.startswith("http") or ":" in c and not ("\\" in c or "/" in c):
            return c
        expanded = os.path.expandvars(c)
        exe_path = expanded.split(" --")[0]
        if Path(exe_path).exists() or c.endswith(".exe"):
            return expanded
    return None


class StartupAppsWindow:
    def __init__(self, root: tk.Tk, get_data, save_data, on_launch_apps=None, on_menu=None, on_whip=None):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_launch_apps = on_launch_apps
        self.on_menu = on_menu
        self.on_whip = on_whip
        self.win: tk.Toplevel | None = None

    def hide(self):
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None

    def show(self, near_x: int = 100, near_y: int = 100):
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        t = themes.get()
        self.win = tk.Toplevel(self.root)
        self.win.title("Auto-Start & Apps")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 360, 520
        safe_x = max(10, min(near_x, sw - target_w - 10))
        safe_y = max(10, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("border", "#181920"), padx=2, pady=2)
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        outer = tk.Frame(self.win, bg=t.get("bg_card", "#20222e"), padx=12, pady=10)
        outer.pack(fill="both", expand=True)

        # ── Header Bar ──────────────────────────────────────────
        hdr = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        hdr.pack(fill="x", pady=(0, 8))

        tk.Label(
            hdr, text="🚀 AUTO-START & APPS", bg=t.get("bg_card", "#20222e"),
            fg=t.get("accent", "#e74c3c"), font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        close_btn = tk.Label(
            hdr, text="✕", bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.hide())

        if self.on_menu:
            mb = tk.Label(
                hdr, text="☰", bg=t.get("bg_card", "#20222e"),
                fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 9, "bold"), cursor="hand2"
            )
            mb.pack(side="right", padx=(0, 6))
            mb.bind("<Button-1>", lambda e: self.on_menu(close_win=self.win, hide_fn=self.hide))

        data = self.get_data()

        # ── PC & App Auto-Launch Toggles ─────────────────────────
        opts_box = tk.Frame(outer, bg=t.get("bg_grid", "#181924"), padx=8, pady=8)
        opts_box.pack(fill="x", pady=(0, 8))

        # Check Windows startup status
        actual_autostart = get_windows_autostart_status()
        self.pet_boot_var = tk.BooleanVar(value=data.get("autostart_pet_on_boot", actual_autostart))
        
        cb_pet = tk.Checkbutton(
            opts_box, text="Run Desktop Pet when Windows starts",
            variable=self.pet_boot_var,
            command=self._on_toggle_pet_boot,
            bg=t.get("bg_grid", "#181924"), fg=t.get("fg_main", "#ffffff"),
            activebackground=t.get("bg_grid", "#181924"),
            activeforeground=t.get("fg_main", "#ffffff"),
            selectcolor=t.get("bg_card", "#20222e"),
            font=("Segoe UI", 8, "bold")
        )
        cb_pet.pack(anchor="w")

        self.apps_boot_var = tk.BooleanVar(value=data.get("autostart_apps_on_boot", True))
        cb_apps = tk.Checkbutton(
            opts_box, text="Auto-open enabled apps when Pet starts",
            variable=self.apps_boot_var,
            command=self._on_toggle_apps_boot,
            bg=t.get("bg_grid", "#181924"), fg=t.get("fg_main", "#ffffff"),
            activebackground=t.get("bg_grid", "#181924"),
            activeforeground=t.get("fg_main", "#ffffff"),
            selectcolor=t.get("bg_card", "#20222e"),
            font=("Segoe UI", 8)
        )
        cb_apps.pack(anchor="w", pady=(2, 0))

        # ── Scrollable App List Area ─────────────────────────────
        tk.Label(
            outer, text="STARTUP WORKSPACE APPS:",
            bg=t.get("bg_card", "#20222e"), fg=t.get("fg_dim", "#888888"),
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(2, 4))

        list_container = tk.Frame(outer, bg=t.get("bg_grid", "#151620"))
        list_container.pack(fill="both", expand=True, pady=(0, 8))

        self.canvas = tk.Canvas(list_container, bg=t.get("bg_grid", "#151620"), highlightthickness=0)
        self.scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=t.get("bg_grid", "#151620"))

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=310)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # ── Add App Action Buttons ───────────────────────────────
        add_btn_row = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        add_btn_row.pack(fill="x", pady=(0, 6))

        tk.Button(
            add_btn_row, text="➕ Browse App", font=("Segoe UI", 8, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, padx=6, pady=4, command=self._browse_app
        ).pack(side="left", expand=True, fill="x", padx=(0, 2))

        tk.Button(
            add_btn_row, text="🌐 Add URL", font=("Segoe UI", 8, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, padx=6, pady=4, command=self._add_url
        ).pack(side="left", expand=True, fill="x", padx=2)

        tk.Button(
            add_btn_row, text="⚡ Presets", font=("Segoe UI", 8, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, padx=6, pady=4, command=self._show_presets_menu
        ).pack(side="left", expand=True, fill="x", padx=(2, 0))

        # ── Bottom Action Controls ───────────────────────────────
        bottom_row = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        bottom_row.pack(fill="x", pady=(4, 0))

        tk.Button(
            bottom_row, text="▶ Launch All", font=("Segoe UI", 8, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, pady=5, padx=6, command=self._launch_all_enabled
        ).pack(side="left", expand=True, fill="x", padx=(0, 2))

        tk.Button(
            bottom_row, text="💥 Whip", font=("Segoe UI", 8, "bold"),
            bg="#b71c1c", fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, pady=5, padx=6, command=self._spawn_whip
        ).pack(side="left", expand=True, fill="x", padx=2)

        tk.Button(
            bottom_row, text="Close", font=("Segoe UI", 8, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, pady=5, padx=8, command=self.hide
        ).pack(side="right", padx=(2, 0))

        self._refresh_app_list()

    def _on_toggle_pet_boot(self):
        enabled = self.pet_boot_var.get()
        set_windows_autostart(enabled)
        data = self.get_data()
        data["autostart_pet_on_boot"] = enabled
        self.save_data(data)

    def _on_toggle_apps_boot(self):
        enabled = self.apps_boot_var.get()
        data = self.get_data()
        data["autostart_apps_on_boot"] = enabled
        self.save_data(data)

    def _refresh_app_list(self):
        t = themes.get()
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        data = self.get_data()
        apps = data.get("startup_apps", [])

        if not apps:
            empty_lbl = tk.Label(
                self.scroll_frame,
                text="No startup apps configured yet!\nClick '➕ Browse App' or '⚡ Presets' above.",
                bg=t.get("bg_grid", "#151620"), fg=t.get("fg_dim", "#777777"),
                font=("Segoe UI", 8), pady=20
            )
            empty_lbl.pack(fill="x", expand=True)
            return

        for idx, app in enumerate(apps):
            row = tk.Frame(self.scroll_frame, bg=t.get("bg_grid", "#151620"), pady=3, padx=4)
            row.pack(fill="x", expand=True)

            # Enable/Disable toggle checkbox
            enabled_var = tk.BooleanVar(value=app.get("enabled", True))
            cb = tk.Checkbutton(
                row, variable=enabled_var,
                command=lambda i=idx, v=enabled_var: self._toggle_app(i, v.get()),
                bg=t.get("bg_grid", "#151620"),
                activebackground=t.get("bg_grid", "#151620"),
                selectcolor=t.get("bg_card", "#20222e")
            )
            cb.pack(side="left", padx=(0, 2))

            # Info text (Name + Short Path)
            info_frame = tk.Frame(row, bg=t.get("bg_grid", "#151620"))
            info_frame.pack(side="left", fill="x", expand=True)

            name = app.get("name", "Unknown App")
            path = app.get("path", "")
            short_path = path if len(path) <= 32 else path[:14] + "..." + path[-15:]

            tk.Label(
                info_frame, text=name,
                bg=t.get("bg_grid", "#151620"), fg=t.get("fg_main", "#ffffff"),
                font=("Segoe UI", 8, "bold"), anchor="w"
            ).pack(fill="x")

            tk.Label(
                info_frame, text=short_path,
                bg=t.get("bg_grid", "#151620"), fg=t.get("fg_dim", "#777777"),
                font=("Segoe UI", 7), anchor="w"
            ).pack(fill="x")

            # Run single test button
            run_btn = tk.Label(
                row, text="▶", bg=t.get("bg_grid", "#151620"),
                fg=t.get("accent", "#e74c3c"), font=("Segoe UI", 8, "bold"),
                cursor="hand2", padx=4
            )
            run_btn.pack(side="left")
            run_btn.bind("<Button-1>", lambda e, p=path: launch_target(p))

            # Delete button
            del_btn = tk.Label(
                row, text="✕", bg=t.get("bg_grid", "#151620"),
                fg=t.get("fg_dim", "#777777"), font=("Segoe UI", 8, "bold"),
                cursor="hand2", padx=4
            )
            del_btn.pack(side="right")
            del_btn.bind("<Button-1>", lambda e, i=idx: self._delete_app(i))

    def _toggle_app(self, index: int, new_val: bool):
        data = self.get_data()
        apps = data.get("startup_apps", [])
        if 0 <= index < len(apps):
            apps[index]["enabled"] = new_val
            data["startup_apps"] = apps
            self.save_data(data)

    def _delete_app(self, index: int):
        data = self.get_data()
        apps = data.get("startup_apps", [])
        if 0 <= index < len(apps):
            removed = apps.pop(index)
            data["startup_apps"] = apps
            self.save_data(data)
            self._refresh_app_list()

    def _browse_app(self):
        filetypes = [
            ("Applications & Shortcuts", "*.exe *.lnk *.bat *.cmd *.url"),
            ("All Files", "*.*")
        ]
        selected = filedialog.askopenfilename(
            parent=self.win or self.root, title="Select Application or Shortcut", filetypes=filetypes
        )
        if selected:
            path_obj = Path(selected)
            name = path_obj.stem.replace("_", " ").title()
            self._add_app_entry(name=name, path=str(path_obj))

    def _add_url(self):
        url = simpledialog.askstring("Add Website", "Enter URL to open on startup (e.g. https://github.com):", parent=self.win or self.root)
        if url and url.strip():
            url = url.strip()
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url
            name = url.replace("https://", "").replace("http://", "").split("/")[0].capitalize()
            self._add_app_entry(name=f"🌐 {name}", path=url)

    def _show_presets_menu(self):
        if self.win is None or not self.win.winfo_exists():
            return

        win = self.win
        t = themes.get()
        menu = tk.Menu(
            win, tearoff=0,
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#000000"),
            activebackground=t.get("btn", "#cccccc"), activeforeground=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 8)
        )

        preset_list = [
            ("🌐 Google Chrome", "Chrome"),
            ("💬 Discord", "Discord"),
            ("💻 VS Code", "VS Code"),
            ("🎵 Spotify", "Spotify"),
            ("🎮 Steam", "Steam"),
            ("📝 Notepad", "Notepad"),
            ("🧮 Calculator", "Calculator"),
        ]

        for label, key in preset_list:
            menu.add_command(
                label=label,
                command=lambda k=key, l=label: self._add_preset(k, l)
            )

        try:
            menu.tk_popup(win.winfo_pointerx(), win.winfo_pointery())
        finally:
            menu.grab_release()

    def _add_preset(self, preset_key: str, display_label: str):
        found_path = find_preset_path(preset_key)
        if not found_path:
            messagebox.showwarning(
                "Preset Not Found",
                f"Could not automatically locate {preset_key} in standard installation folders.\nYou can use '➕ Browse App' to select its .exe file directly!",
                parent=self.win or self.root
            )
            return

        self._add_app_entry(name=display_label, path=found_path)

    def _add_app_entry(self, name: str, path: str):
        data = self.get_data()
        apps = data.setdefault("startup_apps", [])
        
        # Check if already added
        for existing in apps:
            if existing.get("path") == path:
                messagebox.showinfo("Already Added", f"'{name}' is already in your startup apps list.", parent=self.win or self.root)
                return

        apps.append({"name": name, "path": path, "enabled": True})
        data["startup_apps"] = apps
        self.save_data(data)
        self._refresh_app_list()

    def _launch_all_enabled(self):
        data = self.get_data()
        apps = data.get("startup_apps", [])
        count = 0
        for app in apps:
            if app.get("enabled", True):
                if launch_target(app.get("path", "")):
                    count += 1

        if self.on_launch_apps:
            self.on_launch_apps(count)
        else:
            messagebox.showinfo("Launched", f"🚀 Launched {count} enabled startup app(s)!", parent=self.win or self.root)

    def _spawn_whip(self):
        if self.on_whip:
            self.hide()
            self.on_whip()
