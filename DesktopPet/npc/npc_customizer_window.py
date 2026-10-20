"""
npc_customizer_window.py
GUI Customizer Studio for the NPC Dog Walker.
Supports photo uploading, interactive marquee cropping (face oval vs full body),
wardrobe editing (shirts, pants, shoes, custom shirt upload), dimension & speed sliders,
dialogue editing for NPC and Pet, and real-time live walking preview.
"""

from __future__ import annotations
import os
import sys
import math
import json
from typing import Any
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk, ImageOps

import themes
import npc_graphics

try:
    import paths
    NPC_ASSETS_DIR = paths.ASSETS_DIR / "npc"
except ImportError:
    NPC_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "npc"

# Supported image file extensions
IMAGE_EXTENSIONS = [
    ("Image Files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
    ("PNG Images", "*.png"),
    ("JPEG Images", "*.jpg;*.jpeg"),
    ("All Files", "*.*"),
]

LEASH_COLORS = {
    "Classic Leather": "#8B4513",
    "Gold Chain": "#FFD700",
    "Neon Blue": "#00E5FF",
    "Crimson Red": "#DC2626",
    "Pastel Pink": "#F472B6",
    "Obsidian Black": "#111827",
}

DEFAULT_NPC_CONFIG: dict[str, Any] = {
    "enabled": True,
    "char_scale": 1.0,
    "face_scale": 1.0,
    "face_offset_x": 0,
    "face_offset_y": 0,
    "is_mirror_base": False,
    "walk_speed": 3,
    "leash_length": 200,
    "leash_color": "#8B4513",
    "shirt_style": "Hoodie",
    "shirt_color": "#1E3A8A",
    "pants_style": "Jeans",
    "pants_color": "#2563EB",
    "shoe_color": "#F9FAFB",
    "crop_mode": "face",
}

DEFAULT_NPC_DIALOGUES = {
    "npc_walk_messages": [
        "Good doggy! Enjoying the walk?",
        "Who's a good boy? You are!",
        "Nice brisk walk today!",
        "Keep pacing with me, buddy!",
        "Look at you trotting along!",
    ],
    "npc_pull_messages": [
        "Keep up! Don't stop now!",
        "Come along, doggy!",
        "Heel! Follow my lead!",
        "Don't get stuck sniffing!",
        "Steady on the leash!",
    ],
    "npc_arrival_messages": [
        "We reached our spot! Good job!",
        "Made it to our destination! Take a rest.",
        "What a fantastic walk!",
        "Sit and stay, good boy!",
    ],
    "pet_leash_walk_messages": [
        "Walkies! 🐾 Best time of day!",
        "Sniff sniff... what's that over there?",
        "Trotting along happily~ 🐶",
        "Panting happily~ ♡",
    ],
    "pet_leash_pull_messages": [
        "Slow down! My paws are tired! 😫",
        "Hey, wait for me! Leash is too tight!",
        "Too fast! 🏃💨 Can we take a break?",
        "Stop pulling so hard! 🥺",
    ],
}


class NPCCustomizerWindow:
    """The studio window to customize the NPC dog walker."""

    def __init__(self, root: tk.Tk, get_data_fn, save_data_fn, on_save_and_start=None, on_close=None):
        self.root = root
        self.get_data = get_data_fn
        self.save_data = save_data_fn
        self.on_save_and_start = on_save_and_start
        self.on_close = on_close

        self.win: tk.Toplevel | None = None
        self.loaded_image: Image.Image | None = None
        self.custom_shirt_img: Image.Image | None = None
        self.cropped_head_img: Image.Image | None = None

        # Configuration state
        self.cfg: dict[str, Any] = dict(DEFAULT_NPC_CONFIG)

        # Dialogues state
        self.dialogues = dict(DEFAULT_NPC_DIALOGUES)

        # Cropper canvas state
        self._crop_scale = 1.0
        self._crop_img_tk = None
        self._crop_rect = [30, 30, 130, 130]  # [x1, y1, x2, y2]
        self._drag_mode = None
        self._drag_start = (0, 0)

        # Preview animation state
        self._preview_phase = 0.0
        self._preview_timer = None
        self._preview_tk = None
        self._preview_mode = "walk"  # "walk" or "idle"

    def show(self, near_x: int = 100, near_y: int = 100):
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        # Load existing config from pet_data if available
        data = self.get_data()
        saved_cfg = data.get("npc_walker", {})
        self.cfg = {**DEFAULT_NPC_CONFIG, **saved_cfg}

        for cat in DEFAULT_NPC_DIALOGUES:
            self.dialogues[cat] = list(data.get(cat, DEFAULT_NPC_DIALOGUES[cat]))

        t = themes.get()
        self.win = tk.Toplevel(self.root)
        self.win.title("🎨 NPC Dog Walker Studio")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 760, 620
        safe_x = max(10, min(near_x - target_w // 2, sw - target_w - 20))
        safe_y = max(10, min(near_y - target_h // 2, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("bg_card", "#ffffff"))
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        # Load saved custom head if exists
        custom_face_path = NPC_ASSETS_DIR / "custom_face.png"
        if custom_face_path.exists():
            try:
                self.cropped_head_img = Image.open(custom_face_path).convert("RGBA")
            except Exception:
                self.cropped_head_img = None

        if self.cropped_head_img is None:
            self.cropped_head_img = npc_graphics.create_default_face(60)

        # Load custom shirt if exists
        custom_shirt_path = NPC_ASSETS_DIR / "custom_shirt.png"
        if custom_shirt_path.exists():
            try:
                self.custom_shirt_img = Image.open(custom_shirt_path).convert("RGBA")
            except Exception:
                self.custom_shirt_img = None

        self._build_ui()
        self._start_preview_loop()

    def hide(self):
        if self._preview_timer:
            try:
                self.root.after_cancel(self._preview_timer)
            except Exception:
                pass
            self._preview_timer = None
        if hasattr(self, "win") and self.win is not None:
            try:
                if self.win.winfo_exists():
                    self.win.destroy()
            except Exception:
                pass
            self.win = None
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass

    def _build_ui(self):
        t = themes.get()

        # Header Bar
        hdr = tk.Frame(self.win, bg=t.get("bg_hdr", "#ffb6c1"), pady=8, padx=14)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="🐕 NPC Dog Walker Studio & Customizer",
            bg=t.get("bg_hdr", "#ffb6c1"), fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 12, "bold")
        ).pack(side="left")

        # Main Split Body
        main_body = tk.Frame(self.win, bg=t.get("bg_card", "#ffffff"))
        main_body.pack(fill="both", expand=True, padx=10, pady=8)

        # Left Column: Notebook Tabs for Customization (Width: 480)
        left_frame = tk.Frame(main_body, bg=t.get("bg_card", "#ffffff"))
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Setup Notebook Tabs
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=t.get("bg_card", "#ffffff"), borderwidth=0)
        style.configure("TNotebook.Tab", background=t.get("bg_grid", "#f0f0f0"), foreground=t.get("fg_main", "#333333"), font=("Segoe UI", 9, "bold"), padding=[10, 4])
        style.map("TNotebook.Tab", background=[("selected", t.get("btn", "#f8bbd0"))], foreground=[("selected", t.get("fg_white", "#ffffff"))])

        self.notebook = ttk.Notebook(left_frame)
        self.notebook.pack(fill="both", expand=True)

        tab_photo = tk.Frame(self.notebook, bg=t.get("bg_card", "#ffffff"), padx=8, pady=8)
        tab_wardrobe = tk.Frame(self.notebook, bg=t.get("bg_card", "#ffffff"), padx=8, pady=8)
        tab_dimensions = tk.Frame(self.notebook, bg=t.get("bg_card", "#ffffff"), padx=8, pady=8)
        tab_dialogue = tk.Frame(self.notebook, bg=t.get("bg_card", "#ffffff"), padx=8, pady=8)

        self.notebook.add(tab_photo, text="👤 Head & Photo")
        self.notebook.add(tab_wardrobe, text="👕 Wardrobe")
        self.notebook.add(tab_dimensions, text="📏 Size & Leash")
        self.notebook.add(tab_dialogue, text="💬 Dialogue")

        self._build_photo_tab(tab_photo)
        self._build_wardrobe_tab(tab_wardrobe)
        self._build_dimensions_tab(tab_dimensions)
        self._build_dialogue_tab(tab_dialogue)

        # Right Column: Live Animated Preview & Action Buttons
        right_frame = tk.Frame(main_body, bg=t.get("bg_card", "#ffffff"), width=220)
        right_frame.pack(side="right", fill="y")

        self._build_preview_panel(right_frame)

    # ── TAB 1: PHOTO & HEAD CROPPER ──────────────────────────────────────────
    def _build_photo_tab(self, parent: tk.Frame):
        t = themes.get()

        top_row = tk.Frame(parent, bg=t["bg_card"])
        top_row.pack(fill="x", pady=(0, 6))

        tk.Button(
            top_row, text="📁 Upload Photo...", font=("Segoe UI", 9, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", cursor="hand2",
            command=self._upload_photo
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            top_row, text="🔄 Flip Face", font=("Segoe UI", 9, "bold"),
            bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"], relief="flat", cursor="hand2",
            command=self._toggle_flip_base
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            top_row, text="Default Chibi Face", font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"], relief="flat",
            command=self._use_default_face
        ).pack(side="right")

        # Cropper Canvas
        tk.Label(
            parent, text="Drag the blue box to crop the face/head:",
            bg=t["bg_card"], fg=t.get("fg_dim", "#666666"), font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(0, 2))

        self.crop_canvas = tk.Canvas(
            parent, width=380, height=220, bg="#1E1E1E", highlightthickness=1, highlightbackground="#4B5563"
        )
        self.crop_canvas.pack(pady=(0, 6))
        self.crop_canvas.bind("<ButtonPress-1>", self._on_crop_press)
        self.crop_canvas.bind("<B1-Motion>", self._on_crop_drag)
        self.crop_canvas.bind("<ButtonRelease-1>", self._on_crop_release)

        # Apply Crop Button
        tk.Button(
            parent, text="✂️ Crop Selection to Head", font=("Segoe UI", 9, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t["fg_white"], relief="flat", cursor="hand2",
            command=self._apply_crop
        ).pack(fill="x", pady=(0, 6))

        # Sliders for Face Tuning
        slider_frame = tk.Frame(parent, bg=t["bg_card"])
        slider_frame.pack(fill="x")

        # Face Size (Bobblehead)
        tk.Label(slider_frame, text="🙂 Face Size (Bobblehead):", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
        self.face_scale_slider = tk.Scale(
            slider_frame, from_=0.5, to=2.0, resolution=0.05, orient="horizontal",
            bg=t["bg_card"], highlightthickness=0, command=self._on_face_scale_change
        )
        self.face_scale_slider.set(float(self.cfg.get("face_scale", 1.0)))
        self.face_scale_slider.grid(row=0, column=1, sticky="ew", padx=6)

        # Face Height Offset
        tk.Label(slider_frame, text="↕️ Head Height Offset:", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 8, "bold")).grid(row=1, column=0, sticky="w")
        self.face_off_y_slider = tk.Scale(
            slider_frame, from_=-40, to=40, resolution=1, orient="horizontal",
            bg=t["bg_card"], highlightthickness=0, command=self._on_face_off_y_change
        )
        self.face_off_y_slider.set(int(self.cfg.get("face_offset_y", 0)))
        self.face_off_y_slider.grid(row=1, column=1, sticky="ew", padx=6)

        slider_frame.columnconfigure(1, weight=1)

        # Draw default face on cropper canvas initially
        self._display_crop_image(npc_graphics.create_default_face(180))

    # ── TAB 2: WARDROBE (CLOTHES) ────────────────────────────────────────────
    def _build_wardrobe_tab(self, parent: tk.Frame):
        t = themes.get()

        # 1. Shirt Selection
        tk.Label(parent, text="👕 Shirt Style:", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(2, 2))
        self.shirt_style_var = tk.StringVar(value=str(self.cfg.get("shirt_style", "Hoodie")))
        style_menu = tk.OptionMenu(
            parent, self.shirt_style_var, *npc_graphics.SHIRT_STYLES,
            command=lambda val=None: self._on_wardrobe_change()
        )
        style_menu.config(bg=t["btn"], fg=t["fg_white"], font=("Segoe UI", 8, "bold"), relief="flat", bd=0)
        style_menu.pack(fill="x", pady=(0, 6))

        # Shirt Colors
        tk.Label(parent, text="Shirt Color:", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
        shirt_col_frame = tk.Frame(parent, bg=t["bg_card"])
        shirt_col_frame.pack(fill="x", pady=(0, 6))

        for name, col in list(npc_graphics.SHIRT_COLORS.items())[:8]:
            btn = tk.Button(
                shirt_col_frame, bg=col, width=2, height=1, relief="solid", bd=1, cursor="hand2",
                command=lambda c=col: self._set_shirt_color(c)
            )
            btn.pack(side="left", padx=2)

        # Custom Shirt Graphic Upload
        custom_shirt_row = tk.Frame(parent, bg=t["bg_card"])
        custom_shirt_row.pack(fill="x", pady=(2, 8))
        tk.Button(
            custom_shirt_row, text="🖼️ Upload Shirt Logo/Graphic", font=("Segoe UI", 8, "bold"),
            bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"], relief="flat", cursor="hand2",
            command=self._upload_shirt_graphic
        ).pack(side="left")
        tk.Button(
            custom_shirt_row, text="Clear Graphic", font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"], relief="flat",
            command=self._clear_shirt_graphic
        ).pack(side="left", padx=6)

        # 2. Pants Selection
        tk.Label(parent, text="👖 Pants Style:", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 2))
        self.pants_style_var = tk.StringVar(value=str(self.cfg.get("pants_style", "Jeans")))
        pants_menu = tk.OptionMenu(
            parent, self.pants_style_var, *npc_graphics.PANTS_STYLES,
            command=lambda val=None: self._on_wardrobe_change()
        )
        pants_menu.config(bg=t["btn"], fg=t["fg_white"], font=("Segoe UI", 8, "bold"), relief="flat", bd=0)
        pants_menu.pack(fill="x", pady=(0, 6))

        # Pants Colors
        tk.Label(parent, text="Pants Color:", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
        pants_col_frame = tk.Frame(parent, bg=t["bg_card"])
        pants_col_frame.pack(fill="x", pady=(0, 6))

        for name, col in npc_graphics.PANTS_COLORS.items():
            btn = tk.Button(
                pants_col_frame, bg=col, width=2, height=1, relief="solid", bd=1, cursor="hand2",
                command=lambda c=col: self._set_pants_color(c)
            )
            btn.pack(side="left", padx=2)

        # 3. Shoes Selection
        tk.Label(parent, text="👟 Shoes Style & Color:", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 2))
        self.shoe_color_var = tk.StringVar(value="Sneakers (White)")
        shoe_menu = tk.OptionMenu(
            parent, self.shoe_color_var, *npc_graphics.SHOE_COLORS.keys(),
            command=lambda val=None: self._on_shoe_change(str(val) if val is not None else "")
        )
        shoe_menu.config(bg=t["btn"], fg=t["fg_white"], font=("Segoe UI", 8, "bold"), relief="flat", bd=0)
        shoe_menu.pack(fill="x")

    # ── TAB 3: DIMENSIONS & LEASH ────────────────────────────────────────────
    def _build_dimensions_tab(self, parent: tk.Frame):
        t = themes.get()

        # Character Overall Height & Scale
        tk.Label(parent, text="🚶 Character Height & Size:", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 0))
        self.char_scale_slider = tk.Scale(
            parent, from_=0.5, to=2.0, resolution=0.05, orient="horizontal",
            bg=t["bg_card"], highlightthickness=0, command=self._on_char_scale_change
        )
        self.char_scale_slider.set(float(self.cfg.get("char_scale", 1.0)))
        self.char_scale_slider.pack(fill="x", pady=(0, 8))

        # Walk Speed
        tk.Label(parent, text="🏃 Walk Speed (1 = stroll, 10 = sprint):", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 0))
        self.speed_slider = tk.Scale(
            parent, from_=1, to=10, resolution=1, orient="horizontal",
            bg=t["bg_card"], highlightthickness=0, command=lambda v: self.cfg.update({"walk_speed": int(v)})
        )
        self.speed_slider.set(int(self.cfg.get("walk_speed", 3)))
        self.speed_slider.pack(fill="x", pady=(0, 8))

        # Leash Max Length
        tk.Label(parent, text="〰️ Leash Max Length (px):", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 0))
        self.leash_len_slider = tk.Scale(
            parent, from_=80, to=400, resolution=10, orient="horizontal",
            bg=t["bg_card"], highlightthickness=0, command=lambda v: self.cfg.update({"leash_length": int(v)})
        )
        self.leash_len_slider.set(int(self.cfg.get("leash_length", 200)))
        self.leash_len_slider.pack(fill="x", pady=(0, 8))

        # Leash Color Presets
        tk.Label(parent, text="🎨 Leash Color:", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 2))
        leash_col_frame = tk.Frame(parent, bg=t["bg_card"])
        leash_col_frame.pack(fill="x")

        for name, col in LEASH_COLORS.items():
            btn = tk.Button(
                leash_col_frame, text=name, bg=col, fg="#FFFFFF" if col not in ("#FFD700", "#F472B6") else "#111827",
                font=("Segoe UI", 7, "bold"), relief="flat", cursor="hand2", padx=6, pady=3,
                command=lambda c=col: self.cfg.update({"leash_color": c})
            )
            btn.pack(side="left", padx=3)

    # ── TAB 4: DIALOGUE EDITOR ───────────────────────────────────────────────
    def _build_dialogue_tab(self, parent: tk.Frame):
        t = themes.get()

        cat_names = [
            ("npc_walk_messages", "🚶 Owner Walking Lines"),
            ("npc_pull_messages", "🪢 Owner Leash Pull Lines"),
            ("npc_arrival_messages", "🎯 Owner Destination Arrival Lines"),
            ("pet_leash_walk_messages", "🐾 Pet Leash Walking Lines"),
            ("pet_leash_pull_messages", "😫 Pet Leash Pull Complaints"),
        ]

        self.cur_diag_cat = "npc_walk_messages"

        # Category dropdown
        tk.Label(parent, text="Category:", bg=t["bg_card"], fg=t["fg_main"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.diag_cat_var = tk.StringVar(value=cat_names[0][1])

        def on_cat_change(selection):
            for key, label in cat_names:
                if label == selection:
                    self.cur_diag_cat = key
                    break
            self._refresh_dialogue_list()

        cat_menu = tk.OptionMenu(parent, self.diag_cat_var, *[c[1] for c in cat_names], command=on_cat_change)
        cat_menu.config(bg=t["btn"], fg=t["fg_white"], font=("Segoe UI", 8, "bold"), relief="flat", bd=0)
        cat_menu.pack(fill="x", pady=(0, 6))

        # Listbox for lines
        self.diag_listbox = tk.Listbox(
            parent, height=6, bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"],
            font=("Segoe UI", 8), selectbackground=t.get("accent", "#e74c3c"), relief="flat"
        )
        self.diag_listbox.pack(fill="both", expand=True, pady=(0, 6))

        # Add Entry
        add_frame = tk.Frame(parent, bg=t["bg_card"])
        add_frame.pack(fill="x", pady=(0, 4))

        self.diag_entry = tk.Entry(add_frame, font=("Segoe UI", 8), relief="solid", bd=1)
        self.diag_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(
            add_frame, text="➕ Add", font=("Segoe UI", 8, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", command=self._add_dialogue_line
        ).pack(side="right")

        # Delete & Restore Buttons
        btn_row = tk.Frame(parent, bg=t["bg_card"])
        btn_row.pack(fill="x")

        tk.Button(
            btn_row, text="🗑️ Delete Selected", font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"], relief="flat", command=self._delete_dialogue_line
        ).pack(side="left")

        tk.Button(
            btn_row, text="Reset to Defaults", font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"], relief="flat", command=self._reset_dialogues
        ).pack(side="right")

        self._refresh_dialogue_list()

    # ── RIGHT PANEL: LIVE PREVIEW & SAVE ──────────────────────────────────────
    def _build_preview_panel(self, parent: tk.Frame):
        t = themes.get()

        tk.Label(
            parent, text="📺 Live Walk Preview", bg=t["bg_card"],
            fg=t["fg_main"], font=("Segoe UI", 10, "bold")
        ).pack(pady=(4, 2))

        # Toggle Walk vs Idle
        toggle_frame = tk.Frame(parent, bg=t["bg_card"])
        toggle_frame.pack(fill="x", pady=(0, 4))
        tk.Button(
            toggle_frame, text="Walk", font=("Segoe UI", 7, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", command=lambda: self._set_preview_mode("walk")
        ).pack(side="left", expand=True, fill="x", padx=1)
        tk.Button(
            toggle_frame, text="Idle", font=("Segoe UI", 7, "bold"),
            bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"], relief="flat", command=lambda: self._set_preview_mode("idle")
        ).pack(side="right", expand=True, fill="x", padx=1)

        # Preview Canvas
        self.preview_canvas = tk.Canvas(
            parent, width=190, height=220, bg="#262626", highlightthickness=1, highlightbackground="#4B5563"
        )
        self.preview_canvas.pack(pady=(0, 10))

        # Bottom Action Buttons
        tk.Button(
            parent, text="✨ Save & Start Walking", font=("Segoe UI", 10, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t["fg_white"], relief="flat", cursor="hand2",
            padx=10, pady=6, command=self._save_and_start
        ).pack(fill="x", pady=(0, 6))

        tk.Button(
            parent, text="Close", font=("Segoe UI", 9, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", cursor="hand2",
            command=self.hide
        ).pack(fill="x")

    # ── EVENT HANDLERS & LOGIC ────────────────────────────────────────────────
    def _set_preview_mode(self, mode: str):
        self._preview_mode = mode

    def _on_face_scale_change(self, val):
        self.cfg["face_scale"] = float(val)

    def _on_face_off_y_change(self, val):
        self.cfg["face_offset_y"] = int(val)

    def _on_char_scale_change(self, val):
        self.cfg["char_scale"] = float(val)

    def _toggle_flip_base(self):
        self.cfg["is_mirror_base"] = not self.cfg.get("is_mirror_base", False)

    def _on_wardrobe_change(self, _=None):
        self.cfg["shirt_style"] = self.shirt_style_var.get()
        self.cfg["pants_style"] = self.pants_style_var.get()

    def _set_shirt_color(self, color_hex: str):
        self.cfg["shirt_color"] = color_hex

    def _set_pants_color(self, color_hex: str):
        self.cfg["pants_color"] = color_hex

    def _on_shoe_change(self, selection: str):
        col = npc_graphics.SHOE_COLORS.get(selection, "#F9FAFB")
        self.cfg["shoe_color"] = col

    def _use_default_face(self):
        self.cropped_head_img = npc_graphics.create_default_face(60)
        self._display_crop_image(npc_graphics.create_default_face(180))

    def _upload_photo(self):
        parent_win = self.win if self.win is not None else self.root
        path = filedialog.askopenfilename(
            parent=parent_win, title="Upload Photo for NPC Face / Body", filetypes=IMAGE_EXTENSIONS
        )
        if path:
            try:
                img = Image.open(path).convert("RGBA")
                self.loaded_image = img
                self._display_crop_image(img)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}", parent=parent_win)

    def _upload_shirt_graphic(self):
        parent_win = self.win if self.win is not None else self.root
        path = filedialog.askopenfilename(
            parent=parent_win, title="Upload Graphic / Logo for Shirt", filetypes=IMAGE_EXTENSIONS
        )
        if path:
            try:
                img = Image.open(path).convert("RGBA")
                self.custom_shirt_img = img
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load shirt graphic: {e}", parent=parent_win)

    def _clear_shirt_graphic(self):
        self.custom_shirt_img = None
        custom_shirt_path = NPC_ASSETS_DIR / "custom_shirt.png"
        if custom_shirt_path.exists():
            try:
                custom_shirt_path.unlink()
            except Exception:
                pass

    def _display_crop_image(self, img: Image.Image):
        cw, ch = 380, 220
        iw, ih = img.size
        scale = min(cw / iw, ch / ih, 1.0)
        self._crop_scale = scale
        disp_w = max(1, int(iw * scale))
        disp_h = max(1, int(ih * scale))
        
        resized = img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        self._crop_img_tk = ImageTk.PhotoImage(resized)

        self.crop_canvas.delete("all")
        # Center image in canvas
        self._crop_offset_x = (cw - disp_w) // 2
        self._crop_offset_y = (ch - disp_h) // 2
        self.crop_canvas.create_image(self._crop_offset_x, self._crop_offset_y, anchor="nw", image=self._crop_img_tk)

        # Draw crop rectangle
        self._crop_rect = [
            self._crop_offset_x + 20,
            self._crop_offset_y + 20,
            self._crop_offset_x + min(120, disp_w - 10),
            self._crop_offset_y + min(120, disp_h - 10),
        ]
        self._draw_crop_marquee()

    def _draw_crop_marquee(self):
        self.crop_canvas.delete("marquee")
        x1, y1, x2, y2 = self._crop_rect
        self.crop_canvas.create_rectangle(
            x1, y1, x2, y2, outline="#38BDF8", width=2, dash=(4, 4), tags="marquee"
        )
        # Inner oval guide for face
        self.crop_canvas.create_oval(
            x1, y1, x2, y2, outline="#F472B6", width=1, dash=(2, 2), tags="marquee"
        )
        # Resize handle
        self.crop_canvas.create_rectangle(
            x2 - 8, y2 - 8, x2, y2, fill="#38BDF8", outline="#FFFFFF", tags="marquee"
        )

    def _on_crop_press(self, event):
        x, y = event.x, event.y
        x1, y1, x2, y2 = self._crop_rect

        # Check if clicking resize handle
        if abs(x - x2) <= 12 and abs(y - y2) <= 12:
            self._drag_mode = "resize"
        elif x1 <= x <= x2 and y1 <= y <= y2:
            self._drag_mode = "move"
        else:
            self._drag_mode = "new"
            self._crop_rect = [x, y, x + 20, y + 20]
        self._drag_start = (x, y)

    def _on_crop_drag(self, event):
        x, y = event.x, event.y
        dx = x - self._drag_start[0]
        dy = y - self._drag_start[1]
        self._drag_start = (x, y)

        if self._drag_mode == "move":
            self._crop_rect[0] += dx
            self._crop_rect[1] += dy
            self._crop_rect[2] += dx
            self._crop_rect[3] += dy
        elif self._drag_mode in ("resize", "new"):
            self._crop_rect[2] = max(self._crop_rect[0] + 30, self._crop_rect[2] + dx)
            self._crop_rect[3] = max(self._crop_rect[1] + 30, self._crop_rect[3] + dy)

        self._draw_crop_marquee()

    def _on_crop_release(self, _=None):
        self._drag_mode = None

    def _apply_crop(self):
        src = self.loaded_image if self.loaded_image is not None else npc_graphics.create_default_face(180)
        
        # Convert crop canvas coordinates to original image coordinates
        x1, y1, x2, y2 = self._crop_rect
        ox1 = max(0, int((x1 - self._crop_offset_x) / self._crop_scale))
        oy1 = max(0, int((y1 - self._crop_offset_y) / self._crop_scale))
        ox2 = min(src.width, int((x2 - self._crop_offset_x) / self._crop_scale))
        oy2 = min(src.height, int((y2 - self._crop_offset_y) / self._crop_scale))

        if ox2 - ox1 < 10 or oy2 - oy1 < 10:
            return

        cropped = src.crop((ox1, oy1, ox2, oy2)).convert("RGBA")
        mask = npc_graphics.create_oval_mask(cropped.width, cropped.height)
        cropped.putalpha(mask)

        self.cropped_head_img = cropped
        parent_win = self.win if (self.win is not None and self.win.winfo_exists()) else self.root
        messagebox.showinfo("Cropped!", "Head cropped successfully! Check the live preview on the right.", parent=parent_win)

    # ── DIALOGUE LISTBOX MANAGEMENT ──────────────────────────────────────────
    def _refresh_dialogue_list(self):
        self.diag_listbox.delete(0, tk.END)
        lines = self.dialogues.get(self.cur_diag_cat, [])
        for line in lines:
            self.diag_listbox.insert(tk.END, line)

    def _add_dialogue_line(self):
        text = self.diag_entry.get().strip()
        if text:
            self.dialogues.setdefault(self.cur_diag_cat, []).append(text)
            self.diag_entry.delete(0, tk.END)
            self._refresh_dialogue_list()

    def _delete_dialogue_line(self):
        sel = self.diag_listbox.curselection()
        if sel:
            idx = sel[0]
            del self.dialogues[self.cur_diag_cat][idx]
            self._refresh_dialogue_list()

    def _reset_dialogues(self):
        if self.cur_diag_cat in DEFAULT_NPC_DIALOGUES:
            self.dialogues[self.cur_diag_cat] = list(DEFAULT_NPC_DIALOGUES[self.cur_diag_cat])
            self._refresh_dialogue_list()

    # ── LIVE PREVIEW TICK LOOP ────────────────────────────────────────────────
    def _start_preview_loop(self):
        self._preview_phase = 0.0
        self._tick_preview()

    def _tick_preview(self):
        if not self.win or not self.win.winfo_exists():
            return

        self._preview_phase += 0.25
        head = self.cropped_head_img if self.cropped_head_img is not None else npc_graphics.create_default_face(60)

        # Composite a frame
        frame_img, (hx, hy) = npc_graphics.compose_full_walker_frame(
            head_img=head,
            frame_type=self._preview_mode,
            walk_phase=self._preview_phase,
            face_scale=float(self.cfg.get("face_scale", 1.0)),
            face_offset_x=int(self.cfg.get("face_offset_x", 0)),
            face_offset_y=int(self.cfg.get("face_offset_y", 0)),
            char_scale=float(self.cfg.get("char_scale", 1.0)),
            is_flipped=False,
            shirt_style=str(self.cfg.get("shirt_style", "Hoodie")),
            shirt_color=str(self.cfg.get("shirt_color", "#1E3A8A")),
            pants_style=str(self.cfg.get("pants_style", "Jeans")),
            pants_color=str(self.cfg.get("pants_color", "#2563EB")),
            shoe_color=str(self.cfg.get("shoe_color", "#F9FAFB")),
            custom_shirt_img=self.custom_shirt_img,
        )

        # Draw live leash indicator connecting to dog placeholder in preview
        pw, ph = 190, 220
        canvas_bg = Image.new("RGBA", (pw, ph), (38, 38, 38, 255))
        
        walker_cx = 60
        walker_cy = ph - frame_img.height - 15
        canvas_bg.paste(frame_img, (walker_cx, walker_cy), frame_img)

        # Dog indicator & Leash in preview
        dog_x, dog_y = 150, ph - 35
        hand_abs_x = walker_cx + hx
        hand_abs_y = walker_cy + hy

        from PIL import ImageDraw
        draw = ImageDraw.Draw(canvas_bg)
        # Draw slack leash arc
        leash_col = self.cfg.get("leash_color", "#8B4513")
        sag = 18 if self._preview_mode == "idle" else 6
        mid_x = (hand_abs_x + dog_x) // 2
        mid_y = (hand_abs_y + dog_y) // 2 + sag
        draw.line([(hand_abs_x, hand_abs_y), (mid_x, mid_y), (dog_x, dog_y)], fill=leash_col, width=2)
        # Mini dog circle placeholder
        draw.ellipse((dog_x - 10, dog_y - 10, dog_x + 10, dog_y + 10), fill="#F59E0B", outline="#FFFFFF", width=1)
        draw.text((dog_x - 8, dog_y - 6), "🐾", fill="#FFFFFF")

        self._preview_tk = ImageTk.PhotoImage(canvas_bg)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, anchor="nw", image=self._preview_tk)

        self._preview_timer = self.root.after(70, self._tick_preview)

    # ── SAVE & LAUNCH ─────────────────────────────────────────────────────────
    def _save_and_start(self):
        try:
            custom_dir = NPC_ASSETS_DIR / "custom"
            head = self.cropped_head_img if self.cropped_head_img is not None else npc_graphics.create_default_face(60)

            # Save head and custom shirt image
            if self.cropped_head_img is not None:
                head_path = NPC_ASSETS_DIR / "custom_face.png"
                head_path.parent.mkdir(parents=True, exist_ok=True)
                self.cropped_head_img.save(head_path, "PNG")

            if self.custom_shirt_img is not None:
                shirt_path = NPC_ASSETS_DIR / "custom_shirt.png"
                shirt_path.parent.mkdir(parents=True, exist_ok=True)
                self.custom_shirt_img.save(shirt_path, "PNG")

            # Generate all animation frames
            anim_set = npc_graphics.generate_full_animation_set(
                head_img=head,
                face_scale=float(self.cfg.get("face_scale", 1.0)),
                face_offset_x=int(self.cfg.get("face_offset_x", 0)),
                face_offset_y=int(self.cfg.get("face_offset_y", 0)),
                char_scale=float(self.cfg.get("char_scale", 1.0)),
                is_mirror_base=bool(self.cfg.get("is_mirror_base", False)),
                shirt_style=str(self.cfg.get("shirt_style", "Hoodie")),
                shirt_color=str(self.cfg.get("shirt_color", "#1E3A8A")),
                pants_style=str(self.cfg.get("pants_style", "Jeans")),
                pants_color=str(self.cfg.get("pants_color", "#2563EB")),
                shoe_color=str(self.cfg.get("shoe_color", "#F9FAFB")),
                custom_shirt_img=self.custom_shirt_img,
            )

            offsets = npc_graphics.export_walker_assets(custom_dir, anim_set)
            with open(custom_dir / "meta.json", "w", encoding="utf-8") as f:
                json.dump(offsets, f, indent=2)

            # Save updated data
            data = self.get_data()
            data["npc_walker"] = dict(self.cfg)
            for cat, lines in self.dialogues.items():
                data[cat] = list(lines)
            self.save_data(data)

            parent_win = self.win if (self.win is not None and self.win.winfo_exists()) else self.root
            messagebox.showinfo("Saved!", "NPC Dog Walker customized successfully! Launching now...", parent=parent_win)
            self.hide()

        except Exception as e:
            parent_win = self.win if (self.win is not None and self.win.winfo_exists()) else self.root
            messagebox.showerror("Error", f"Failed to save walker assets: {e}", parent=parent_win)
            return

        if self.on_save_and_start:
            self.root.after(50, self.on_save_and_start)
