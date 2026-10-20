"""
rename_char_window.py
Popup dialog to rename an existing character folder in assets/ and refresh the pet.
"""

import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import themes

ASSETS_DIR = Path(__file__).parent / "assets"


class RenameCharacterWindow:
    def __init__(self, root: tk.Tk, current_char_dir: Path, on_renamed=None):
        self.root = root
        self.char_dir = current_char_dir
        self.on_renamed = on_renamed
        self.win = None

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
        self.win.title("Rename Character")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 280, 180
        safe_x = max(10, min(near_x, sw - target_w - 10))
        safe_y = max(10, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("bg_card", "#ffffff"))
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        tk.Label(
            self.win, text="✏️ Rename Character", bg=t["bg_card"],
            fg=t["fg_main"], font=("Georgia", 10, "bold")
        ).pack(pady=(12, 6))

        curr_name = self.char_dir.name.replace("_", " ").title()
        tk.Label(
            self.win, text=f"Current: {curr_name}", bg=t["bg_card"],
            fg=t.get("fg_dim", "#777777"), font=("Georgia", 8)
        ).pack(pady=(0, 6))

        container = tk.Frame(self.win, bg=t["bg_card"])
        container.pack(fill="x", padx=16, pady=4)

        tk.Label(container, text="New Name:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 8, "bold")).pack(anchor="w")
        self.name_entry = tk.Entry(container, font=("Georgia", 9), relief="solid", bd=1)
        self.name_entry.insert(0, self.char_dir.name.replace("_", " "))
        self.name_entry.pack(fill="x", pady=(2, 8))
        self.name_entry.focus_set()

        btn_frame = tk.Frame(self.win, bg=t["bg_card"])
        btn_frame.pack(fill="x", padx=16, pady=(4, 10))

        tk.Button(
            btn_frame, text="Save Name", font=("Georgia", 8, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t["fg_white"], relief="flat",
            command=self._apply_rename
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        tk.Button(
            btn_frame, text="Cancel", font=("Georgia", 8, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", command=self.win.destroy
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

    def _apply_rename(self):
        p_win: tk.Misc = self.win if (self.win is not None and self.win.winfo_exists()) else self.root
        if self.char_dir.name == "pet":
            messagebox.showwarning("Default Character", "The default 'Cat' character ('pet') cannot be renamed to preserve system defaults.\nYou can rename any custom characters!", parent=p_win)
            return

        new_display = self.name_entry.get().strip()
        if not new_display:
            messagebox.showerror("Error", "Name cannot be blank.", parent=p_win)
            return

        new_folder_name = new_display.lower().replace(" ", "_")
        target_dir = ASSETS_DIR / new_folder_name

        if target_dir == self.char_dir:
            if self.win:
                self.win.destroy()
            return

        if target_dir.exists():
            messagebox.showerror("Error", f"A character named '{new_display}' already exists.", parent=p_win)
            return

        try:
            self.char_dir.rename(target_dir)
            self.char_dir = target_dir
            if self.on_renamed:
                self.on_renamed(new_folder_name, target_dir)
            if self.win:
                self.win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename character:\n{e}", parent=p_win)