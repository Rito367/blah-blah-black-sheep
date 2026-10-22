"""
npc_walker.py
Desktop NPC Owner Companion Window for DesktopPet.
Walks the pet on a leash with bidirectional facing, destination waypoint navigation,
dragging, auto-patrol, follow cursor, speech bubble, and right-click controls.
"""

from __future__ import annotations
import math
import random
import json
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk, ImageOps

try:
    import paths
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths

import themes

CHROMA = "#010101"

try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_LANCZOS = getattr(Image, "LANCZOS")


class NPCWalkerWindow:
    """The Desktop NPC Owner that walks the pet."""

    def __init__(
        self,
        root: tk.Tk,
        get_data_fn,
        save_data_fn,
        on_bubble=None,
        on_open_customizer=None,
        on_dismiss=None,
    ):
        self.root = root
        self.get_data = get_data_fn
        self.save_data = save_data_fn
        self.on_bubble = on_bubble
        self.on_open_customizer = on_open_customizer
        self.on_dismiss = on_dismiss

        self.sw = root.winfo_screenwidth()
        self.sh = root.winfo_screenheight()

        self.active: bool = False
        self.facing_right: bool = True
        self.current_anim: str = "idle"
        self.frame_index: int = 0

        # Movement state
        self.walk_speed: int = 3
        self.patrol_active: bool = False
        self.follow_cursor: bool = False
        self.target_pos: tuple[int, int] | None = None
        self._speech_timer: str | None = None

        # Drag state
        self._dragging: bool = False
        self._drag_ox: int = 0
        self._drag_oy: int = 0

        # Frame storage: {"idle": [(PhotoImage, (hx, hy)), ...], "walk": [...]}
        self.frames: dict[str, list[tuple[ImageTk.PhotoImage, tuple[int, int]]]] = {}
        self.flipped_frames: dict[str, list[tuple[ImageTk.PhotoImage, tuple[int, int]]]] = {}
        self.sprite_w = 100
        self.sprite_h = 140

        # Bubble window for NPC speech
        self._bubble_win: tk.Toplevel | None = None
        self._bubble_timer: str | None = None

        # Destination Waypoint Marker Window
        self._waypoint_win: tk.Toplevel | None = None
        self._waypoint_phase = 0

        # Build window
        self._build_window()

        # Reload assets from disk
        self.reload_assets()

        # Start loops
        self._anim_timer = None
        self._move_timer = None
        self._dialogue_timer = None
        self._anim_tick()
        self._move_tick()

    def _build_window(self):
        """Builds or rebuilds the transparent walker sprite window."""
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", CHROMA)
        self.win.configure(bg=CHROMA)
        self.win.resizable(False, False)
        self.win.withdraw()
        self.win.protocol("WM_DELETE_WINDOW", self.disable)

        self.canvas = tk.Canvas(
            self.win, width=self.sprite_w, height=self.sprite_h,
            bg=CHROMA, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self._img_item = self.canvas.create_image(
            self.sprite_w // 2, self.sprite_h // 2, anchor="center"
        )

        # Event bindings
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-3>", self._show_context_menu)

    def _ensure_window(self):
        """Ensures the transparent walker sprite window is created and valid."""
        try:
            if not self.win.winfo_exists():
                self._build_window()
        except Exception:
            self._build_window()

    def reload_assets(self):
        try:
            import paths
            base_path = paths.ASSETS_DIR / "npc"
        except ImportError:
            base_path = Path(__file__).resolve().parent.parent / "assets" / "npc"
        custom_dir = base_path / "custom"
        default_dir = base_path / "default"

        char_dir = custom_dir if (custom_dir / "meta.json").exists() else default_dir
        meta_path = char_dir / "meta.json"

        offsets = {}
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    offsets = json.load(f)
            except Exception:
                offsets = {}

        data = self.get_data()
        npc_cfg = data.get("npc_walker", {})
        self.walk_speed = npc_cfg.get("walk_speed", 3)

        self.frames = {"idle": [], "walk": []}
        self.flipped_frames = {"idle": [], "walk": []}

        for anim_name in ("idle", "walk"):
            anim_dir = char_dir / anim_name
            if not anim_dir.exists():
                continue

            frame_files = sorted(anim_dir.glob("*.png"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0)
            anim_offsets = offsets.get(anim_name, [])

            for idx, fpath in enumerate(frame_files):
                try:
                    img = Image.open(fpath).convert("RGBA")
                    self.sprite_w, self.sprite_h = img.size

                    hx, hy = anim_offsets[idx] if idx < len(anim_offsets) else (self.sprite_w - 20, self.sprite_h - 40)

                    # Normal (Facing Right)
                    tk_img = ImageTk.PhotoImage(img)
                    self.frames[anim_name].append((tk_img, (hx, hy)))

                    # Flipped (Facing Left)
                    flipped_img = ImageOps.mirror(img)
                    flipped_tk = ImageTk.PhotoImage(flipped_img)
                    flipped_hx = self.sprite_w - hx
                    self.flipped_frames[anim_name].append((flipped_tk, (flipped_hx, hy)))
                except Exception:
                    pass

        # Update window dimensions
        try:
            if self.win.winfo_exists():
                self.canvas.config(width=self.sprite_w, height=self.sprite_h)
                self.canvas.coords(self._img_item, self.sprite_w // 2, self.sprite_h // 2)
        except Exception:
            pass

    def enable(self, start_x: int | None = None, start_y: int | None = None):
        """Shows and activates the NPC walker on screen."""
        self._ensure_window()
        self.active = True
        self.reload_assets()

        if start_x is None or start_y is None:
            data = self.get_data()
            pet_pos = data.get("pet_position", [self.sw // 2, self.sh - 180])
            start_x = max(20, min(self.sw - self.sprite_w - 20, pet_pos[0] - 120))
            start_y = max(20, min(self.sh - self.sprite_h - 30, pet_pos[1] - (self.sprite_h - 60)))

        try:
            self.win.geometry(f"{self.sprite_w}x{self.sprite_h}+{start_x}+{start_y}")
            self.win.deiconify()
            self.win.lift()
            self.win.attributes("-topmost", True)
        except Exception:
            pass
        self.say(random.choice(self._get_dialogue_pool("npc_walk_messages")))
        if not getattr(self, "_dialogue_timer", None):
            self._dialogue_tick()

    def disable(self):
        """Hides the NPC walker."""
        self.active = False
        dtimer = getattr(self, "_dialogue_timer", None)
        if dtimer is not None:
            try:
                self.root.after_cancel(dtimer)
            except Exception:
                pass
            self._dialogue_timer = None
        try:
            if self.win.winfo_exists():
                self.win.withdraw()
        except Exception:
            pass
        self._hide_waypoint()
        self._hide_bubble()

    def get_hand_screen_position(self) -> tuple[int, int]:
        """Returns the global screen coordinates of the hand holding the leash."""
        if not self.active:
            return (0, 0)
        try:
            if not self.win.winfo_exists():
                return (0, 0)
            wx = self.win.winfo_x()
            wy = self.win.winfo_y()
        except Exception:
            return (0, 0)

        anim = self.current_anim if self.current_anim in self.frames else "idle"
        frame_list = self.frames.get(anim, [])
        if not frame_list:
            return (wx + self.sprite_w // 2, wy + self.sprite_h // 2)

        idx = self.frame_index % len(frame_list)
        if self.facing_right:
            _, (hx, hy) = self.frames[anim][idx]
        else:
            _, (hx, hy) = self.flipped_frames[anim][idx]

        return (wx + hx, wy + hy)

    def get_position(self) -> tuple[int, int]:
        try:
            if self.win.winfo_exists():
                return (self.win.winfo_x(), self.win.winfo_y())
        except Exception:
            pass
        return (0, 0)

    def set_position(self, x: int, y: int):
        try:
            if self.win.winfo_exists():
                self.win.geometry(f"+{x}+{y}")
                self._reposition_bubble()
        except Exception:
            pass

    def move_to(self, target_x: int, target_y: int):
        """Sets a target destination waypoint for the NPC to walk to."""
        self.target_pos = (target_x, target_y)
        self.patrol_active = False
        self.follow_cursor = False
        self._show_waypoint(target_x, target_y)

    def _on_press(self, event):
        self._dragging = False
        self._drag_ox = event.x_root - self.win.winfo_x()
        self._drag_oy = event.y_root - self.win.winfo_y()
        self.target_pos = None

    def _on_drag(self, event):
        self._dragging = True
        new_x = event.x_root - self._drag_ox
        new_y = event.y_root - self._drag_oy
        self.win.geometry(f"+{new_x}+{new_y}")
        self._reposition_bubble()

    def _on_release(self, _=None):
        self._dragging = False

    # ── CONTEXT MENU ─────────────────────────────────────────────────────────
    def _show_context_menu(self, event):
        t = themes.get()
        menu = tk.Menu(
            self.root, tearoff=0,
            bg=t.get("menu_bg", "#ffffff"), fg=t.get("menu_fg", "#333333"),
            activebackground=t.get("menu_active_bg", "#f8bbd0"),
            activeforeground=t.get("menu_active_fg", "#ffffff"),
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0
        )

        menu.add_command(label="📍  Set Destination (Click Screen)", command=self._start_click_destination_mode)
        
        patrol_lbl = "🚶  Auto Patrol  ✓" if self.patrol_active else "🚶  Auto Patrol"
        menu.add_command(label=patrol_lbl, command=self._toggle_patrol)

        follow_lbl = "🖱️  Follow Cursor  ✓" if self.follow_cursor else "🖱️  Follow Cursor"
        menu.add_command(label=follow_lbl, command=self._toggle_follow_cursor)

        menu.add_command(label="🛑  Stay Here", command=self._stop_movement)
        menu.add_separator()
        menu.add_command(label="🎨  Customize Wardrobe & Appearance", command=self._open_customizer)
        menu.add_command(label="❌  Dismiss Owner", command=self._dismiss)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def start_click_destination_mode(self):
        self._start_click_destination_mode()

    def _start_click_destination_mode(self):
        """Creates a transparent full-screen click catcher to pick a destination anywhere."""
        overlay = tk.Toplevel(self.root)
        overlay.attributes("-fullscreen", True)
        overlay.attributes("-alpha", 0.05)
        overlay.attributes("-topmost", True)
        overlay.config(cursor="crosshair")

        def on_click(e):
            dest_x = e.x_root - self.sprite_w // 2
            dest_y = e.y_root - self.sprite_h + 20
            self.move_to(dest_x, dest_y)
            overlay.destroy()

        overlay.bind("<Button-1>", on_click)
        overlay.bind("<Button-3>", lambda e: overlay.destroy())
        overlay.bind("<Escape>", lambda e: overlay.destroy())

    def toggle_patrol(self):
        self._toggle_patrol()

    def _toggle_patrol(self):
        self.patrol_active = not self.patrol_active
        self.follow_cursor = False
        self.target_pos = None

    def toggle_follow_cursor(self):
        self._toggle_follow_cursor()

    def _toggle_follow_cursor(self):
        self.follow_cursor = not self.follow_cursor
        self.patrol_active = False
        self.target_pos = None

    def _stop_movement(self):
        self.target_pos = None
        self.patrol_active = False
        self.follow_cursor = False
        self._hide_waypoint()
        self.current_anim = "idle"

    def _open_customizer(self):
        if self.on_open_customizer:
            self.on_open_customizer()

    def _dismiss(self):
        self.disable()
        if self.on_dismiss:
            self.on_dismiss()

    # ── ANIMATION & MOVEMENT TICK LOOPS ──────────────────────────────────────
    def _anim_tick(self):
        try:
            if self.active and self.win.winfo_exists():
                anim = self.current_anim if self.current_anim in self.frames else "idle"
                frame_list = self.frames.get(anim, [])

                if frame_list:
                    self.frame_index %= len(frame_list)
                    if self.facing_right:
                        photo, _ = self.frames[anim][self.frame_index]
                    else:
                        photo, _ = self.flipped_frames[anim][self.frame_index]

                    self.canvas.itemconfig(self._img_item, image=photo)
                    self.frame_index += 1
        except Exception:
            pass

        self._anim_timer = self.root.after(140 if self.current_anim == "walk" else 200, self._anim_tick)

    def _move_tick(self):
        if not self.active or not self.win.winfo_exists() or self._dragging:
            self._move_timer = self.root.after(50, self._move_tick)
            return

        cur_x = self.win.winfo_x()
        cur_y = self.win.winfo_y()

        is_moving = False

        # 1. Waypoint Destination Mode
        if self.target_pos is not None:
            tx, ty = self.target_pos
            dx = tx - cur_x
            dy = ty - cur_y
            dist = math.hypot(dx, dy)

            if dist > max(6, self.walk_speed):
                is_moving = True
                step = min(self.walk_speed, dist)
                nx = int(cur_x + (dx / dist) * step)
                ny = int(cur_y + (dy / dist) * step)
                self.facing_right = (dx >= 0)
                self.win.geometry(f"+{nx}+{ny}")
            else:
                # Arrived at destination!
                self.target_pos = None
                self._hide_waypoint()
                self.say(random.choice(self._get_dialogue_pool("npc_arrival_messages")))

        # 2. Follow Cursor Mode
        elif self.follow_cursor:
            mx = self.root.winfo_pointerx() - self.sprite_w // 2
            my = self.root.winfo_pointery() - self.sprite_h + 20
            dx = mx - cur_x
            dy = my - cur_y
            dist = math.hypot(dx, dy)

            if dist > 60:
                is_moving = True
                step = min(self.walk_speed, dist)
                nx = int(cur_x + (dx / dist) * step)
                ny = int(cur_y + (dy / dist) * step)
                self.facing_right = (dx >= 0)
                self.win.geometry(f"+{nx}+{ny}")

        # 3. Auto Patrol Mode
        elif self.patrol_active:
            is_moving = True
            step = self.walk_speed if self.facing_right else -self.walk_speed
            nx = cur_x + step

            if nx > self.sw - self.sprite_w - 30:
                self.facing_right = False
            elif nx < 30:
                self.facing_right = True

            self.win.geometry(f"+{nx}+{cur_y}")

        self.current_anim = "walk" if is_moving else "idle"
        if is_moving:
            self._reposition_bubble()
        self._move_timer = self.root.after(35, self._move_tick)

    # ── SPEECH BUBBLE & DIALOGUE ─────────────────────────────────────────────
    def _get_dialogue_pool(self, category: str) -> list[str]:
        data = self.get_data()
        return data.get(category, ["Good doggy!"])

    def say(self, message: str, duration_ms: int = 3500):
        """Displays a speech bubble above the NPC walker."""
        if not self.active or not self.win.winfo_exists():
            return

        self._hide_bubble()

        t = themes.get()
        self._bubble_win = tk.Toplevel(self.root)
        self._bubble_win.overrideredirect(True)
        self._bubble_win.attributes("-topmost", True)
        self._bubble_win.configure(bg=t.get("bubble_bg", "#ffffff"))

        lbl = tk.Label(
            self._bubble_win, text=message,
            bg=t.get("bubble_bg", "#ffffff"), fg=t.get("bubble_fg", "#333333"),
            font=("Segoe UI", 9, "bold"), padx=10, pady=5,
            relief="solid", bd=1, highlightbackground=t.get("bubble_out", "#ffb6c1"),
        )
        lbl.pack()

        self._bubble_win.update_idletasks()
        self._reposition_bubble()

        self._bubble_timer = self.root.after(duration_ms, self._hide_bubble)

    def _reposition_bubble(self):
        if self._bubble_win and self._bubble_win.winfo_exists() and self.win.winfo_exists():
            try:
                bw = self._bubble_win.winfo_width() or 120
                bh = self._bubble_win.winfo_height() or 40
                bx = self.win.winfo_x() + self.sprite_w // 2 - bw // 2
                by = max(10, self.win.winfo_y() - bh - 6)
                self._bubble_win.geometry(f"+{bx}+{by}")
            except Exception:
                pass

    def _hide_bubble(self):
        if self._bubble_timer:
            self.root.after_cancel(self._bubble_timer)
            self._bubble_timer = None
        if self._bubble_win and self._bubble_win.winfo_exists():
            self._bubble_win.destroy()
            self._bubble_win = None

    def _dialogue_tick(self):
        """Periodically triggers casual walking dialogue."""
        self._dialogue_timer = None
        if not self.active:
            return

        if self.current_anim == "walk" and not self._bubble_win:
            if random.random() < 0.25:
                pool = self._get_dialogue_pool("npc_walk_messages")
                if pool:
                    self.say(random.choice(pool))

        self._dialogue_timer = self.root.after(14000, self._dialogue_tick)

    # ── WAYPOINT BEACON ──────────────────────────────────────────────────────
    def _show_waypoint(self, x: int, y: int):
        self._hide_waypoint()
        self._waypoint_win = tk.Toplevel(self.root)
        self._waypoint_win.overrideredirect(True)
        self._waypoint_win.attributes("-topmost", True)
        self._waypoint_win.attributes("-transparentcolor", CHROMA)
        self._waypoint_win.configure(bg=CHROMA)

        wp_size = 40
        wx = x + self.sprite_w // 2 - wp_size // 2
        wy = y + self.sprite_h - wp_size
        self._waypoint_win.geometry(f"{wp_size}x{wp_size}+{wx}+{wy}")

        canvas = tk.Canvas(self._waypoint_win, width=wp_size, height=wp_size, bg=CHROMA, highlightthickness=0)
        canvas.pack()
        # Animated beacon ring and target pin
        canvas.create_oval(4, 20, 36, 36, outline="#38BDF8", width=2)
        canvas.create_oval(10, 24, 30, 32, fill="#0284C7", outline="")
        canvas.create_text(20, 14, text="📍", font=("Segoe UI", 14))

    def _hide_waypoint(self):
        if self._waypoint_win and self._waypoint_win.winfo_exists():
            self._waypoint_win.destroy()
            self._waypoint_win = None
