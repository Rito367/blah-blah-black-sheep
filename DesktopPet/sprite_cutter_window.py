"""
sprite_cutter_window.py
GUI tool to slice sprite sheets, auto-generate character templates, and switch to the new pet live.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
from pathlib import Path
from PIL import Image
import themes

ANIM_NAMES = ["idle", "walk", "jump", "sleep", "eat"]


class SpriteCutterWindow:
    def __init__(self, root: tk.Tk, on_complete=None):
        self.root = root
        self.on_complete = on_complete
        self.win = None
        self.sheet_path = None

    def hide(self):
        self.sheet_path = None
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
        self.win.title("Sprite Sheet Cutter")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 340, 460
        safe_x = max(10, min(near_x, sw - target_w - 10))
        safe_y = max(10, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("bg_card", "#ffffff"))
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        tk.Label(
            self.win, text="✂️ Auto Character Creator", bg=t["bg_card"],
            fg=t["fg_main"], font=("Georgia", 11, "bold")
        ).pack(pady=(10, 4))

        container = tk.Frame(self.win, bg=t["bg_card"])
        container.pack(fill="both", expand=True, padx=15, pady=5)

        # 1. File Selector
        tk.Label(container, text="1. Select Sprite Sheet Image:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 8, "bold")).pack(anchor="w", pady=(4, 2))
        
        file_row = tk.Frame(container, bg=t["bg_card"])
        file_row.pack(fill="x", pady=(0, 6))

        self.file_lbl = tk.Label(file_row, text="No file selected", bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"], font=("Georgia", 7), width=24, anchor="w", padx=4)
        self.file_lbl.pack(side="left", fill="x", expand=True, padx=(0, 4))

        tk.Button(
            file_row, text="Browse", font=("Georgia", 8, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", command=self._browse_image
        ).pack(side="right")

        # 2. Grid Slicing Setup
        tk.Label(container, text="2. Grid Dimensions:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 8, "bold")).pack(anchor="w", pady=(4, 2))
        
        grid_row = tk.Frame(container, bg=t["bg_card"])
        grid_row.pack(fill="x", pady=(0, 6))

        tk.Label(grid_row, text="Cols (Frames):", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 7)).grid(row=0, column=0, sticky="w")
        self.cols_entry = tk.Entry(grid_row, font=("Georgia", 8), width=5, relief="solid", bd=1)
        self.cols_entry.insert(0, "4")
        self.cols_entry.grid(row=0, column=1, padx=(4, 12))

        tk.Label(grid_row, text="Rows:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 7)).grid(row=0, column=2, sticky="w")
        self.rows_entry = tk.Entry(grid_row, font=("Georgia", 8), width=5, relief="solid", bd=1)
        self.rows_entry.insert(0, "1")
        self.rows_entry.grid(row=0, column=3, padx=(4, 0))

        # 3. Output Configuration
        tk.Label(container, text="3. Target Character & Action:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 8, "bold")).pack(anchor="w", pady=(4, 2))

        char_row = tk.Frame(container, bg=t["bg_card"])
        char_row.pack(fill="x", pady=(0, 4))
        tk.Label(char_row, text="Character Name:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 7)).pack(side="left")
        self.char_entry = tk.Entry(char_row, font=("Georgia", 8), relief="solid", bd=1)
        self.char_entry.insert(0, "new_pet")
        self.char_entry.pack(side="right", fill="x", expand=True, padx=(4, 0))

        anim_row = tk.Frame(container, bg=t["bg_card"])
        anim_row.pack(fill="x", pady=(0, 6))
        tk.Label(anim_row, text="Primary Action:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 7)).pack(side="left")
        
        self.anim_var = tk.StringVar(value=ANIM_NAMES[0])
        self.anim_menu = tk.OptionMenu(anim_row, self.anim_var, *ANIM_NAMES)
        self.anim_menu.config(bg=t["btn"], fg=t["fg_white"], font=("Georgia", 7, "bold"), relief="flat", bd=0)
        self.anim_menu.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Auto-equip toggle
        self.auto_equip_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            container, text="Automatically equip character after slicing",
            variable=self.auto_equip_var, bg=t["bg_card"], fg=t["fg_main"],
            activebackground=t["bg_card"], selectcolor=t.get("bg_grid", "#f0f0f0"),
            font=("Georgia", 7)
        ).pack(anchor="w", pady=(0, 4))

        # Action Buttons
        btn_frame = tk.Frame(self.win, bg=t["bg_card"])
        btn_frame.pack(fill="x", padx=15, pady=(8, 12))

        tk.Button(
            btn_frame, text="✨ Slice & Create Pet", font=("Georgia", 8, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t["fg_white"], relief="flat", command=self._slice_and_save
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        tk.Button(
            btn_frame, text="Close", font=("Georgia", 8, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", command=self.hide
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

    def _browse_image(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All files", "*.*")]
        parent_win: tk.Misc = self.win if (self.win is not None and self.win.winfo_exists()) else self.root
        selected = filedialog.askopenfilename(parent=parent_win, title="Select Sprite Sheet", filetypes=filetypes)
        if selected:
            self.sheet_path = Path(selected)
            self.file_lbl.config(text=self.sheet_path.name)
            
            cleaned_name = self.sheet_path.stem.lower().replace(" ", "_").replace("-", "_")
            self.char_entry.delete(0, tk.END)
            self.char_entry.insert(0, cleaned_name)

    def _slice_and_save(self):
        parent_win: tk.Misc = self.win if (self.win is not None and self.win.winfo_exists()) else self.root
        if not self.sheet_path or not self.sheet_path.exists():
            messagebox.showerror("Error", "Please select a valid sprite sheet image first.", parent=parent_win)
            return

        try:
            cols = int(self.cols_entry.get().strip())
            rows = int(self.rows_entry.get().strip())
            if cols <= 0 or rows <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Columns and rows must be positive integers.", parent=parent_win)
            return

        char_name = self.char_entry.get().strip().lower().replace(" ", "_")
        anim_name = self.anim_var.get().strip().lower()

        if not char_name:
            messagebox.showerror("Error", "Please provide a character name.", parent=parent_win)
            return

        assets_dir = Path(__file__).parent / "assets"
        char_dir = assets_dir / char_name
        target_anim_dir = char_dir / anim_name
        target_anim_dir.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(self.sheet_path) as sheet_file:
                sheet = sheet_file.convert("RGBA")
                sheet_w, sheet_h = sheet.size

                frame_w = sheet_w // cols
                frame_h = sheet_h // rows

                saved_files = []
                frame_count = 0
                for r in range(rows):
                    for c in range(cols):
                        box = (c * frame_w, r * frame_h, (c + 1) * frame_w, (r + 1) * frame_h)
                        frame_img = sheet.crop(box)
                        out_path = target_anim_dir / f"{anim_name}_{frame_count:02d}.png"
                        frame_img.save(out_path)
                        saved_files.append(out_path)
                        frame_count += 1

            # Auto-create all other missing animation folders using sliced frames as fallback
            if saved_files:
                for required_anim in ANIM_NAMES:
                    other_dir = char_dir / required_anim
                    if not other_dir.exists() or not any(other_dir.glob("*.png")):
                        other_dir.mkdir(parents=True, exist_ok=True)
                        for idx, src_file in enumerate(saved_files):
                            shutil.copy(src_file, other_dir / f"{required_anim}_{idx:02d}.png")

            messagebox.showinfo(
                "Character Created!",
                f"🎉 Character '{char_name}' successfully created in assets/{char_name}/",
                parent=parent_win
            )

            if self.on_complete:
                self.on_complete(char_name=char_name, char_dir=char_dir, auto_equip=self.auto_equip_var.get())

            self.hide()

        except Exception as e:
            messagebox.showerror("Creation Failed", f"Failed to slice and create character:\n{e}", parent=parent_win)