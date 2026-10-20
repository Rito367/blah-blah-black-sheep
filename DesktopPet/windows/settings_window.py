"""
settings_window.py
Settings window with live previews for sprite scale, menu UI, pet opacity, window opacity,
and full custom color picker for menu background and text.
"""



import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
from pathlib import Path
from typing import Any
from PIL import Image, ImageTk
import themes
import git_sync
import sound_manager
from speech_bubble import BUBBLE_FONTS, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE
from themes import THEME_KEYS, THEME_KEY_LABELS

try:
    import paths
    ASSETS_DIR = paths.ASSETS_DIR
except ImportError:
    ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
BASE_SPRITE_SIZE = 60
PET_PREVIEW_SIZE = 120


class SettingsWindow:
    def __init__(self, root: tk.Tk, get_data, save_data, on_apply=None, on_menu=None, on_password_manager=None):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_apply = on_apply
        self.on_menu  = on_menu
        self.on_password_manager = on_password_manager
        self.win = None

        self._base_img = None
        self._preview_photo = None
        self.menu_colors = {}
        self.pass_enabled_var: tk.BooleanVar | None = None
        self.sec_status_lbl: tk.Label | None = None
        self._sound_list_frame: tk.Frame | None = None
        self._sound_summary_lbl: tk.Label | None = None

    def hide(self):
        try:
            sound_manager.stop_preview()
        except Exception:
            pass
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None

    def show(self, near_x: int = 100, near_y: int = 100):
        if self.win and self.win.winfo_exists():
            self._update_password_status_ui()
            self._render_sound_list()
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        t = themes.get()
        data = self.get_data()

        # Load existing custom colors
        saved_custom = data.get("custom_menu_colors", {})
        self.menu_colors = {
            "menu_bg":        saved_custom.get("menu_bg")        or t.get("menu_bg",        "#ffffff"),
            "menu_fg":        saved_custom.get("menu_fg")        or t.get("menu_fg",        "#333333"),
            "menu_active_bg": saved_custom.get("menu_active_bg") or t.get("menu_active_bg", "#f8bbd0"),
            "menu_active_fg": saved_custom.get("menu_active_fg") or t.get("menu_active_fg", "#ffffff"),
            "bubble_bg":      saved_custom.get("bubble_bg")      or t.get("bubble_bg",      "#ffffff"),
            "bubble_out":     saved_custom.get("bubble_out")     or t.get("bubble_out",     "#ffb6c1"),
            "bubble_fg":      saved_custom.get("bubble_fg")      or t.get("fg_main",        "#333333"),
            "bubble_font_family": saved_custom.get("bubble_font_family") or DEFAULT_FONT_FAMILY,
            "bubble_font_size":   saved_custom.get("bubble_font_size")   or str(DEFAULT_FONT_SIZE),
        }

        self.win = tk.Toplevel(self.root)
        self.win.title("Pet Settings & Custom Menu Colors")
        
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w = 460
        target_h = min(680, sh - 100)
        safe_x = max(20, min(near_x, sw - target_w - 20))
        safe_y = max(20, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("bg_card", "#ffffff"))
        self.win.resizable(False, True)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        current_ui_alpha = data.get("ui_opacity", 1.0)
        self.win.attributes("-alpha", current_ui_alpha)

        # ── header bar ────────────────────────────────────────────────────
        hdr_bg = t.get("bg_hdr", "#ffb6c1")
        hdr = tk.Frame(self.win, bg=hdr_bg, pady=5, padx=10)
        hdr.pack(fill="x", side="top")
        tk.Label(hdr, text="⚙️  Settings", bg=hdr_bg, fg=t.get("fg_white", "#ffffff"),
                 font=("Georgia", 10, "bold")).pack(side="left")
        if self.on_menu:
            mb = tk.Label(hdr, text="☰", bg=hdr_bg, fg=t.get("fg_white", "#ffffff"),
                          font=("Segoe UI", 10, "bold"), cursor="hand2")
            mb.pack(side="right")
            mb.bind("<Button-1>", lambda e: self.on_menu(close_win=self.win, hide_fn=self.hide) if self.on_menu else None)

        # ── Bottom Action Buttons (Always visible) ─────────────────────────
        btn_row = tk.Frame(self.win, bg=t["bg_card"])
        btn_row.pack(side="bottom", fill="x", padx=16, pady=8)

        tk.Button(
            btn_row, text="Cancel", font=("Georgia", 8, "bold"),
            bg=t.get("btn", "#cccccc"), fg=t["fg_white"], relief="flat",
            command=self.hide,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        tk.Button(
            btn_row, text="Save Settings", font=("Georgia", 8, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t["fg_white"], relief="flat",
            command=self._save_and_apply,
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

        # ── Scrollable Body Area ───────────────────────────────────────────
        scroll_outer = tk.Frame(self.win, bg=t["bg_card"])
        scroll_outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_outer, bg=t["bg_card"], highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg=t["bg_card"])
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_content_config(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        content.bind("<Configure>", _on_content_config)

        def _on_canvas_config(e):
            canvas.itemconfig(content_id, width=e.width)
        canvas.bind("<Configure>", _on_canvas_config)

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self.win.bind("<MouseWheel>", _on_wheel)

        # Preview section
        preview_outer = tk.LabelFrame(
            content,
            text=" Live Previews ",
            bg=t["bg_card"],
            fg=t["fg_main"],
            font=("Georgia", 8, "bold"),
            padx=8,
            pady=6,
        )
        preview_outer.pack(fill="x", padx=16, pady=(0, 6))

        preview_grid = tk.Frame(preview_outer, bg=t["bg_card"])
        preview_grid.pack(fill="x")

        # Pet sprite preview
        pet_box = tk.Frame(preview_grid, bg=t["bg_card"])
        pet_box.pack(side="left", fill="both", expand=True, padx=(0, 4))

        tk.Label(
            pet_box, text="Pet Sprite", bg=t["bg_card"],
            fg=t["fg_main"], font=("Georgia", 7, "bold"),
        ).pack(pady=(0, 2))

        self.pet_canvas = tk.Canvas(
            pet_box,
            width=PET_PREVIEW_SIZE,
            height=PET_PREVIEW_SIZE,
            bg=t.get("bg_grid", "#f0f0f0"),
            highlightthickness=1,
            highlightbackground=t.get("btn", "#cccccc"),
        )
        self.pet_canvas.pack(pady=2)

        self.pet_info_lbl = tk.Label(
            pet_box, text="", bg=t["bg_card"],
            fg=t.get("fg_dim", "#888888"), font=("Georgia", 7),
        )
        self.pet_info_lbl.pack()

        # Menu preview
        menu_box = tk.Frame(preview_grid, bg=t["bg_card"])
        menu_box.pack(side="right", fill="both", expand=True, padx=(4, 0))

        tk.Label(
            menu_box, text="Live Menu Preview", bg=t["bg_card"],
            fg=t["fg_main"], font=("Georgia", 7, "bold"),
        ).pack(pady=(0, 2))

        self.menu_sample_frame = tk.Frame(
            menu_box,
            width=PET_PREVIEW_SIZE + 40,
            height=PET_PREVIEW_SIZE,
            bg=self.menu_colors["menu_bg"],
            highlightthickness=1,
            highlightbackground=t.get("btn", "#cccccc"),
        )
        self.menu_sample_frame.pack_propagate(False)
        self.menu_sample_frame.pack(pady=2)

        self.menu_item_1 = tk.Label(
            self.menu_sample_frame, text="🍖  Feed",
            bg=self.menu_colors["menu_bg"], fg=self.menu_colors["menu_fg"],
            anchor="w", padx=6,
        )
        self.menu_item_1.pack(fill="x", padx=4, pady=(4, 1))

        self.menu_item_2 = tk.Label(
            self.menu_sample_frame, text="🐾  Pet Modes",
            bg=self.menu_colors["menu_bg"], fg=self.menu_colors["menu_fg"],
            anchor="w", padx=6,
        )
        self.menu_item_2.pack(fill="x", padx=4, pady=1)

        self.menu_item_3 = tk.Label(
            self.menu_sample_frame, text="⚙️  Hovered Item",
            bg=self.menu_colors["menu_active_bg"], fg=self.menu_colors["menu_active_fg"],
            anchor="w", padx=6,
        )
        self.menu_item_3.pack(fill="x", padx=4, pady=(1, 4))

        self.menu_info_lbl = tk.Label(
            menu_box, text="", bg=t["bg_card"],
            fg=t.get("fg_dim", "#888888"), font=("Georgia", 7),
        )
        self.menu_info_lbl.pack()

        self._load_character_sprite(data.get("character", "pet"))

        # Color picker card
        color_box = tk.LabelFrame(
            content,
            text=" Menu Colors ",
            bg=t["bg_card"],
            fg=t["fg_main"],
            font=("Georgia", 8, "bold"),
            padx=8,
            pady=4,
        )
        color_box.pack(fill="x", padx=16, pady=(0, 4))

        col_grid = tk.Frame(color_box, bg=t["bg_card"])
        col_grid.pack(fill="x")

        # Row 1: Menu BG & Text Color
        self.btn_mbg = tk.Button(
            col_grid, text="Menu BG", font=("Segoe UI", 7, "bold"),
            bg=self.menu_colors["menu_bg"], fg=self._get_contrast_fg(self.menu_colors["menu_bg"]),
            relief="solid", bd=1, command=lambda: self._choose_color("menu_bg")
        )
        self.btn_mbg.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        self.btn_mfg = tk.Button(
            col_grid, text="Text Color", font=("Segoe UI", 7, "bold"),
            bg=self.menu_colors["menu_fg"], fg=self._get_contrast_fg(self.menu_colors["menu_fg"]),
            relief="solid", bd=1, command=lambda: self._choose_color("menu_fg")
        )
        self.btn_mfg.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        # Row 2: Hover BG & Hover Text Color
        self.btn_mabg = tk.Button(
            col_grid, text="Hover BG", font=("Segoe UI", 7, "bold"),
            bg=self.menu_colors["menu_active_bg"], fg=self._get_contrast_fg(self.menu_colors["menu_active_bg"]),
            relief="solid", bd=1, command=lambda: self._choose_color("menu_active_bg")
        )
        self.btn_mabg.grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        self.btn_mafg = tk.Button(
            col_grid, text="Hover Text", font=("Segoe UI", 7, "bold"),
            bg=self.menu_colors["menu_active_fg"], fg=self._get_contrast_fg(self.menu_colors["menu_active_fg"]),
            relief="solid", bd=1, command=lambda: self._choose_color("menu_active_fg")
        )
        self.btn_mafg.grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        col_grid.columnconfigure(0, weight=1)
        col_grid.columnconfigure(1, weight=1)

        tk.Button(
            color_box, text="↺ Reset to Theme Colors", font=("Segoe UI", 7),
            bg=t.get("btn", "#cccccc"), fg=t["fg_white"], relief="flat",
            command=self._reset_menu_colors
        ).pack(fill="x", pady=(2, 2))

        # ── Speech Bubble Colors ──────────────────────────────────────────
        bubble_box = tk.LabelFrame(
            content,
            text=" Speech Bubble ",
            bg=t["bg_card"],
            fg=t["fg_main"],
            font=("Georgia", 8, "bold"),
            padx=8,
            pady=4,
        )
        bubble_box.pack(fill="x", padx=16, pady=(0, 4))

        bubble_row = tk.Frame(bubble_box, bg=t["bg_card"])
        bubble_row.pack(fill="x")

        # ── live bubble preview canvas ────────────────────────────────────
        self.bubble_canvas = tk.Canvas(
            bubble_box, width=200, height=54,
            bg=t.get("bg_grid", "#f0f0f0"),
            highlightthickness=1,
            highlightbackground=t.get("btn", "#cccccc"),
        )
        self.bubble_canvas.pack(pady=(0, 4))
        self._draw_bubble_preview()

        # colour picker buttons
        bub_grid = tk.Frame(bubble_box, bg=t["bg_card"])
        bub_grid.pack(fill="x")

        self.btn_bub_bg = tk.Button(
            bub_grid, text="Bubble BG", font=("Segoe UI", 7, "bold"),
            bg=self.menu_colors["bubble_bg"],
            fg=self._get_contrast_fg(self.menu_colors["bubble_bg"]),
            relief="solid", bd=1, command=lambda: self._choose_color("bubble_bg"),
        )
        self.btn_bub_bg.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        self.btn_bub_out = tk.Button(
            bub_grid, text="Outline", font=("Segoe UI", 7, "bold"),
            bg=self.menu_colors["bubble_out"],
            fg=self._get_contrast_fg(self.menu_colors["bubble_out"]),
            relief="solid", bd=1, command=lambda: self._choose_color("bubble_out"),
        )
        self.btn_bub_out.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        self.btn_bub_fg = tk.Button(
            bub_grid, text="Text Color", font=("Segoe UI", 7, "bold"),
            bg=self.menu_colors["bubble_fg"],
            fg=self._get_contrast_fg(self.menu_colors["bubble_fg"]),
            relief="solid", bd=1, command=lambda: self._choose_color("bubble_fg"),
        )
        self.btn_bub_fg.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        bub_grid.columnconfigure(0, weight=1)
        bub_grid.columnconfigure(1, weight=1)
        bub_grid.columnconfigure(2, weight=1)

        tk.Button(
            bubble_box, text="↺ Reset Bubble to Theme Colors", font=("Segoe UI", 7),
            bg=t.get("btn", "#cccccc"), fg=t["fg_white"], relief="flat",
            command=self._reset_bubble_colors,
        ).pack(fill="x", pady=(2, 2))

        # ── font family picker ────────────────────────────────────────────
        font_row = tk.Frame(bubble_box, bg=t["bg_card"])
        font_row.pack(fill="x", pady=(4, 0))

        tk.Label(
            font_row, text="Font:", bg=t["bg_card"], fg=t["fg_main"],
            font=("Georgia", 8, "bold"), width=6, anchor="w",
        ).pack(side="left")

        self._font_var = tk.StringVar(value=self.menu_colors["bubble_font_family"])
        font_menu = tk.OptionMenu(
            font_row, self._font_var, *BUBBLE_FONTS,
            command=self._on_font_family_change,
        )
        font_menu.config(
            font=("Segoe UI", 8), bg=t.get("bg_card", "#ffffff"),
            fg=t.get("fg_main", "#333333"), relief="solid",
            highlightthickness=0, bd=1, activebackground=t.get("btn", "#f8bbd0"),
        )
        font_menu["menu"].config(
            font=("Segoe UI", 8), bg=t.get("bg_card", "#ffffff"),
            fg=t.get("fg_main", "#333333"),
        )
        font_menu.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # ── font size slider ──────────────────────────────────────────────
        size_row = tk.Frame(bubble_box, bg=t["bg_card"])
        size_row.pack(fill="x", pady=(2, 4))

        tk.Label(
            size_row, text="Size:", bg=t["bg_card"], fg=t["fg_main"],
            font=("Georgia", 8, "bold"), width=6, anchor="w",
        ).pack(side="left")

        saved_size = int(self.menu_colors.get("bubble_font_size") or DEFAULT_FONT_SIZE)
        self.font_size_slider = tk.Scale(
            size_row, from_=7, to=18, resolution=1, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_font_size_change,
        )
        self.font_size_slider.set(saved_size)
        self.font_size_slider.pack(side="left", fill="x", expand=True)

        # ── Custom Theme Editor button ────────────────────────────────────
        cte_frame = tk.Frame(content, bg=t["bg_card"])
        cte_frame.pack(fill="x", padx=16, pady=(0, 4))
        tk.Button(
            cte_frame,
            text="🎨  Edit Custom Theme",
            font=("Georgia", 8, "bold"),
            bg=t.get("bg_hdr", "#ffb6c1"), fg="#ffffff",
            relief="flat", cursor="hand2",
            command=self._open_custom_theme_editor,
        ).pack(fill="x")

        # Sliders Section
        ctrl_frame = tk.Frame(content, bg=t["bg_card"])
        ctrl_frame.pack(fill="both", expand=True, padx=16, pady=2)

        # Pet Scale
        tk.Label(ctrl_frame, text="Pet Size (Scale):", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 8, "bold")).pack(anchor="w")
        self.scale_slider = tk.Scale(
            ctrl_frame, from_=0.5, to=2.5, resolution=0.1, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_scale_change,
        )
        self.scale_slider.set(data.get("scale", 1.0))
        self.scale_slider.pack(fill="x", pady=(0, 2))

        # Menu Scale
        tk.Label(ctrl_frame, text="Menu UI Scale:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 8, "bold")).pack(anchor="w")
        self.menu_scale_slider = tk.Scale(
            ctrl_frame, from_=0.8, to=2.0, resolution=0.1, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_menu_scale_change,
        )
        self.menu_scale_slider.set(data.get("menu_scale", 1.0))
        self.menu_scale_slider.pack(fill="x", pady=(0, 2))

        # Dual Opacity Sliders
        opacity_row = tk.Frame(ctrl_frame, bg=t["bg_card"])
        opacity_row.pack(fill="x", pady=(0, 2))

        pet_op_col = tk.Frame(opacity_row, bg=t["bg_card"])
        pet_op_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Label(pet_op_col, text="Pet Opacity:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 8, "bold")).pack(anchor="w")
        self.pet_opacity_slider = tk.Scale(
            pet_op_col, from_=0.2, to=1.0, resolution=0.05, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_pet_opacity_change,
        )
        self.pet_opacity_slider.set(data.get("pet_opacity", data.get("opacity", 1.0)))
        self.pet_opacity_slider.pack(fill="x")

        ui_op_col = tk.Frame(opacity_row, bg=t["bg_card"])
        ui_op_col.pack(side="right", fill="x", expand=True, padx=(4, 0))
        tk.Label(ui_op_col, text="Windows Opacity:", bg=t["bg_card"], fg=t["fg_main"], font=("Georgia", 8, "bold")).pack(anchor="w")
        self.ui_opacity_slider = tk.Scale(
            ui_op_col, from_=0.3, to=1.0, resolution=0.05, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_ui_opacity_change,
        )
        self.ui_opacity_slider.set(data.get("ui_opacity", 1.0))
        self.ui_opacity_slider.pack(fill="x")

        # ── Physics Section ───────────────────────────────────────────────
        physics_lf = tk.LabelFrame(
            ctrl_frame, text=" Physics & Behaviour ",
            bg=t["bg_card"], fg=t["fg_main"],
            font=("Georgia", 8, "bold"), padx=8, pady=4,
        )
        physics_lf.pack(fill="x", pady=(6, 2))

        # Gravity
        grav_row = tk.Frame(physics_lf, bg=t["bg_card"])
        grav_row.pack(fill="x", pady=(2, 0))
        tk.Label(grav_row, text="Gravity:", bg=t["bg_card"], fg=t["fg_main"],
                 font=("Georgia", 8, "bold"), width=14, anchor="w").pack(side="left")
        tk.Label(grav_row, text="(heavier ►)", bg=t["bg_card"],
                 fg=t.get("fg_dim", "#888888"), font=("Georgia", 7)).pack(side="right")
        self.gravity_slider = tk.Scale(
            physics_lf, from_=0.1, to=4.0, resolution=0.1, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_gravity_change,
        )
        self.gravity_slider.set(data.get("gravity", 1.2))
        self.gravity_slider.pack(fill="x", pady=(0, 4))

        # Bounciness
        bounce_row = tk.Frame(physics_lf, bg=t["bg_card"])
        bounce_row.pack(fill="x", pady=(2, 0))
        tk.Label(bounce_row, text="Bounciness:", bg=t["bg_card"], fg=t["fg_main"],
                 font=("Georgia", 8, "bold"), width=14, anchor="w").pack(side="left")
        tk.Label(bounce_row, text="(bouncier ►)", bg=t["bg_card"],
                 fg=t.get("fg_dim", "#888888"), font=("Georgia", 7)).pack(side="right")
        self.bounce_slider = tk.Scale(
            physics_lf, from_=0.0, to=1.0, resolution=0.05, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_bounce_change,
        )
        self.bounce_slider.set(data.get("bounciness", 0.6))
        self.bounce_slider.pack(fill="x", pady=(0, 4))

        # Walk Speed
        speed_row = tk.Frame(physics_lf, bg=t["bg_card"])
        speed_row.pack(fill="x", pady=(2, 0))
        tk.Label(speed_row, text="Walk Speed:", bg=t["bg_card"], fg=t["fg_main"],
                 font=("Georgia", 8, "bold"), width=14, anchor="w").pack(side="left")
        tk.Label(speed_row, text="(faster ►)", bg=t["bg_card"],
                 fg=t.get("fg_dim", "#888888"), font=("Georgia", 7)).pack(side="right")
        self.walk_speed_slider = tk.Scale(
            physics_lf, from_=1, to=12, resolution=1, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_walk_speed_change,
        )
        self.walk_speed_slider.set(data.get("walk_speed", 2))
        self.walk_speed_slider.pack(fill="x", pady=(0, 4))

        # Chatter Chance
        chat_row = tk.Frame(physics_lf, bg=t["bg_card"])
        chat_row.pack(fill="x", pady=(2, 0))
        tk.Label(chat_row, text="Chatter Chance:", bg=t["bg_card"], fg=t["fg_main"],
                 font=("Georgia", 8, "bold"), width=14, anchor="w").pack(side="left")
        tk.Label(chat_row, text="(more chatty ►)", bg=t["bg_card"],
                 fg=t.get("fg_dim", "#888888"), font=("Georgia", 7)).pack(side="right")
        self.chatter_slider = tk.Scale(
            physics_lf, from_=0.0, to=1.0, resolution=0.05, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_chatter_change,
        )
        self.chatter_slider.set(data.get("chatter_chance", 0.20))
        self.chatter_slider.pack(fill="x", pady=(0, 4))

        # Bomb Fling Force
        fling_row = tk.Frame(physics_lf, bg=t["bg_card"])
        fling_row.pack(fill="x", pady=(2, 0))
        tk.Label(fling_row, text="Bomb Fling Force:", bg=t["bg_card"], fg=t["fg_main"],
                 font=("Georgia", 8, "bold"), width=16, anchor="w").pack(side="left")
        tk.Label(fling_row, text="(stronger fling ►)", bg=t["bg_card"],
                 fg=t.get("fg_dim", "#888888"), font=("Georgia", 7)).pack(side="right")
        self.fling_slider = tk.Scale(
            physics_lf, from_=10.0, to=150.0, resolution=5.0, orient="horizontal",
            bg=t["bg_card"], fg=t["fg_main"], highlightthickness=0,
            command=self._on_bomb_blast_power_change,
        )
        self.fling_slider.set(data.get("bomb_blast_power", 35.0))
        self.fling_slider.pack(fill="x", pady=(0, 2))

        # ── Whip Hit Sounds Section ───────────────────────────────────────
        sound_lf = tk.LabelFrame(
            content,
            text=" 🔊 Whip Hit Sounds (Chance Pool & Duration) ",
            font=("Georgia", 8, "bold"),
            bg=t["bg_card"],
            fg=t.get("fg_main", "#333333"),
            padx=8,
            pady=6,
        )
        sound_lf.pack(fill="x", padx=16, pady=(0, 10))

        self._sound_summary_lbl = tk.Label(
            sound_lf,
            text="Loading sounds...",
            font=("Segoe UI", 8),
            bg=t["bg_card"],
            fg=t.get("fg_dim", "#666666"),
            anchor="w",
        )
        self._sound_summary_lbl.pack(fill="x", pady=(0, 4))

        self._sound_list_frame = tk.Frame(sound_lf, bg=t["bg_card"])
        self._sound_list_frame.pack(fill="x", pady=(0, 6))

        snd_btn_row = tk.Frame(sound_lf, bg=t["bg_card"])
        snd_btn_row.pack(fill="x", pady=(2, 0))

        tk.Button(
            snd_btn_row,
            text="➕ Upload Sound (.wav / .mp3)...",
            font=("Georgia", 8, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t["fg_white"],
            relief="flat",
            cursor="hand2",
            command=self._on_upload_sound,
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        tk.Button(
            snd_btn_row,
            text="🎲 Test Random Strike",
            font=("Georgia", 8, "bold"),
            bg=t.get("btn", "#cccccc"),
            fg=t["fg_white"],
            relief="flat",
            cursor="hand2",
            command=self._on_test_random_sound,
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        self._render_sound_list()

        # ── Menu Password & Security ───────────────────────────────────────
        sec_lf = tk.LabelFrame(
            content,
            text=" 🔐 Menu Password & Security ",
            font=("Georgia", 8, "bold"),
            bg=t["bg_card"],
            fg=t.get("accent", "#e74c3c"),
            padx=10,
            pady=8,
        )
        sec_lf.pack(fill="x", padx=16, pady=(0, 10))

        is_pass_enabled = bool(data.get("menu_password_enabled", True))
        has_pass = bool(str(data.get("menu_password", "")).strip())
        status_text = "🔒 Password Protection: ACTIVE" if (is_pass_enabled and has_pass) else "🔓 Password Protection: DISABLED / NOT SET"
        status_color = "#2e7d32" if (is_pass_enabled and has_pass) else "#757575"

        self.sec_status_lbl = tk.Label(
            sec_lf, text=status_text, bg=t["bg_card"],
            fg=status_color, font=("Segoe UI", 8, "bold")
        )
        self.sec_status_lbl.pack(anchor="w", pady=(2, 4))

        # Direct On/Off Checkbox Toggle
        self.pass_enabled_var = tk.BooleanVar(value=is_pass_enabled)
        chk = tk.Checkbutton(
            sec_lf,
            text="Require password to open menus",
            variable=self.pass_enabled_var,
            font=("Segoe UI", 9, "bold"),
            bg=t["bg_card"],
            fg=t["fg_main"],
            activebackground=t["bg_card"],
            command=self._on_toggle_password_enabled,
        )
        chk.pack(anchor="w", pady=(0, 6))

        tk.Button(
            sec_lf,
            text="⚙️  Set / Change Password...",
            font=("Georgia", 8, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat", cursor="hand2",
            command=self._open_password_manager,
        ).pack(fill="x", pady=(2, 4))

        # ── Reset Everything ──────────────────────────────────────────────
        reset_all_frame = tk.Frame(content, bg=t["bg_card"])
        reset_all_frame.pack(fill="x", padx=16, pady=(0, 12))

        tk.Button(
            reset_all_frame,
            text="↺  Reset ALL to Theme Defaults",
            font=("Georgia", 8, "bold"),
            bg="#e74c3c", fg="#ffffff",
            relief="flat", cursor="hand2",
            command=self._reset_all,
        ).pack(fill="x")

        self._update_pet_preview(self.scale_slider.get())
        self._update_menu_preview(self.menu_scale_slider.get())

        self.win.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        self._bind_mousewheel(self.win, canvas)

    def _bind_mousewheel(self, widget, canvas):
        def _on_wheel(e):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        try:
            widget.bind("<MouseWheel>", _on_wheel, add="+")
        except Exception:
            pass
        for child in widget.winfo_children():
            self._bind_mousewheel(child, canvas)

    def _open_password_manager(self):
        if self.on_password_manager:
            self.on_password_manager()

    def _on_toggle_password_enabled(self) -> None:
        if self.pass_enabled_var is None:
            return
        is_on = self.pass_enabled_var.get()
        data = self.get_data()
        current_pass = str(data.get("menu_password", "")).strip()

        # If turning on but no password set yet, prompt password setup dialog
        if is_on and not current_pass:
            if self.on_password_manager:
                self.on_password_manager()
            self._update_password_status_ui()
            return

        data["menu_password_enabled"] = is_on
        self.save_data(data)
        self._update_password_status_ui()

    def update_password_status_ui(self) -> None:
        self._update_password_status_ui()

    def _update_password_status_ui(self) -> None:
        if self.sec_status_lbl is None or not self.sec_status_lbl.winfo_exists():
            return
        data = self.get_data()
        is_pass_enabled = bool(data.get("menu_password_enabled", True))
        has_pass = bool(str(data.get("menu_password", "")).strip())
        status_text = "🔒 Password Protection: ACTIVE" if (is_pass_enabled and has_pass) else "🔓 Password Protection: DISABLED / NOT SET"
        status_color = "#2e7d32" if (is_pass_enabled and has_pass) else "#757575"
        self.sec_status_lbl.configure(text=status_text, fg=status_color)
        if self.pass_enabled_var is not None:
            self.pass_enabled_var.set(is_pass_enabled)

    def _choose_color(self, color_key: str):
        parent_win: tk.Misc = self.win if self.win is not None else self.root
        chosen = colorchooser.askcolor(
            color=self.menu_colors[color_key],
            title=f"Choose {color_key.replace('_', ' ').title()}",
            parent=parent_win
        )
        if chosen and chosen[1]:
            hex_col = chosen[1]
            self.menu_colors[color_key] = hex_col
            self._update_color_buttons()
            self._update_menu_preview(self.menu_scale_slider.get())
            # refresh bubble preview if a bubble key changed
            if color_key.startswith("bubble_"):
                self._draw_bubble_preview()

    def _get_contrast_fg(self, hex_col: str) -> str:
        try:
            hex_col = hex_col.lstrip("#")
            r, g, b = tuple(int(hex_col[i:i+2], 16) for i in (0, 2, 4))
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return "#000000" if brightness > 140 else "#ffffff"
        except Exception:
            return "#000000"

    def _update_color_buttons(self):
        self.btn_mbg.config(bg=self.menu_colors["menu_bg"],        fg=self._get_contrast_fg(self.menu_colors["menu_bg"]))
        self.btn_mfg.config(bg=self.menu_colors["menu_fg"],        fg=self._get_contrast_fg(self.menu_colors["menu_fg"]))
        self.btn_mabg.config(bg=self.menu_colors["menu_active_bg"], fg=self._get_contrast_fg(self.menu_colors["menu_active_bg"]))
        self.btn_mafg.config(bg=self.menu_colors["menu_active_fg"], fg=self._get_contrast_fg(self.menu_colors["menu_active_fg"]))
        # bubble buttons (may not exist yet during construction)
        if hasattr(self, "btn_bub_bg"):
            self.btn_bub_bg.config(bg=self.menu_colors["bubble_bg"],  fg=self._get_contrast_fg(self.menu_colors["bubble_bg"]))
            self.btn_bub_out.config(bg=self.menu_colors["bubble_out"], fg=self._get_contrast_fg(self.menu_colors["bubble_out"]))
            self.btn_bub_fg.config(bg=self.menu_colors["bubble_fg"],  fg=self._get_contrast_fg(self.menu_colors["bubble_fg"]))

    def _open_custom_theme_editor(self):
        """Opens a dedicated window to edit every colour of the Custom theme."""
        if not (self.win and self.win.winfo_exists()):
            return
        # prevent duplicate windows
        if hasattr(self, "_cte_win") and self._cte_win and self._cte_win.winfo_exists():
            self._cte_win.lift()
            return

        t      = themes.get()
        base_t = dict(themes.THEMES.get("custom", themes.THEMES["pink"]))
        bg     = t.get("bg_card", "#ffffff")
        fg     = t.get("fg_main", "#333333")
        acc    = t.get("accent",  "#e74c3c")
        btn_bg = t.get("btn",     "#f8bbd0")
        hdr_bg = t.get("bg_hdr",  "#ffb6c1")

        cte = tk.Toplevel(self.win)
        cte.title("🎨 Custom Theme Editor")
        cte.geometry(f"360x560+{self.win.winfo_x()+450}+{self.win.winfo_y()}")
        cte.attributes("-topmost", True)
        cte.configure(bg=bg)
        cte.resizable(False, True)
        self._cte_win = cte

        # working copy of custom theme colours
        self._ct_colors = dict(base_t)

        # ── header ────────────────────────────────────────────────────────
        hdr = tk.Frame(cte, bg=hdr_bg, pady=6)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🎨  My Custom Theme", bg=hdr_bg, fg="#ffffff",
                 font=("Georgia", 10, "bold")).pack(side="left", padx=10)

        # ── "copy from theme" dropdown ────────────────────────────────────
        copy_row = tk.Frame(cte, bg=bg)
        copy_row.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(copy_row, text="Start from:", bg=bg, fg=fg,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self._copy_var = tk.StringVar(value="pink")
        src_menu = tk.OptionMenu(copy_row, self._copy_var,
                                 *[n for n in themes.THEME_ORDER if n != "custom"])
        src_menu.config(font=("Segoe UI", 8), bg=bg, fg=fg, relief="solid", bd=1,
                        highlightthickness=0, activebackground=btn_bg)
        src_menu["menu"].config(font=("Segoe UI", 8), bg=bg, fg=fg)
        src_menu.pack(side="left", padx=6)
        tk.Button(copy_row, text="Copy", bg=btn_bg, fg="#ffffff", relief="flat",
                  font=("Segoe UI", 8, "bold"), cursor="hand2",
                  command=lambda: self._copy_theme_to_custom()).pack(side="left")

        # ── scrollable colour swatches ────────────────────────────────────
        scroll_outer = tk.Frame(cte, bg=bg)
        scroll_outer.pack(fill="both", expand=True, padx=8, pady=4)

        canvas = tk.Canvas(scroll_outer, bg=bg, highlightthickness=0)
        sb = tk.Scrollbar(scroll_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=bg)
        fid = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(fid, width=e.width))

        self._ct_btns = {}
        for key in THEME_KEYS:
            label = THEME_KEY_LABELS.get(key, key)
            row = tk.Frame(inner, bg=bg)
            row.pack(fill="x", pady=1, padx=4)

            btn = tk.Button(
                row, text=label,
                font=("Segoe UI", 8),
                bg=self._ct_colors.get(key, "#ffffff"),
                fg=self._get_contrast_fg(self._ct_colors.get(key, "#ffffff")),
                relief="solid", bd=1, anchor="w",
                cursor="hand2",
                command=lambda k=key: self._pick_custom_color(k),
            )
            btn.pack(fill="x")
            self._ct_btns[key] = btn

        # ── save / cancel ─────────────────────────────────────────────────
        btn_row = tk.Frame(cte, bg=bg)
        btn_row.pack(fill="x", padx=12, pady=8)
        tk.Button(btn_row, text="Cancel", bg=btn_bg, fg="#ffffff", relief="flat",
                  font=("Segoe UI", 8, "bold"),
                  command=cte.destroy).pack(side="left", expand=True, fill="x", padx=(0, 4))
        tk.Button(btn_row, text="💾 Save Custom Theme", bg=acc, fg="#ffffff", relief="flat",
                  font=("Segoe UI", 8, "bold"),
                  command=self._save_custom_theme).pack(side="right", expand=True, fill="x", padx=(4, 0))

    def _pick_custom_color(self, key: str):
        chosen = colorchooser.askcolor(
            color=self._ct_colors.get(key, "#ffffff"),
            title=f"Choose: {THEME_KEY_LABELS.get(key, key)}",
            parent=self._cte_win,
        )
        if chosen and chosen[1]:
            self._ct_colors[key] = chosen[1]
            btn = self._ct_btns.get(key)
            if btn:
                btn.config(bg=chosen[1], fg=self._get_contrast_fg(chosen[1]))

    def _copy_theme_to_custom(self):
        src = self._copy_var.get()
        src_data = themes.THEMES.get(src, themes.THEMES["pink"])
        self._ct_colors = dict(src_data)
        for key, btn in self._ct_btns.items():
            col = self._ct_colors.get(key, "#ffffff")
            btn.config(bg=col, fg=self._get_contrast_fg(col))

    def _save_custom_theme(self):
        # write into the live THEMES dict
        themes.set_custom_theme_data(self._ct_colors)
        # persist to pet_data.json
        data = self.get_data()
        data["custom_theme"] = dict(self._ct_colors)
        self.save_data(data)
        if self.on_apply:
            self.on_apply(custom_theme=dict(self._ct_colors))
        if hasattr(self, "_cte_win") and self._cte_win.winfo_exists():
            self._cte_win.destroy()

    def _reset_all(self):
        """Reset every colour, font, and slider back to the current theme's defaults."""
        t = themes.get()

        # Reset colours to empty strings — means "use theme default, no override"
        self.menu_colors = {
            "menu_bg":            "",
            "menu_fg":            "",
            "menu_active_bg":     "",
            "menu_active_fg":     "",
            "bubble_bg":          "",
            "bubble_out":         "",
            "bubble_fg":          "",
            "bubble_font_family": "",
            "bubble_font_size":   "",
        }

        # Update the picker buttons to show the theme's actual colours
        # (even though we'll save "" for them)
        self.menu_colors["menu_bg"]        = t.get("menu_bg",        "#ffffff")
        self.menu_colors["menu_fg"]        = t.get("menu_fg",        "#333333")
        self.menu_colors["menu_active_bg"] = t.get("menu_active_bg", "#f8bbd0")
        self.menu_colors["menu_active_fg"] = t.get("menu_active_fg", "#ffffff")
        self.menu_colors["bubble_bg"]      = t.get("bubble_bg",      "#ffffff")
        self.menu_colors["bubble_out"]     = t.get("bubble_out",     "#ffb6c1")
        self.menu_colors["bubble_fg"]      = t.get("fg_main",        "#333333")
        self.menu_colors["bubble_font_family"] = DEFAULT_FONT_FAMILY
        self.menu_colors["bubble_font_size"]   = str(DEFAULT_FONT_SIZE)

        # ── font picker widgets ───────────────────────────────────────────
        if hasattr(self, "_font_var"):
            self._font_var.set(DEFAULT_FONT_FAMILY)
        if hasattr(self, "font_size_slider"):
            self.font_size_slider.set(DEFAULT_FONT_SIZE)

        # ── sliders ───────────────────────────────────────────────────────
        if hasattr(self, "scale_slider"):
            self.scale_slider.set(1.0)
            self._update_pet_preview(1.0)

        if hasattr(self, "menu_scale_slider"):
            self.menu_scale_slider.set(1.0)

        if hasattr(self, "pet_opacity_slider"):
            self.pet_opacity_slider.set(1.0)

        if hasattr(self, "ui_opacity_slider"):
            self.ui_opacity_slider.set(1.0)
            if self.win and self.win.winfo_exists():
                self.win.attributes("-alpha", 1.0)

        # ── physics sliders ───────────────────────────────────────────────
        if hasattr(self, "gravity_slider"):
            self.gravity_slider.set(1.2)

        if hasattr(self, "bounce_slider"):
            self.bounce_slider.set(0.6)

        if hasattr(self, "walk_speed_slider"):
            self.walk_speed_slider.set(2)

        if hasattr(self, "chatter_slider"):
            self.chatter_slider.set(0.20)

        if hasattr(self, "fling_slider"):
            self.fling_slider.set(35.0)

        # Single batched apply — saves to disk only once
        if self.on_apply:
            self.on_apply(
                scale=1.0, menu_scale=1.0,
                pet_opacity=1.0, ui_opacity=1.0,
                gravity=1.2, bounciness=0.6,
                walk_speed=2, chatter_chance=0.20,
                bomb_blast_power=35.0,
            )

        # ── refresh all previews ──────────────────────────────────────────
        self._update_color_buttons()
        self._update_menu_preview(1.0)
        self._draw_bubble_preview()

    def _reset_menu_colors(self):
        t = themes.get()
        self.menu_colors.update({
            "menu_bg":        t.get("bg_card",       "#ffffff"),
            "menu_fg":        t.get("fg_main",        "#333333"),
            "menu_active_bg": t.get("btn",            "#f8bbd0"),
            "menu_active_fg": t.get("fg_white",       "#ffffff"),
        })
        self._update_color_buttons()
        self._update_menu_preview(self.menu_scale_slider.get())

    def _reset_bubble_colors(self):
        t = themes.get()
        self.menu_colors.update({
            "bubble_bg":  t.get("bubble_bg",  "#ffffff"),
            "bubble_out": t.get("bubble_out", "#ffb6c1"),
            "bubble_fg":  t.get("fg_main",    "#333333"),
            "bubble_font_family": DEFAULT_FONT_FAMILY,
            "bubble_font_size":   str(DEFAULT_FONT_SIZE),
        })
        if hasattr(self, "_font_var"):
            self._font_var.set(DEFAULT_FONT_FAMILY)
        if hasattr(self, "font_size_slider"):
            self.font_size_slider.set(DEFAULT_FONT_SIZE)
        self._update_color_buttons()
        self._draw_bubble_preview()

    def _on_font_family_change(self, value: Any = None):
        family = str(value.get() if hasattr(value, "get") else value)
        self.menu_colors["bubble_font_family"] = family
        self._draw_bubble_preview()

    def _on_font_size_change(self, value):
        self.menu_colors["bubble_font_size"] = str(int(float(value)))
        self._draw_bubble_preview()

    def _draw_bubble_preview(self):
        """Draw a small comic-bubble mockup using the current bubble colours and font."""
        if not hasattr(self, "bubble_canvas"):
            return
        c = self.bubble_canvas
        c.delete("all")

        bg  = self.menu_colors["bubble_bg"]
        out = self.menu_colors["bubble_out"]
        fg  = self.menu_colors["bubble_fg"]
        fam = self.menu_colors.get("bubble_font_family") or DEFAULT_FONT_FAMILY
        fsz = int(self.menu_colors.get("bubble_font_size") or DEFAULT_FONT_SIZE)
        # clamp preview font size so it fits the small canvas
        preview_fsz = max(7, min(fsz, 11))

        W, H   = 200, 54
        bw, bh = 160, 36
        x0     = (W - bw) // 2
        y0     = 4
        r      = 8
        TAIL   = 8

        # rounded rect body
        pts = [
            x0+r, y0,   x0+bw-r, y0,
            x0+bw, y0,  x0+bw, y0+r,
            x0+bw, y0+bh-r, x0+bw, y0+bh,
            x0+bw-r, y0+bh, x0+r, y0+bh,
            x0, y0+bh, x0, y0+bh-r,
            x0, y0+r,  x0, y0,
            x0+r, y0,
        ]
        c.create_polygon(pts, smooth=True, fill=bg, outline=out, width=2)

        # tail
        mid = x0 + bw // 2
        c.create_polygon(
            mid-5, y0+bh,
            mid+5, y0+bh,
            mid,   y0+bh+TAIL,
            fill=bg, outline=out, width=2,
        )
        # cover seam on tail
        c.create_rectangle(mid-4, y0+bh-1, mid+4, y0+bh+1, fill=bg, outline=bg)

        # sample text
        c.create_text(
            W // 2, y0 + bh // 2,
            text="♡ Keep going! ♡",
            fill=fg, font=(fam, preview_fsz, "bold"),
        )

    def _load_character_sprite(self, char_name: str):
        char_dir = ASSETS_DIR / char_name / "idle"
        if not char_dir.exists():
            char_dir = ASSETS_DIR / "pet" / "idle"

        img_file = None
        if char_dir.exists():
            pngs = sorted(char_dir.glob("*.png"))
            if pngs:
                img_file = pngs[0]

        if img_file and img_file.exists():
            try:
                self._base_img = Image.open(img_file).convert("RGBA")
            except Exception:
                self._base_img = None
        else:
            self._base_img = None

    def _on_scale_change(self, val):
        try:
            scale_val = float(val)
            self._update_pet_preview(scale_val)
            if self.on_apply:
                self.on_apply(scale=scale_val)
        except ValueError:
            pass

    def _on_menu_scale_change(self, val):
        try:
            menu_scale_val = float(val)
            self._update_menu_preview(menu_scale_val)
            if self.on_apply:
                self.on_apply(menu_scale=menu_scale_val)
        except ValueError:
            pass

    def _on_pet_opacity_change(self, val):
        try:
            opacity_val = float(val)
            if self.on_apply:
                self.on_apply(pet_opacity=opacity_val)
        except ValueError:
            pass

    def _on_ui_opacity_change(self, val):
        try:
            ui_opacity_val = float(val)
            if self.win and self.win.winfo_exists():
                self.win.attributes("-alpha", ui_opacity_val)
            if self.on_apply:
                self.on_apply(ui_opacity=ui_opacity_val)
        except ValueError:
            pass

    def _on_gravity_change(self, val):
        try:
            v = float(val)
            if self.on_apply:
                self.on_apply(gravity=v)
        except ValueError:
            pass

    def _on_bounce_change(self, val):
        try:
            v = float(val)
            if self.on_apply:
                self.on_apply(bounciness=v)
        except ValueError:
            pass

    def _on_walk_speed_change(self, val):
        try:
            v = int(float(val))
            if self.on_apply:
                self.on_apply(walk_speed=v)
        except ValueError:
            pass

    def _on_chatter_change(self, val):
        try:
            v = float(val)
            if self.on_apply:
                self.on_apply(chatter_chance=v)
        except ValueError:
            pass

    def _on_bomb_blast_power_change(self, val):
        try:
            v = float(val)
            if self.on_apply:
                self.on_apply(bomb_blast_power=v)
        except ValueError:
            pass

    def _update_pet_preview(self, scale_val: float):
        self.pet_canvas.delete("all")
        px_size = max(10, int(BASE_SPRITE_SIZE * scale_val))
        center = PET_PREVIEW_SIZE // 2

        if self._base_img:
            resized = self._base_img.resize((px_size, px_size), Image.Resampling.LANCZOS)
            self._preview_photo = ImageTk.PhotoImage(resized)
            self.pet_canvas.create_image(center, center, image=self._preview_photo)
        else:
            half = px_size // 2
            self.pet_canvas.create_rectangle(
                center - half, center - half, center + half, center + half,
                fill="#ffb6c1", outline="#e74c3c", width=2,
            )
            self.pet_canvas.create_text(
                center, center, text="🐾", font=("Segoe UI", max(8, int(14 * scale_val))),
            )

        self.pet_info_lbl.config(text=f"{px_size} × {px_size} px ({scale_val:.1f}x)")

    def _update_menu_preview(self, menu_scale: float):
        font_size = max(7, int(9 * menu_scale))
        pad_y = max(1, int(2 * menu_scale))
        font_cfg = ("Segoe UI", font_size)

        self.menu_sample_frame.config(bg=self.menu_colors["menu_bg"])

        self.menu_item_1.config(
            font=font_cfg, pady=pad_y,
            bg=self.menu_colors["menu_bg"], fg=self.menu_colors["menu_fg"]
        )
        self.menu_item_2.config(
            font=font_cfg, pady=pad_y,
            bg=self.menu_colors["menu_bg"], fg=self.menu_colors["menu_fg"]
        )
        self.menu_item_3.config(
            font=font_cfg, pady=pad_y,
            bg=self.menu_colors["menu_active_bg"], fg=self.menu_colors["menu_active_fg"]
        )

        self.menu_info_lbl.config(text=f"Font: {font_size} pt ({menu_scale:.1f}x)")

    def _save_and_apply(self):
        data = self.get_data()
        scale          = self.scale_slider.get()
        menu_scale     = self.menu_scale_slider.get()
        pet_opacity    = self.pet_opacity_slider.get()
        ui_opacity     = self.ui_opacity_slider.get()
        gravity        = self.gravity_slider.get()
        bounciness     = self.bounce_slider.get()
        walk_speed       = int(self.walk_speed_slider.get())
        chatter_chance   = self.chatter_slider.get()
        bomb_blast_power = self.fling_slider.get() if hasattr(self, "fling_slider") else 35.0

        data["scale"]            = scale
        data["menu_scale"]       = menu_scale
        data["pet_opacity"]      = pet_opacity
        data["ui_opacity"]       = ui_opacity
        data["gravity"]          = gravity
        data["bounciness"]       = bounciness
        data["walk_speed"]       = walk_speed
        data["chatter_chance"]   = chatter_chance
        data["bomb_blast_power"] = bomb_blast_power

        # Only save colour/font overrides that the user explicitly changed.
        # Compare against the active theme's own defaults — identical values
        # are stored as "" so they don't shadow a future theme switch.
        t_defaults = themes.THEMES.get(themes.current_name(), themes.THEMES["pink"])
        clean_colors: dict = {}
        for key, val in self.menu_colors.items():
            if not val:
                clean_colors[key] = ""
                continue
            # font keys have no theme default — always save them if set
            if key in ("bubble_font_family", "bubble_font_size"):
                clean_colors[key] = val
                continue
            # map colour key → theme key name
            theme_key = {
                "menu_bg": "menu_bg", "menu_fg": "menu_fg",
                "menu_active_bg": "menu_active_bg", "menu_active_fg": "menu_active_fg",
                "bubble_bg": "bubble_bg", "bubble_out": "bubble_out",
                "bubble_fg": "fg_main",
            }.get(key, key)
            default_val = t_defaults.get(theme_key, "")
            clean_colors[key] = "" if val.lower() == default_val.lower() else val

        data["custom_menu_colors"] = clean_colors
        self.save_data(data)
        git_sync.push_to_github_async(commit_msg="Update pet settings & menu colors")

        if self.on_apply:
            self.on_apply(
                scale=scale,
                menu_scale=menu_scale,
                pet_opacity=pet_opacity,
                ui_opacity=ui_opacity,
                gravity=gravity,
                bounciness=bounciness,
                walk_speed=walk_speed,
                chatter_chance=chatter_chance,
                bomb_blast_power=bomb_blast_power,
                custom_menu_colors=clean_colors,
            )

        self.hide()

    # ── Whip Sound Effects Manager ──────────────────────────────────────
    def _render_sound_list(self):
        if not self._sound_list_frame or not self._sound_list_frame.winfo_exists():
            return

        for child in self._sound_list_frame.winfo_children():
            child.destroy()

        t = themes.get()
        sounds = sound_manager.get_hit_sounds()
        total_sounds = len(sounds)

        if self._sound_summary_lbl and self._sound_summary_lbl.winfo_exists():
            chance_txt = f"{sounds[0].chance_percent}%" if sounds else "0%"
            self._sound_summary_lbl.config(
                text=f"Total: {total_sounds} sounds in pool  •  Chance: {chance_txt} each (1 in {total_sounds})"
            )

        if not sounds:
            tk.Label(
                self._sound_list_frame,
                text="No hit sounds found in assets/ folder.",
                font=("Segoe UI", 8, "italic"),
                bg=t["bg_card"],
                fg=t.get("fg_dim", "#888888"),
            ).pack(pady=4)
            return

        for s in sounds:
            row_frame = tk.Frame(
                self._sound_list_frame,
                bg=t.get("bg_grid", "#f7f7f7"),
                highlightthickness=1,
                highlightbackground=t.get("btn", "#e0e0e0"),
                padx=8,
                pady=6,
            )
            row_frame.pack(fill="x", pady=3)

            # Top Row: Icon + Name + Chance badge + Action buttons
            top_row = tk.Frame(row_frame, bg=t.get("bg_grid", "#f7f7f7"))
            top_row.pack(fill="x")

            name_box = tk.Frame(top_row, bg=t.get("bg_grid", "#f7f7f7"))
            name_box.pack(side="left", fill="x", expand=True)

            tk.Label(
                name_box,
                text=f"🎵 {s.display_name}",
                font=("Georgia", 8, "bold"),
                bg=t.get("bg_grid", "#f7f7f7"),
                fg=t["fg_main"],
                anchor="w",
            ).pack(anchor="w")

            tk.Label(
                name_box,
                text=s.filename,
                font=("Segoe UI", 7),
                bg=t.get("bg_grid", "#f7f7f7"),
                fg=t.get("fg_dim", "#888888"),
                anchor="w",
            ).pack(anchor="w")

            # Chance badge
            tk.Label(
                top_row,
                text=f"🎯 {s.chance_percent}%",
                font=("Segoe UI", 8, "bold"),
                bg=t.get("bg_card", "#ffffff"),
                fg=t.get("accent", "#e74c3c"),
                padx=6,
                pady=2,
                relief="solid",
                bd=1,
            ).pack(side="right", padx=(4, 0))

            # Delete button (if not default)
            if not s.is_default:
                del_btn = tk.Button(
                    top_row,
                    text="🗑",
                    font=("Segoe UI", 8),
                    bg=t.get("bg_grid", "#f7f7f7"),
                    fg="#c0392b",
                    relief="flat",
                    cursor="hand2",
                    command=lambda p=s.path, fn=s.filename: self._on_delete_sound(p, fn),
                )
                del_btn.pack(side="right", padx=(2, 4))
            else:
                tk.Label(
                    top_row,
                    text="🔒 Base",
                    font=("Segoe UI", 7),
                    bg=t.get("bg_grid", "#f7f7f7"),
                    fg=t.get("fg_dim", "#888888"),
                ).pack(side="right", padx=(2, 4))

            # Preview button
            is_cur_playing = sound_manager.is_preview_playing(s.filename)
            play_btn = tk.Button(
                top_row,
                text="⏹ Stop" if is_cur_playing else "▶ Play",
                font=("Segoe UI", 7, "bold"),
                bg=t.get("accent", "#e74c3c") if is_cur_playing else t.get("btn", "#cccccc"),
                fg=t["fg_white"],
                relief="flat",
                cursor="hand2",
                width=6,
                command=lambda sound_obj=s: self._on_toggle_preview(sound_obj),
            )
            play_btn.pack(side="right", padx=2)

            # Bottom Row: Duration selector
            dur_row = tk.Frame(row_frame, bg=t.get("bg_grid", "#f7f7f7"))
            dur_row.pack(fill="x", pady=(4, 0))

            tk.Label(
                dur_row,
                text="⏱ Duration:",
                font=("Segoe UI", 7, "bold"),
                bg=t.get("bg_grid", "#f7f7f7"),
                fg=t["fg_main"],
            ).pack(side="left", padx=(0, 4))

            cur_dur_val = s.duration
            if cur_dur_val == 0.0:
                cur_dur_label = "Full Sound"
            elif cur_dur_val == int(cur_dur_val):
                cur_dur_label = f"{int(cur_dur_val)}.0s"
            else:
                cur_dur_label = f"{cur_dur_val:.1f}s"

            dur_options = [
                "Full Sound",
                "0.5s",
                "1.0s",
                "1.5s",
                "2.0s",
                "2.5s",
                "3.0s",
                "4.0s",
                "5.0s",
                "Custom...",
            ]

            if cur_dur_label not in dur_options and cur_dur_label != "Custom...":
                dur_options.insert(len(dur_options) - 1, cur_dur_label)

            dur_var = tk.StringVar(value=cur_dur_label)
            dur_menu = tk.OptionMenu(
                dur_row,
                dur_var,
                *dur_options,
                command=lambda val, fname=s.filename, cur_val=s.duration: self._on_change_sound_duration(fname, str(val), cur_val),
            )
            dur_menu.config(
                font=("Segoe UI", 7),
                bg=t.get("bg_card", "#ffffff"),
                fg=t.get("fg_main", "#333333"),
                relief="solid",
                bd=1,
                padx=4,
                pady=1,
                highlightthickness=0,
            )
            dur_menu["menu"].config(
                font=("Segoe UI", 8),
                bg=t.get("bg_card", "#ffffff"),
                fg=t.get("fg_main", "#333333"),
            )
            dur_menu.pack(side="left")

            desc_text = "plays complete audio" if cur_dur_val == 0 else f"cuts off after {cur_dur_label}"
            tk.Label(
                dur_row,
                text=f"({desc_text})",
                font=("Segoe UI", 7, "italic"),
                bg=t.get("bg_grid", "#f7f7f7"),
                fg=t.get("fg_dim", "#888888"),
            ).pack(side="left", padx=4)

    def _on_toggle_preview(self, sound_obj: sound_manager.HitSoundInfo):
        if sound_manager.is_preview_playing(sound_obj.filename):
            sound_manager.stop_preview()
            self._render_sound_list()
        else:
            def _on_finish():
                if self.win and self.win.winfo_exists():
                    self._render_sound_list()

            sound_manager.play_preview(
                sound_obj.path,
                duration_sec=sound_obj.duration,
                tk_root=self.win,
                on_stop=_on_finish,
            )
            self._render_sound_list()

    def _on_change_sound_duration(self, filename: str, selected_val: str, cur_val: float):
        parent_win = self.win if (self.win and self.win.winfo_exists()) else self.root
        if selected_val == "Full Sound":
            sound_manager.set_sound_duration(filename, 0.0)
        elif selected_val == "Custom...":
            new_sec = simpledialog.askfloat(
                "Custom Sound Duration",
                f"Enter playback duration in seconds for '{filename}':\n(Enter 0 for Full Sound)",
                initialvalue=cur_val if cur_val > 0 else 1.0,
                minvalue=0.0,
                maxvalue=60.0,
                parent=parent_win,
            )
            if new_sec is not None:
                sound_manager.set_sound_duration(filename, new_sec)
        else:
            try:
                sec = float(selected_val.rstrip("s"))
                sound_manager.set_sound_duration(filename, sec)
            except ValueError:
                pass

        sound_manager.stop_preview()
        self._render_sound_list()

    def _on_delete_sound(self, sound_path: Path, sound_name: str):
        parent_win = self.win if (self.win and self.win.winfo_exists()) else self.root
        confirm = messagebox.askyesno(
            "Delete Sound",
            f"Are you sure you want to remove '{sound_name}'?\n\nIt will be removed from the whip sound pool.",
            parent=parent_win,
        )
        if confirm:
            success = sound_manager.delete_custom_sound(sound_path)
            if success:
                self._render_sound_list()
            else:
                messagebox.showerror("Error", f"Failed to delete '{sound_name}'.", parent=parent_win)

    def _on_upload_sound(self):
        parent_win = self.win if (self.win and self.win.winfo_exists()) else self.root
        filetypes = [
            ("Audio Files", "*.wav;*.mp3;*.ogg;*.m4a"),
            ("WAV Audio (*.wav)", "*.wav"),
            ("MP3 Audio (*.mp3)", "*.mp3"),
            ("All Files (*.*)", "*.*"),
        ]
        selected = filedialog.askopenfilename(
            parent=parent_win,
            title="Upload Custom Whip Sound",
            filetypes=filetypes,
        )
        if not selected:
            return

        try:
            new_info = sound_manager.add_custom_sound(selected)
            self._render_sound_list()
            messagebox.showinfo(
                "Sound Uploaded!",
                f"Added '{new_info.filename}' to whip sound pool!\n\n"
                f"🎯 Chance: {new_info.chance_percent}% (1 in {len(sound_manager.get_hit_sounds())})\n"
                f"⏱ Duration: Full Sound (you can adjust this in the list)",
                parent=parent_win,
            )
        except Exception as err:
            messagebox.showerror("Upload Failed", str(err), parent=parent_win)

    def _on_test_random_sound(self):
        parent_win = self.win if (self.win and self.win.winfo_exists()) else self.root
        hit = sound_manager.get_random_hit_sound()
        if not hit:
            messagebox.showinfo("No Sounds", "No hit sounds available in pool.", parent=parent_win)
            return

        path, duration = hit

        def _on_finish():
            if self.win and self.win.winfo_exists():
                self._render_sound_list()

        sound_manager.play_preview(path, duration_sec=duration, tk_root=self.win, on_stop=_on_finish)
        self._render_sound_list()