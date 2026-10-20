"""
bomb.py
Interactive Bomb Spawner and Explosive FX for Desktop Pet.
Features:
- Transparent floating Toplevel window anywhere on screen.
- Draggable with left mouse button to reposition anywhere.
- Real-time mouse wheel scroll on the bomb to adjust fuse time on the fly.
- Right-click context menu with quick presets (1s, 2s, 3s, 5s, 10s, Custom), Detonate Now, and Defuse.
- Sizzling burning rope fuse with animated sparks, fire particles, and smoke puffs.
- Swelling/pulsing red body as detonation nears.
- Multi-layered fireball explosion effect with expanding shockwave ring.
- Radial blast physics callback that flings the pet and triggers explosion audio.
"""

from __future__ import annotations
import math
import time
import random
import tkinter as tk
from tkinter import simpledialog
from typing import Callable, Any

CHROMA = "#010101"
CANVAS_SIZE = 160


class BombWindow:
    """An individual active bomb window on screen."""

    def __init__(
        self,
        root: tk.Tk,
        center_x: int,
        center_y: int,
        fuse_sec: float = 3.0,
        blast_power: float = 35.0,
        on_explode: Callable[..., None] | None = None,
        on_remove: Callable[[BombWindow], None] | None = None,
    ):
        self.root = root
        self.center_x = center_x
        self.center_y = center_y
        self.fuse_sec = max(0.5, fuse_sec)
        self.time_left = self.fuse_sec
        self.blast_power = max(5.0, blast_power)
        self.on_explode = on_explode
        self.on_remove = on_remove

        self.state = "ticking"  # "ticking" or "exploding"
        self._drag_ox = 0
        self._drag_oy = 0
        self._is_dragging = False
        self._drag_start_time = 0.0

        # Animation states
        self._spark_particles: list[dict[str, Any]] = []
        self._explosion_frame = 0
        self._explosion_particles: list[dict[str, Any]] = []
        self._last_tick_time = time.time()
        self._pulse_phase = 0.0

        # Window setup
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", CHROMA)
        self.win.configure(bg=CHROMA)
        self.win.resizable(False, False)

        half = CANVAS_SIZE // 2
        self.win.geometry(f"{CANVAS_SIZE}x{CANVAS_SIZE}+{center_x - half}+{center_y - half}")

        self.canvas = tk.Canvas(
            self.win,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            bg=CHROMA,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Mouse bindings
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-3>", self._show_popup_menu)

        # Start animation loop
        self._loop_id: str | None = None
        self._tick()

    def _on_press(self, event):
        self._drag_ox = event.x
        self._drag_oy = event.y
        self._is_dragging = False
        self._drag_start_time = time.time()

    def _on_drag(self, event):
        self._is_dragging = True
        wx = self.win.winfo_x() + (event.x - self._drag_ox)
        wy = self.win.winfo_y() + (event.y - self._drag_oy)
        self.win.geometry(f"+{wx}+{wy}")
        self.center_x = wx + CANVAS_SIZE // 2
        self.center_y = wy + CANVAS_SIZE // 2

    def _on_release(self, event):
        if not self._is_dragging and (time.time() - self._drag_start_time) < 0.25:
            # Quick left click: ignite faster or detonate immediately!
            if self.time_left > 0.5:
                self.time_left = 0.3  # rapid instant countdown!
            else:
                self.detonate()

    def _on_mousewheel(self, event):
        """Scroll wheel adjusts fuse time up or down dynamically."""
        if self.state != "ticking":
            return
        delta = 0.5 if event.delta > 0 else -0.5
        new_fuse = max(0.5, min(30.0, self.fuse_sec + delta))
        self.set_fuse(new_fuse)

    def set_fuse(self, sec: float):
        """Updates fuse duration."""
        self.fuse_sec = max(0.5, sec)
        self.time_left = self.fuse_sec

    def set_blast_power(self, power: float):
        """Updates fling force for this bomb."""
        self.blast_power = max(5.0, min(250.0, power))

    def _prompt_custom_force(self):
        val = simpledialog.askfloat(
            "Custom Fling Force",
            "Enter blast fling power (5.0 to 250.0):\n(Gentle: 15, Normal: 35, Strong: 55, Extreme: 80+)",
            initialvalue=self.blast_power,
            minvalue=5.0,
            maxvalue=250.0,
            parent=self.win
        )
        if val is not None:
            self.set_blast_power(val)

    def _show_popup_menu(self, event):
        """Shows right-click popup menu for bomb controls."""
        menu = tk.Menu(self.win, tearoff=0, font=("Segoe UI", 9))
        menu.add_command(label="💥 Detonate Now!", command=self.detonate)
        menu.add_separator()

        fuse_menu = tk.Menu(menu, tearoff=0, font=("Segoe UI", 9))
        for s in [1.0, 2.0, 3.0, 5.0, 10.0, 15.0]:
            is_cur = abs(self.fuse_sec - s) < 0.1
            lbl = f"{s:.1f}s" + ("  ✓" if is_cur else "")
            fuse_menu.add_command(label=lbl, command=lambda val=s: self.set_fuse(val))
        fuse_menu.add_separator()
        fuse_menu.add_command(label="✏️ Custom Fuse...", command=self._prompt_custom_fuse)
        menu.add_cascade(label=f"⏱️ Set Fuse Time ({self.fuse_sec:.1f}s)", menu=fuse_menu)

        force_menu = tk.Menu(menu, tearoff=0, font=("Segoe UI", 9))
        presets = [
            ("Gentle", 15.0),
            ("Normal", 35.0),
            ("Strong", 55.0),
            ("Extreme / YEET", 80.0),
            ("Orbital Rocket", 120.0),
        ]
        for name, p in presets:
            is_cur = abs(self.blast_power - p) < 1.0
            lbl = f"{name} ({int(p)})" + ("  ✓" if is_cur else "")
            force_menu.add_command(label=lbl, command=lambda val=p: self.set_blast_power(val))
        force_menu.add_separator()
        force_menu.add_command(label="✏️ Custom Force...", command=self._prompt_custom_force)
        menu.add_cascade(label=f"🚀 Fling Force ({int(self.blast_power)})", menu=force_menu)

        menu.add_separator()
        menu.add_command(label="❌ Defuse Bomb", command=self.defuse)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _prompt_custom_fuse(self):
        val = simpledialog.askfloat(
            "Custom Fuse Time",
            "Enter fuse duration in seconds (0.5 to 60.0):",
            initialvalue=self.fuse_sec,
            minvalue=0.5,
            maxvalue=60.0,
            parent=self.win
        )
        if val is not None:
            self.set_fuse(val)

    def defuse(self):
        """Cancels and safely removes this bomb."""
        if self._loop_id:
            try:
                self.win.after_cancel(self._loop_id)
            except Exception:
                pass
            self._loop_id = None
        if self.on_remove:
            self.on_remove(self)
        try:
            self.win.destroy()
        except Exception:
            pass

    def detonate(self):
        """Triggers the explosion immediately."""
        if self.state == "exploding":
            return
        self.state = "exploding"
        self._explosion_frame = 0

        # Calculate absolute screen center
        cur_wx = self.win.winfo_x()
        cur_wy = self.win.winfo_y()
        cx = cur_wx + CANVAS_SIZE // 2
        cy = cur_wy + CANVAS_SIZE // 2

        # Initialize explosion particle bursts
        self._explosion_particles = []
        for _ in range(28):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(3.0, 10.5)
            self._explosion_particles.append({
                "x": CANVAS_SIZE / 2,
                "y": CANVAS_SIZE / 2,
                "vx": math.cos(angle) * spd,
                "vy": math.sin(angle) * spd,
                "life": 1.0,
                "decay": random.uniform(0.06, 0.12),
                "size": random.uniform(3.0, 7.0),
                "color": random.choice(["#FFF", "#FFD700", "#FF4500", "#FF8C00", "#FF3300"])
            })

        # Fire callback to trigger sound & fling pet!
        if self.on_explode:
            try:
                self.on_explode(cx, cy, self.blast_power)
            except TypeError:
                self.on_explode(cx, cy)

    def _tick(self):
        now = time.time()
        dt = max(0.001, now - self._last_tick_time)
        self._last_tick_time = now

        if not self.win.winfo_exists():
            return

        self.canvas.delete("all")

        if self.state == "ticking":
            self.time_left -= dt
            self._pulse_phase += dt * (10.0 if self.time_left < 1.0 else 5.0)

            if self.time_left <= 0:
                self.detonate()
            else:
                self._draw_bomb()

        elif self.state == "exploding":
            self._explosion_frame += 1
            self._draw_explosion(dt)

            if self._explosion_frame >= 16:
                # Explosion sequence finished
                self.defuse()
                return

        delay = 33  # ~30 FPS
        self._loop_id = self.win.after(delay, self._tick)

    def _draw_bomb(self):
        cx = CANVAS_SIZE // 2
        cy = CANVAS_SIZE // 2 + 10

        # Pulsating scale when about to detonate
        urgency = max(0.0, 1.0 - (self.time_left / max(0.5, self.fuse_sec)))
        pulse = math.sin(self._pulse_phase) * (3.5 * urgency)
        r = 24.0 + pulse

        # 1. Burning Fuse Rope
        # Fuse is a quadratic curve starting at bomb collar (cx, cy - r) to fuse tip
        fuse_ratio = max(0.05, self.time_left / max(0.1, self.fuse_sec))
        tip_x = cx + 22.0 * fuse_ratio
        tip_y = (cy - r - 22.0 * fuse_ratio)
        ctrl_x = cx + 8.0
        ctrl_y = cy - r - 20.0

        # Draw braided rope line
        coords = [cx, cy - r, ctrl_x, ctrl_y, tip_x, tip_y]
        self.canvas.create_line(
            coords,
            fill="#8B5A2B", width=3, smooth=True, capstyle="round"
        )

        # 2. Sizzling Spark Particles at Fuse Tip
        # Add new spark
        self._spark_particles.append({
            "x": tip_x,
            "y": tip_y,
            "vx": random.uniform(-2.5, 2.5),
            "vy": random.uniform(-3.5, 0.5),
            "life": 1.0,
            "color": random.choice(["#FFF", "#FFD700", "#FF8C00", "#FF4500"])
        })

        # Update & draw sparks
        alive_sparks = []
        for spk in self._spark_particles:
            spk["x"] += spk["vx"]
            spk["y"] += spk["vy"]
            spk["life"] -= 0.12
            if spk["life"] > 0:
                alive_sparks.append(spk)
                sz = max(1.0, 3.5 * spk["life"])
                self.canvas.create_oval(
                    spk["x"] - sz, spk["y"] - sz, spk["x"] + sz, spk["y"] + sz,
                    fill=spk["color"], outline=""
                )
        self._spark_particles = alive_sparks

        # Main glowing spark at tip
        glow_sz = random.uniform(4.0, 7.0)
        self.canvas.create_oval(
            tip_x - glow_sz, tip_y - glow_sz, tip_x + glow_sz, tip_y + glow_sz,
            fill="#FFF700", outline="#FF4500", width=1
        )

        # 3. Metallic Brass Cap/Collar
        cap_w = 7.0
        cap_h = 5.0
        self.canvas.create_rectangle(
            cx - cap_w, cy - r - cap_h, cx + cap_w, cy - r + 1,
            fill="#D4AF37", outline="#8C6D1F", width=1
        )

        # 4. Bomb Body (Color flashes red when urgent)
        if self.time_left < 1.0 and (int(self._pulse_phase * 2) % 2 == 0):
            bomb_color = "#B22222"  # Urgent flashing red
            outline_col = "#FF0000"
        else:
            bomb_color = "#151515"
            outline_col = "#2A2A2A"

        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=bomb_color, outline=outline_col, width=2
        )

        # 5. Glossy Highlight Arc
        hl_r = r * 0.65
        self.canvas.create_arc(
            cx - r + 5, cy - r + 5, cx - r + 5 + hl_r * 2, cy - r + 5 + hl_r * 2,
            start=100, extent=75,
            outline="#FFFFFF", width=3, style="arc"
        )
        self.canvas.create_oval(
            cx - r + 9, cy - r + 9, cx - r + 13, cy - r + 13,
            fill="#FFFFFF", outline=""
        )

        # 6. Countdown Time Badge
        badge_txt = f"{self.time_left:.1f}s"
        badge_y = cy + r + 12
        self.canvas.create_rectangle(
            cx - 24, badge_y - 8, cx + 24, badge_y + 8,
            fill="#1E1E28", outline="#FF4500" if self.time_left < 1.0 else "#444455", width=1
        )
        self.canvas.create_text(
            cx, badge_y,
            text=badge_txt,
            fill="#FFD700" if self.time_left < 1.0 else "#FFFFFF",
            font=("Segoe UI", 8, "bold")
        )

    def _draw_explosion(self, dt: float):
        cx = CANVAS_SIZE / 2
        cy = CANVAS_SIZE / 2

        progress = self._explosion_frame / 16.0
        max_r = 72.0

        # 1. Shockwave expanding ring
        ring_r = progress * max_r * 1.05
        ring_alpha_width = max(1, int(4 * (1.0 - progress)))
        ring_col = "#FFD700" if progress < 0.4 else "#FF4500"
        self.canvas.create_oval(
            cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r,
            outline=ring_col, width=ring_alpha_width
        )

        # 2. Layered Fireball Burst
        # Outer smoke/orange puff
        outer_r = max(5.0, math.sin(progress * math.pi) * (max_r * 0.95))
        self.canvas.create_oval(
            cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
            fill="#FF4500", outline="#FF8C00", width=2
        )

        # Middle intense yellow burst
        mid_r = outer_r * 0.7
        if mid_r > 3:
            self.canvas.create_oval(
                cx - mid_r, cy - mid_r, cx + mid_r, cy + mid_r,
                fill="#FFD700", outline=""
            )

        # Core white-hot center
        core_r = outer_r * 0.4
        if core_r > 2 and progress < 0.7:
            self.canvas.create_oval(
                cx - core_r, cy - core_r, cx + core_r, cy + core_r,
                fill="#FFFFFF", outline=""
            )

        # 3. Flying Spark & Debris Particles
        for p in self._explosion_particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] *= 0.92
            p["vy"] *= 0.92
            p["life"] = max(0.0, p["life"] - p["decay"])

            if p["life"] > 0:
                psz = max(1.0, p["size"] * p["life"])
                self.canvas.create_oval(
                    p["x"] - psz, p["y"] - psz, p["x"] + psz, p["y"] + psz,
                    fill=p["color"], outline=""
                )


