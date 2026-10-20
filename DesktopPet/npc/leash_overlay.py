"""
leash_overlay.py (Interactive Bullwhip Tool)
Full-screen transparent canvas overlay featuring a realistic handheld bullwhip.
The whip floats naturally at the cursor with multi-node Verlet physics (natural hanging drape,
inertia sway, wrist loop, braided leather details, and red cracker).
Continuously follows the system cursor via real-time pointer querying.
Left-clicking anywhere immediately lashes out across the screen and whips the pet directly!
"""

import math
import random
import tkinter as tk
from pathlib import Path

try:
    import paths
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths

import themes
import sound_manager

try:
    from combo_counter import ComboCounter
except ImportError:
    from core.combo_counter import ComboCounter

CHROMA = "#020202"
WHIP_CRACK_SOUND = sound_manager.WHIP_CRACK_SOUND
SOUND_FILE = WHIP_CRACK_SOUND  # Backward compatibility
NUM_NODES = 10
SEGMENT_REST_LEN = 13.5


class WhipNode:
    """Verlet physics particle representing a segment joint along the whip."""
    __slots__ = ("x", "y", "old_x", "old_y")

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.old_x = x
        self.old_y = y


class LeashOverlay:
    """Interactive Bullwhip Tool that floats realistically at the cursor and whips the pet on click."""

    def __init__(self, root: tk.Tk, on_hit=None, on_close=None, is_muted_fn=None, get_pet_rect_fn=None):
        self.root = root
        self.on_hit = on_hit
        self.on_close = on_close
        self.is_muted_fn = is_muted_fn
        self.get_pet_rect_fn = get_pet_rect_fn

        self.sw = root.winfo_screenwidth()
        self.sh = root.winfo_screenheight()

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", CHROMA)
        self.win.configure(bg=CHROMA)
        self.win.geometry(f"{self.sw}x{self.sh}+0+0")
        self.win.withdraw()

        self.canvas = tk.Canvas(
            self.win, width=self.sw, height=self.sh,
            bg=CHROMA, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.active: bool = False
        self.animating: bool = False
        self._anim_timer: str | None = None
        self._physics_timer: str | None = None
        self._tick: int = 0

        self.last_pet_rect: tuple[int, int, int, int] | None = None
        self.mouse_x: int = self.sw // 2
        self.mouse_y: int = self.sh // 2
        self._prev_mx: int = self.mouse_x
        self._prev_my: int = self.mouse_y

        self._prev_l_down: bool = True
        self._prev_r_down: bool = True
        self._prev_esc_down: bool = False

        # Arcade combo counter
        self.combo_counter = ComboCounter()

        # Multi-node Verlet physics chain
        self.nodes: list[WhipNode] = [WhipNode(0.0, 0.0) for _ in range(NUM_NODES)]
        self._init_whip_nodes(self.mouse_x, self.mouse_y)

        # Bindings on overlay canvas
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<ButtonPress-1>", self._on_click)
        self.canvas.bind("<ButtonPress-3>", self._on_right_click)
        self.win.bind("<Escape>", lambda e: self.disable())

    def _init_whip_nodes(self, mx: int, my: int):
        """Initializes whip joints in a natural, realistic handheld hanging drape."""
        handle_angle = math.radians(30.0)
        handle_len = 36.0
        hx = mx + (handle_len - 6.0) * math.cos(handle_angle)
        hy = my + (handle_len - 6.0) * math.sin(handle_angle)

        # Natural catenary hang: arches out from handle, curves downward, and curls back gently at tip
        drape_offsets = [
            (0.0, 0.0),      # Node 0 (handle tip / keeper)
            (6.0, 11.0),     # Node 1
            (11.0, 24.0),    # Node 2
            (14.0, 39.0),    # Node 3
            (13.0, 56.0),    # Node 4
            (9.0, 72.0),     # Node 5
            (2.0, 87.0),     # Node 6
            (-6.0, 99.0),    # Node 7
            (-15.0, 104.0),  # Node 8
            (-21.0, 98.0),   # Node 9 (curling upward tip with cracker)
        ]

        for i in range(NUM_NODES):
            ox, oy = drape_offsets[i]
            self.nodes[i].x = hx + ox
            self.nodes[i].y = hy + oy
            self.nodes[i].old_x = hx + ox
            self.nodes[i].old_y = hy + oy

    def enable(self):
        self.active = True
        self.animating = False
        self._tick = 0
        self._prev_l_down = True  # prevent accidental click trigger from the button press
        self._prev_r_down = True
        self._prev_esc_down = False
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

        # Update initial cursor position
        try:
            cur_x = self.win.winfo_pointerx()
            cur_y = self.win.winfo_pointery()
            if 0 <= cur_x <= self.sw and 0 <= cur_y <= self.sh:
                self.mouse_x = cur_x
                self.mouse_y = cur_y
        except Exception:
            pass

        self._prev_mx = self.mouse_x
        self._prev_my = self.mouse_y

        self.combo_counter.reset()
        self._init_whip_nodes(self.mouse_x, self.mouse_y)
        self._start_physics_loop()

    def disable(self):
        if not self.active:
            return
        self.active = False
        self.animating = False
        if self._anim_timer:
            try:
                self.win.after_cancel(self._anim_timer)
            except Exception:
                pass
            self._anim_timer = None
        if self._physics_timer:
            try:
                self.win.after_cancel(self._physics_timer)
            except Exception:
                pass
            self._physics_timer = None
        sound_manager.stop_all()
        self.combo_counter.reset()
        self.canvas.delete("all")
        self.win.withdraw()
        if self.on_close:
            self.on_close()

    def update_pet_rect(self, pet_x: int, pet_y: int, pet_w: int, pet_h: int):
        """Stores pet coordinates for whip strike targeting."""
        self.last_pet_rect = (pet_x, pet_y, pet_w, pet_h)

    def update_leash(self, pet_x: int, pet_y: int, pet_w: int, pet_h: int):
        """Backwards compatibility alias for update_pet_rect."""
        self.update_pet_rect(pet_x, pet_y, pet_w, pet_h)

    def _start_physics_loop(self):
        """High-refresh Verlet physics loop simulating genuine fluid whip drape and inertia."""
        if not self.active:
            return

        if not self.animating:
            self._update_physics()
            self._redraw_idle()

        # Update combo counter state & tracking
        if self.get_pet_rect_fn:
            try:
                self.last_pet_rect = self.get_pet_rect_fn()
            except Exception:
                pass
        self.combo_counter.update(0.018, pet_rect=self.last_pet_rect)

        # ~55 FPS smooth physics loop
        self._physics_timer = self.win.after(18, self._start_physics_loop)

    def _update_physics(self):
        self._tick += 1

        # Query live system pointer position so whip reliably follows cursor anywhere on screen
        try:
            cur_x = self.win.winfo_pointerx()
            cur_y = self.win.winfo_pointery()
            if -100 <= cur_x <= self.sw + 100 and -100 <= cur_y <= self.sh + 100:
                self.mouse_x = cur_x
                self.mouse_y = cur_y
        except Exception:
            pass

        mx, my = self.mouse_x, self.mouse_y

        # Subtly tilt handle with cursor horizontal momentum
        cursor_vx = (mx - self._prev_mx)
        self._prev_mx = mx
        self._prev_my = my

        # Global input detection via GetAsyncKeyState for reliable click-to-whip anywhere on desktop
        try:
            import ctypes
            l_down = bool(ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000)
            r_down = bool(ctypes.windll.user32.GetAsyncKeyState(0x02) & 0x8000)
            esc_down = bool(ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000)

            if r_down and not getattr(self, "_prev_r_down", True):
                self.disable()
                return

            if esc_down and not getattr(self, "_prev_esc_down", False):
                self.disable()
                return

            if l_down and not getattr(self, "_prev_l_down", True):
                self._handle_user_click(mx, my)

            self._prev_l_down = l_down
            self._prev_r_down = r_down
            self._prev_esc_down = esc_down
        except Exception:
            pass

        dynamic_tilt = max(-0.25, min(0.25, cursor_vx * 0.015))
        handle_angle = math.radians(30.0) + dynamic_tilt
        handle_len = 36.0
        hx = mx + (handle_len - 6.0) * math.cos(handle_angle)
        hy = my + (handle_len - 6.0) * math.sin(handle_angle)

        # Node 0 is anchored to the front of the handle
        self.nodes[0].x = hx
        self.nodes[0].y = hy
        self.nodes[0].old_x = hx
        self.nodes[0].old_y = hy

        gravity = 0.72
        friction = 0.89
        ambient_drift = math.sin(self._tick * 0.08) * 0.28

        # Step 1: Verlet position integration
        for i in range(1, NUM_NODES):
            node = self.nodes[i]
            vx = (node.x - node.old_x) * friction
            vy = (node.y - node.old_y) * friction
            node.old_x = node.x
            node.old_y = node.y
            # Apply inertia, gravity, and gentle ambient idle breathing
            node.x += vx + ambient_drift * (i / float(NUM_NODES))
            node.y += vy + gravity

        # Step 2: Distance constraint relaxation (6 passes for rock-solid stability)
        for _ in range(6):
            self.nodes[0].x = hx
            self.nodes[0].y = hy

            for i in range(NUM_NODES - 1):
                na = self.nodes[i]
                nb = self.nodes[i + 1]
                dx = nb.x - na.x
                dy = nb.y - na.y
                dist = math.hypot(dx, dy)
                if dist > 0.0001:
                    diff = (dist - SEGMENT_REST_LEN) / dist
                    if i == 0:
                        nb.x -= dx * diff
                        nb.y -= dy * diff
                    else:
                        na.x += dx * diff * 0.45
                        na.y += dy * diff * 0.45
                        nb.x -= dx * diff * 0.55
                        nb.y -= dy * diff * 0.55

    def _on_motion(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def _on_right_click(self, event):
        """Right click puts away the whip cleanly."""
        self.disable()

    def _on_click(self, event):
        self._handle_user_click(event.x, event.y)

    def _handle_user_click(self, tx: int, ty: int):
        if not self.active:
            return

        # Check if user clicked the top HUD close button [✕]
        pill_cx = self.sw // 2
        if pill_cx + 130 <= tx <= pill_cx + 200 and 10 <= ty <= 45:
            self.disable()
            return

        # Query live pet coordinates directly
        if self.get_pet_rect_fn:
            try:
                self.last_pet_rect = self.get_pet_rect_fn()
            except Exception:
                pass

        if self.last_pet_rect is not None:
            px, py, pw, ph = self.last_pet_rect
            strike_x = px + pw // 2
            strike_y = py + ph // 3
        else:
            strike_x = tx
            strike_y = ty

        # Unleash whip directly on pet
        self.crack_at(strike_x, strike_y, origin_x=tx, origin_y=ty, is_hit=True)

    def crack_at(self, target_x: int, target_y: int, origin_x: int | None = None, origin_y: int | None = None, is_hit: bool = True):
        """Triggers high-impact dynamic whip strike straight onto target_x, target_y."""
        if not self.active:
            return

        self.animating = True
        if self._anim_timer:
            try:
                self.win.after_cancel(self._anim_timer)
            except Exception:
                pass

        if origin_x is None:
            origin_x = self.mouse_x
        if origin_y is None:
            origin_y = self.mouse_y

        # Left-click: always play whip crack sound immediately
        self._play_crack_sound()

        # Notify hit on pet immediately so physics impulse kicks in right on crack
        if is_hit and self.on_hit:
            self.on_hit(target_x, target_y, origin_x, origin_y)

        if is_hit:
            self.combo_counter.register_hit(target_x, target_y, pet_rect=self.last_pet_rect)

        # Animation sequence:
        # Phase 0: Rear high-tension windup (0ms)
        self._draw_crack_phase(origin_x, origin_y, target_x, target_y, phase=0, is_hit=is_hit)

        # Phase 1: High speed sonic wave across screen (25ms)
        def step1():
            self._draw_crack_phase(origin_x, origin_y, target_x, target_y, phase=1, is_hit=is_hit)

        # Phase 2: Maximum supersonic impact + starburst sparks + text on pet (60ms)
        def step2():
            self._draw_crack_phase(origin_x, origin_y, target_x, target_y, phase=2, is_hit=is_hit)
            if is_hit:
                self._play_hit_sound()

        # Phase 3: Recoil ripple (125ms)
        def step3():
            self._draw_crack_phase(origin_x, origin_y, target_x, target_y, phase=3, is_hit=is_hit)

        # Phase 4: Settle back smoothly to floating handheld physics pose (210ms)
        def step4():
            self.animating = False
            self._init_whip_nodes(self.mouse_x, self.mouse_y)
            self._redraw_idle()

        self.win.after(25, step1)
        self.win.after(60, step2)
        self.win.after(125, step3)
        self._anim_timer = self.win.after(210, step4)

    def _play_crack_sound(self):
        if self.is_muted_fn and self.is_muted_fn():
            return
        sound_manager.play_crack_sound()

    def _play_hit_sound(self):
        if self.is_muted_fn and self.is_muted_fn():
            return

        hit_info = sound_manager.get_random_hit_sound()
        if not hit_info:
            return

        hit_target, duration_sec = hit_info
        sound_manager.play_hit_sound(hit_target, duration_sec=duration_sec, tk_root=self.root)

    def _play_sound(self):
        """Backward compatibility alias."""
        self._play_crack_sound()

    def _draw_hud(self):
        """Draws top status notification pill."""
        pill_w = 440
        pill_h = 32
        pill_x1 = self.sw // 2 - pill_w // 2
        pill_y1 = 12
        pill_x2 = self.sw // 2 + pill_w // 2
        pill_y2 = pill_y1 + pill_h

        t = themes.get()
        accent = t.get("accent", "#e74c3c")
        bg_bar = "#14151f"

        self.canvas.create_rectangle(
            pill_x1, pill_y1, pill_x2, pill_y2,
            fill=bg_bar, outline=accent, width=1.5
        )
        hud_text = "🤠 WHIP ACTIVE — Left-Click anywhere to Whip Pet! • Right-Click / ESC to Exit"
        if self.combo_counter.combo > 0:
            hits_word = "HIT" if self.combo_counter.combo == 1 else "HITS"
            hud_text = f"🤠 WHIP ACTIVE — Combo: {self.combo_counter.combo} {hits_word}! • Right-Click / ESC to Exit"

        self.canvas.create_text(
            pill_x1 + 14, (pill_y1 + pill_y2) // 2,
            anchor="w",
            text=hud_text,
            fill="#ffffff", font=("Segoe UI", 9, "bold")
        )
        close_bx = pill_x2 - 25
        self.canvas.create_text(
            close_bx, (pill_y1 + pill_y2) // 2,
            text="[✕]",
            fill=accent, font=("Segoe UI", 10, "bold")
        )

    def _draw_handle(self, mx: int, my: int, angle: float) -> tuple[float, float]:
        """Renders an authentic leather bullwhip handle at the cursor."""
        handle_len = 36.0
        # The hand grips the handle near the cursor
        base_x = mx - 6.0 * math.cos(angle)
        base_y = my - 6.0 * math.sin(angle)
        hx = mx + (handle_len - 6.0) * math.cos(angle)
        hy = my + (handle_len - 6.0) * math.sin(angle)

        # Hanging leather wrist loop dangling naturally under gravity
        strap_pts = [
            base_x, base_y,
            base_x - 3, base_y + 10,
            base_x + 1, base_y + 18,
            base_x + 6, base_y + 11,
            base_x + 2, base_y + 2,
        ]
        self.canvas.create_line(strap_pts, smooth=True, width=2.0, fill="#231206", capstyle="round")

        # Main handle grip rod
        self.canvas.create_line(
            [base_x, base_y, hx, hy],
            width=7.5, fill="#1c0e04", capstyle="round"
        )
        # Braided leather ridges
        self.canvas.create_line(
            [base_x + 3 * math.cos(angle), base_y + 3 * math.sin(angle),
             hx - 3 * math.cos(angle), hy - 3 * math.sin(angle)],
            width=5.0, fill="#42210c", capstyle="round"
        )
        # Gold/brass pommel heel knot
        self.canvas.create_oval(
            base_x - 4.5, base_y - 4.5, base_x + 4.5, base_y + 4.5,
            fill="#d4af37", outline="#8a6f1e", width=1.5
        )
        # Gold/brass ferrule collar joining thong
        self.canvas.create_oval(
            hx - 3.5, hy - 3.5, hx + 3.5, hy + 3.5,
            fill="#d4af37", outline="#8a6f1e", width=1.5
        )
        return hx, hy

    def _redraw_idle(self):
        """Renders the realistic handheld bullwhip floating at cursor with physics drape."""
        if not self.active:
            return

        self.canvas.delete("all")
        self._draw_hud()

        mx, my = self.mouse_x, self.mouse_y

        # Handle tilted forward-down ~30 degrees
        handle_angle = math.radians(30.0)
        self._draw_handle(mx, my, handle_angle)

        # Multi-tiered tapered braided whip curve through physics nodes
        pts = [(n.x, n.y) for n in self.nodes]

        # 1. Thick leather keeper & transition (Nodes 0 to 3)
        c0_3 = [c for pt in pts[0:4] for c in pt]
        self.canvas.create_line(
            c0_3, smooth=True, width=6.2, fill="#231206", capstyle="round"
        )

        # 2. Braided leather thong body (Nodes 2 to 6)
        c2_6 = [c for pt in pts[2:7] for c in pt]
        self.canvas.create_line(
            c2_6, smooth=True, width=4.4, fill="#4a2510", capstyle="round"
        )

        # 3. Tapered leather fall (Nodes 5 to 8)
        c5_8 = [c for pt in pts[5:9] for c in pt]
        self.canvas.create_line(
            c5_8, smooth=True, width=2.8, fill="#783c18", capstyle="round"
        )

        # 4. Latigo tip (Nodes 7 to 9)
        c7_9 = [c for pt in pts[7:10] for c in pt]
        self.canvas.create_line(
            c7_9, smooth=True, width=1.8, fill="#9a5223", capstyle="round"
        )

        # 5. Red nylon cracker popper at curling tip
        tip_x, tip_y = pts[-1]
        prev_x, prev_y = pts[-2]
        tdx = tip_x - prev_x
        tdy = tip_y - prev_y
        tlen = max(0.001, math.hypot(tdx, tdy))
        cracker_end_x = tip_x + (tdx / tlen) * 12.0
        cracker_end_y = tip_y + (tdy / tlen) * 12.0

        self.canvas.create_line(
            [tip_x, tip_y, cracker_end_x, cracker_end_y],
            width=2.5, fill="#ff1744", capstyle="round"
        )
        # Cracker fray tuft
        self.canvas.create_oval(
            cracker_end_x - 2.5, cracker_end_y - 2.5,
            cracker_end_x + 2.5, cracker_end_y + 2.5,
            fill="#ffea00", outline="#d50000", width=1
        )

        # Draw combo counter badge on top
        self.combo_counter.draw(self.canvas)

    def _draw_crack_phase(self, mx: int, my: int, tx: int, ty: int, phase: int, is_hit: bool = True):
        """Draws the 4 animation phases of the whip strike directly onto the target/pet."""
        if not self.active:
            return

        self.canvas.delete("all")
        self._draw_hud()

        angle = math.atan2(ty - my, tx - mx)
        hx, hy = self._draw_handle(mx, my, angle)

        dist = math.hypot(tx - hx, ty - hy)
        nx = (tx - hx) / max(1.0, dist)
        ny = (ty - hy) / max(1.0, dist)
        norm_x = -ny
        norm_y = nx

        if phase == 0:
            # Phase 0: Rear windup high-tension coil
            c1_x = hx - nx * 35 + norm_x * 45
            c1_y = hy - ny * 35 + norm_y * 45
            c2_x = hx + nx * (dist * 0.25) - norm_x * 40
            c2_y = hy + ny * (dist * 0.25) - norm_y * 40
            tip_x = hx + nx * (dist * 0.45)
            tip_y = hy + ny * (dist * 0.45)

            self.canvas.create_line(
                [hx, hy, c1_x, c1_y, c2_x, c2_y, tip_x, tip_y],
                smooth=True, width=5.2, fill="#2c1407", capstyle="round"
            )

        elif phase == 1:
            # Phase 1: High speed supersonic wave surging across screen to pet
            c1_x = hx + nx * (dist * 0.35) + norm_x * 55
            c1_y = hy + ny * (dist * 0.35) + norm_y * 55
            c2_x = hx + nx * (dist * 0.70) - norm_x * 45
            c2_y = hy + ny * (dist * 0.70) - norm_y * 45
            tip_x = tx - nx * 18
            tip_y = ty - ny * 18

            self.canvas.create_line(
                [hx, hy, c1_x, c1_y, c2_x, c2_y, tip_x, tip_y],
                smooth=True, width=4.2, fill="#4a2510", capstyle="round"
            )

        elif phase == 2:
            # Phase 2: THE CRACK! Whip strikes directly onto pet / target
            snap_x = tx - nx * 18 + norm_x * 12
            snap_y = ty - ny * 18 + norm_y * 12

            self.canvas.create_line(
                [hx, hy, (hx + tx) / 2 - norm_x * 10, (hy + ty) / 2 - norm_y * 10, snap_x, snap_y, tx, ty],
                smooth=True, width=3.4, fill="#6b3415", capstyle="round"
            )
            # Red popper crack line
            self.canvas.create_line(
                [snap_x, snap_y, tx, ty],
                width=3.0, fill="#ff1744", capstyle="round"
            )

        elif phase == 3:
            # Phase 3: Recoil ripple snapping back towards hand
            mid_x = (hx + tx) / 2 + norm_x * 22
            mid_y = (hy + ty) / 2 + norm_y * 22
            tip_x = tx - nx * 55
            tip_y = ty - ny * 55

            self.canvas.create_line(
                [hx, hy, mid_x, mid_y, tip_x, tip_y],
                smooth=True, width=3.4, fill="#4a2510", capstyle="round"
            )

        # Draw combo counter badge on top of whip
        self.combo_counter.draw(self.canvas)


# Backwards compatibility alias
WhipOverlay = LeashOverlay