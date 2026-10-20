"""
npc_leash.py
Interactive Leash Overlay and Tether Physics Engine connecting NPC Owner to Pet.
Renders real-time catenary sag when slack, straight taut tension when walking,
and physically leads/pulls the pet dog along at the leash perimeter.
"""

from __future__ import annotations
import math
import tkinter as tk
from typing import Callable

CHROMA = "#020202"


class NPCLeashOverlay:
    """Full-screen click-through transparent canvas overlay rendering the dynamic leash."""

    def __init__(
        self,
        root: tk.Tk,
        get_hand_fn: Callable[[], tuple[int, int]],
        get_collar_fn: Callable[[], tuple[int, int]],
        pull_pet_fn: Callable[[int, int, bool], None],
        get_config_fn: Callable[[], dict],
        on_pull_dialogue_fn=None,
    ):
        self.root = root
        self.get_hand = get_hand_fn
        self.get_collar = get_collar_fn
        self.pull_pet = pull_pet_fn
        self.get_config = get_config_fn
        self.on_pull_dialogue = on_pull_dialogue_fn

        self.sw = root.winfo_screenwidth()
        self.sh = root.winfo_screenheight()

        self.active: bool = False
        self._loop_timer: str | None = None
        self._taut_ticks: int = 0
        self._last_pull_speech = 0.0

        self._build_window()

    def _build_window(self):
        """Builds or rebuilds the fullscreen transparent leash canvas overlay window."""
        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", CHROMA)
        self.win.configure(bg=CHROMA)
        self.win.geometry(f"{self.sw}x{self.sh}+0+0")
        self.win.withdraw()
        self.win.protocol("WM_DELETE_WINDOW", self.disable)

        self.canvas = tk.Canvas(
            self.win, width=self.sw, height=self.sh,
            bg=CHROMA, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self._make_click_through(self.win)

    def _ensure_window(self):
        """Ensures the fullscreen transparent leash canvas window is created and valid."""
        try:
            if not self.win.winfo_exists():
                self._build_window()
        except Exception:
            self._build_window()

    def _make_click_through(self, toplevel: tk.Toplevel):
        """Enables WS_EX_TRANSPARENT on Windows so mouse clicks pass right through the leash overlay."""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(toplevel.winfo_id())
            if not hwnd:
                hwnd = toplevel.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        except Exception:
            pass

    def enable(self):
        self._ensure_window()
        self.active = True
        try:
            self.win.deiconify()
            self.win.lift()
            self.win.attributes("-topmost", True)
        except Exception:
            pass
        if not self._loop_timer:
            self._tick()

    def disable(self):
        self.active = False
        if self._loop_timer:
            try:
                self.root.after_cancel(self._loop_timer)
            except Exception:
                pass
            self._loop_timer = None
        try:
            if self.win.winfo_exists():
                self.canvas.delete("all")
                self.win.withdraw()
        except Exception:
            pass

    def _tick(self):
        self._loop_timer = None
        if not self.active:
            return
        try:
            if not self.win.winfo_exists():
                return
        except Exception:
            return

        try:
            hx, hy = self.get_hand()
            cx, cy = self.get_collar()
        except Exception:
            return

        # Both points must be valid on screen
        if hx <= 0 or hy <= 0 or cx <= 0 or cy <= 0:
            self.canvas.delete("all")
            self._loop_timer = self.root.after(40, self._tick)
            return

        cfg = self.get_config()
        max_len = float(cfg.get("leash_length", 200))
        leash_col = str(cfg.get("leash_color", "#8B4513"))

        dx = cx - hx
        dy = cy - hy
        dist = float(math.hypot(dx, dy))

        self.canvas.delete("all")

        # ── 1. TAUT LEASH (Distance >= Max Length) ───────────────────────────
        if dist >= max_len:
            self._taut_ticks += 1

            # Draw straight taut line with slight tension vibration
            vib = math.sin(self._taut_ticks * 0.8) * 1.2 if self._taut_ticks % 2 == 0 else 0.0
            mid_vx = (hx + cx) / 2.0 - (dy / dist) * vib
            mid_vy = (hy + cy) / 2.0 + (dx / dist) * vib

            # Draw outer outline / stitch
            coords = [float(hx), float(hy), float(mid_vx), float(mid_vy), float(cx), float(cy)]
            self.canvas.create_line(
                coords,
                fill=leash_col, width=3, capstyle="round", joinstyle="round"
            )

            # Draw metallic collar clip / ring at pet collar
            self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#F59E0B", outline="#78350F")

            # Physics pull: lead/step pet towards the owner
            excess = float(dist - max_len)
            if excess > 8.0:
                pull_step = 8
            elif excess < 2.0:
                pull_step = 2
            else:
                pull_step = int(excess)

            dir_x = (hx - cx) / dist
            dir_y = (hy - cy) / dist

            target_step_x = int(dir_x * pull_step)
            target_step_y = int(dir_y * pull_step)
            self.pull_pet(target_step_x, target_step_y, dir_x > 0)

            # Trigger pull complaint or owner urge dialogue occasionally
            if self._taut_ticks > 25:
                import time
                now = time.time()
                if now - self._last_pull_speech > 9.0:
                    self._last_pull_speech = now
                    if self.on_pull_dialogue:
                        self.on_pull_dialogue()

        # ── 2. SLACK LEASH (Distance < Max Length) ────────────────────────────
        else:
            self._taut_ticks = 0

            # Catenary drooping curve
            slack = max_len - dist
            sag = min(90.0, slack * 0.48)

            # 3-point quadratic spline curve using mid-point
            mid_x = (hx + cx) / 2.0
            mid_y = (hy + cy) / 2.0 + sag

            # Quarter points for realistic hanging rope spline
            q1_x = (hx + mid_x) / 2.0
            q1_y = (hy + mid_y) / 2.0 + (sag * 0.25)

            q2_x = (mid_x + cx) / 2.0
            q2_y = (mid_y + cy) / 2.0 + (sag * 0.25)

            # Smooth curve using canvas smooth=True
            coords = [hx, hy, q1_x, q1_y, mid_x, mid_y, q2_x, q2_y, cx, cy]
            self.canvas.create_line(
                coords, smooth=True, fill=leash_col, width=3,
                capstyle="round", joinstyle="round"
            )

            # Collar clip
            self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#F59E0B", outline="#78350F")

        # Schedule next render frame at ~30 FPS
        self._loop_timer = self.root.after(33, self._tick)