class BombManager:
    """Manages spawning, tracking, and triggering active bombs on screen."""

    def __init__(
        self,
        root: tk.Tk,
        on_explode: Callable[..., None],
        get_fuse_fn: Callable[[], float] | None = None,
        set_fuse_fn: Callable[[float], None] | None = None,
        get_power_fn: Callable[[], float] | None = None,
        set_power_fn: Callable[[float], None] | None = None,
    ):
        self.root = root
        self.on_explode = on_explode
        self.get_fuse_fn = get_fuse_fn
        self.set_fuse_fn = set_fuse_fn
        self.get_power_fn = get_power_fn
        self.set_power_fn = set_power_fn
        self.bombs: list[BombWindow] = []

    def get_default_fuse(self) -> float:
        if self.get_fuse_fn:
            try:
                return self.get_fuse_fn()
            except Exception:
                pass
        return 3.0

    def set_default_fuse(self, sec: float):
        sec = max(0.5, min(60.0, round(sec, 1)))
        if self.set_fuse_fn:
            try:
                self.set_fuse_fn(sec)
            except Exception:
                pass

    def get_default_power(self) -> float:
        if self.get_power_fn:
            try:
                return self.get_power_fn()
            except Exception:
                pass
        return 35.0

    def set_default_power(self, power: float):
        power = max(5.0, min(250.0, round(power, 1)))
        if self.set_power_fn:
            try:
                self.set_power_fn(power)
            except Exception:
                pass

    def spawn_bomb(
        self,
        x: int,
        y: int,
        fuse_sec: float | None = None,
        blast_power: float | None = None,
    ) -> BombWindow:
        """Spawns an interactive bomb centered at (x, y)."""
        f_sec: float = self.get_default_fuse() if fuse_sec is None else fuse_sec
        b_pow: float = self.get_default_power() if blast_power is None else blast_power

        bomb = BombWindow(
            root=self.root,
            center_x=x,
            center_y=y,
            fuse_sec=f_sec,
            blast_power=b_pow,
            on_explode=self.on_explode,
            on_remove=self._remove_bomb
        )
        self.bombs.append(bomb)
        return bomb

    def _remove_bomb(self, bomb: BombWindow):
        if bomb in self.bombs:
            self.bombs.remove(bomb)

    def detonate_all(self):
        """Detonates all currently active bombs simultaneously."""
        for b in list(self.bombs):
            b.detonate()

    def defuse_all(self):
        """Defuses and cleans up all active bombs."""
        for b in list(self.bombs):
            b.defuse()
        self.bombs.clear()

    def cleanup(self):
        self.defuse_all()
