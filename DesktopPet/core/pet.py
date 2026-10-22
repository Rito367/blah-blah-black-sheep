"""
pet.py
Transparent always-on-top pet window with fling physics, live settings, screen-edge bounce,
custom dialogue integrations, and summon/stealth visibility controls.
"""

import tkinter as tk
import time
import random
import re
from pathlib import Path
from PIL import Image, ImageTk

# Pillow 10+ Resampling and Transpose constants
try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
    FLIP_HORIZONTAL = Image.Transpose.FLIP_LEFT_RIGHT
except AttributeError:
    RESAMPLE_LANCZOS = getattr(Image, "LANCZOS")
    FLIP_HORIZONTAL = getattr(Image, "FLIP_LEFT_RIGHT")

# ── animation ─────────────────────────────────────────────────────────────
ANIMATIONS       = ["idle", "walk", "jump", "sleep", "eat"]
FRAME_MS         = 180
JUMP_MS          = 120
BASE_SPRITE_SIZE = (60, 60)

# ── behaviour timing (ms) ─────────────────────────────────────────────────
SLEEP_MIN_MS  = 15 * 60 * 1000
SLEEP_MAX_MS  = 30 * 60 * 1000
SLEEP_DUR_MS  =  5 * 60 * 1000
WALK_MIN_MS   =  5 * 60 * 1000
WALK_MAX_MS   = 10 * 60 * 1000
EAT_EVERY_MS  = 10 * 60 * 1000
EAT_DUR_MS    =  3 * 60 * 1000
IDLE_BUBBLE_CHECK_MS = 60 * 1000

# ── fallback messages ─────────────────────────────────────────────────────
IDLE_MESSAGES = [
    "Keep going, you're learning.",
    "One step at a time.",
    "Progress over perfection.",
    "Learn, grow, improve.",
    "You've got this.",
    "Keep showing up.",
    "Small steps still count.",
    "Grow through the experience.",
    "Do your best, learn the rest.",
    "Every day is progress.",
    "Jiayou! 加油！",
    "Don't be stressed. ♡",
    "Almost there!",
]

PAT_MESSAGES   = ["♡ ♡ ♡", "~(≧▽≦)/", "( ˘ ³˘)♥"]
SLEEP_MESSAGES = ["z z z . . .", "zzZZ 💤", "z z z ♡"]
EAT_MESSAGES   = ["Yummy~ ♡", "Yumz!", "Nom nom ♡", "So tasty~"]

COMPLAIN_MESSAGES = [
    "I'm tired...", 
    "Too much walking!", 
    "My legs hurt!", 
    "Can we stop?", 
    "Whew... so far!",
    "Slow down!"
]

WHIP_MESSAGES = [
    "OUCH! Why are you whipping me?! 😭",
    "OWWW! I'm working, I'm working! 🏃💨",
    "Mercy!! Please have mercy!! 🥺💔",
    "Hyaaaa! *runs for dear life* ⚡",
    "Call 911! Animal cruelty! 📢💀",
    "I'LL DO ANYTHING! JUST STOP! 😭🙌",
    "CRACK! That stings so bad! 🔥😿",
    "Faster! Faster! Sprinting now! 🏃‍♂️💨",
    "Aaaaargh! Not the whip! 😱"
]

BOMB_MESSAGES = [
    "BOOOOOOM?! 💥💀",
    "HOLY SHIT! WHAT WAS THAT?! 💣🔥",
    "I'M BLASTING OFF AGAINNNN! 🚀💫",
    "MY BUTT IS ON FIRE! 🚒💨",
    "WHO GAVE YOU A BOMB?! 😭💣",
    "AIRBORNE! ☁️🌪️",
    "MY EARS ARE RINGING! 🔔💥",
    "WHY DO YOU HAVE EXPLOSIVES?! 🙀💣"
]
MAX_WALK_STEPS = 60

# ── physics constants ─────────────────────────────────────────────────────
AIR_FRICTION_X   = 0.985
FLOOR_FRICTION_X = 0.85
PHYSICS_MS       = 30
FLOOR_MARGIN     = 40      
MIN_BOUNCE_VY    = 2.0
MIN_STOP_VX      = 0.3

CHROMA = "#010101"


def get_desktop_work_area() -> tuple[int, int, int, int] | None:
    """Returns (left, top, right, bottom) of the Windows usable work area (excluding taskbar), or None."""
    try:
        import ctypes
        import ctypes.wintypes
        rc = ctypes.wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rc), 0):
            if rc.right > rc.left and rc.bottom > rc.top:
                return rc.left, rc.top, rc.right, rc.bottom
    except Exception:
        pass
    return None


class PetWindow:
    def __init__(self, root: tk.Tk, on_double_click,
                 on_bubble=None,
                 on_move=None,
                 character_dir: Path | None = None,
                 scale: float = 1.0,
                 gravity: float = 1.2,
                 bounciness: float = 0.6,
                 chatter_chance: float = 0.20,
                 get_data=None):
        self.root            = root
        self.on_double_click = on_double_click
        self.on_bubble       = on_bubble
        self.on_move         = on_move
        self.scale           = scale
        self.gravity         = gravity
        self.bounciness      = bounciness
        self.chatter_chance  = chatter_chance
        self.get_data        = get_data

        if character_dir is None:
            try:
                import paths
                character_dir = paths.ASSETS_DIR / "pet"
            except ImportError:
                character_dir = Path(__file__).resolve().parent.parent / "assets" / "pet"
        self._char_dir = character_dir

        self.raw_frames: dict[str, list[Image.Image]] = {}
        self.frames: dict[str, list[ImageTk.PhotoImage]] = {}
        self._flip_cache: dict[str, ImageTk.PhotoImage]  = {}
        self._load_frames(self._char_dir)

        # ── animation state ───────────────────────────────────────────────
        self.current_anim  = "idle"
        self.frame_index   = 0
        self.facing_right  = True
        self.is_jumping    = False
        self._is_hovered   = False

        # ── behaviour state ───────────────────────────────────────────────
        self._state          = "idle"
        self._sleeping       = False    
        self._walk_target_x: int | None = None
        self._walk_duration_steps = 0
        self.chase_mouse     = False    
        self.continuous_patrol = False
        self.step_count      = 0
        self.walk_step_px    = 2
        self._base_walk_step_px = 2
        self._panic_sched_id: str | None = None
        self._is_hidden      = False
        self._topmost_tick   = 0
        
        self._sleep_sched_id = None
        self._walk_sched_id  = None
        self._eat_sched_id   = None
        self._wake_sched_id  = None
        self._eat_end_id     = None

        # ── physics state ─────────────────────────────────────────────────
        self._vx       = 0.0
        self._vy       = 0.0
        self._held     = False
        self._on_floor = False

        # ── mouse velocity tracking ───────────────────────────────────────
        self._drag_samples: list[tuple[float, int, int]] = []

        # ── screen & geometry ─────────────────────────────────────────────
        w, h = self.get_current_size()
        self.w = w   # Bug #6 fix: expose width so main.py can position bubbles correctly
        self.h = h
        self._update_screen_bounds()

        # ── window ────────────────────────────────────────────────────────
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", CHROMA)
        self.win.configure(bg=CHROMA)
        self.win.resizable(False, False)
        init_x = min(100 + self._min_x, self._max_x)
        self.win.geometry(f"{w}x{h}+{init_x}+{self._floor_y}")

        self.canvas = tk.Canvas(self.win, width=w, height=h,
                                bg=CHROMA, highlightthickness=0)
        self.canvas.pack()
        self._img_item = self.canvas.create_image(
            w // 2, h // 2, anchor="center")

        # ── bindings ──────────────────────────────────────────────────────
        self._drag_ox      = 0
        self._drag_oy      = 0
        self._dragging     = False
        self._click_count  = 0
        self._click_timer  = None
        DOUBLE_MS          = 300

        def on_press(event):
            self._drag_ox  = event.x_root - self.win.winfo_x()
            self._drag_oy  = event.y_root - self.win.winfo_y()
            self._dragging = False
            self._held     = True
            self._vx       = 0.0
            self._vy       = 0.0
            self._drag_samples = [(time.time(), event.x_root, event.y_root)]
            self.win.lift()
            self.win.attributes("-topmost", True)

        def on_drag(event):
            self._dragging = True
            now = time.time()
            self._drag_samples.append((now, event.x_root, event.y_root))
            self._drag_samples = [s for s in self._drag_samples if now - s[0] <= 0.1]

            nx = event.x_root - self._drag_ox
            ny = event.y_root - self._drag_oy
            self.win.geometry(f"+{nx}+{ny}")
            self._notify_move(nx, ny)

        def on_release(event):
            self._held = False
            if self._dragging:
                self._dragging = False
                now = time.time()
                recent_samples = [s for s in self._drag_samples if now - s[0] <= 0.08]

                if len(recent_samples) >= 2:
                    t0, x0, y0 = recent_samples[0]
                    t1, x1, y1 = recent_samples[-1]
                    dt = max(0.01, t1 - t0)

                    calc_vx = ((x1 - x0) / dt) * 0.03
                    calc_vy = ((y1 - y0) / dt) * 0.03
                    self._vx = max(-35.0, min(35.0, calc_vx))
                    self._vy = max(-35.0, min(35.0, calc_vy))
                else:
                    self._vx = 0.0
                    self._vy = 1.0

                if abs(self._vx) > 3.0 or abs(self._vy) > 3.0:
                    self._set_anim("jump")
                return

            self._click_count += 1
            if self._click_timer:
                self.win.after_cancel(self._click_timer)
            self._click_timer = self.win.after(
                DOUBLE_MS, self._dispatch_click)

        self.canvas.bind("<ButtonPress-1>",   on_press)
        self.canvas.bind("<B1-Motion>",       on_drag)
        self.canvas.bind("<ButtonRelease-1>", on_release)
        self.canvas.bind("<Enter>",           self._on_enter)
        self.canvas.bind("<Leave>",           self._on_leave)

        # ── start ─────────────────────────────────────────────────────────
        self._animate()
        self._physics_tick()
        self._schedule_sleep()
        self._schedule_walk()
        self._schedule_eat()
        self._schedule_idle_bubble()

    def _get_phrases(self, category: str, fallbacks: list[str]) -> list[str]:
        if self.get_data:
            custom = self.get_data().get(category, [])
            if custom:
                return custom
        return fallbacks

    def get_current_size(self) -> tuple[int, int]:
        w = max(20, int(BASE_SPRITE_SIZE[0] * self.scale))
        h = max(20, int(BASE_SPRITE_SIZE[1] * self.scale))
        return (w, h)

    def _load_frames(self, char_dir: Path):
        self.raw_frames  = {}
        self.frames      = {}
        self._flip_cache = {}
        self._char_dir   = char_dir
        
        w, h = self.get_current_size()
        for anim in ANIMATIONS:
            anim_dir = char_dir / anim
            raw_imgs = []
            tk_imgs  = []
            if anim_dir.exists():
                def _frame_sort_key(p: Path) -> int:
                    if p.stem.isdigit():
                        return int(p.stem)
                    m = re.search(r"\d+", p.stem)
                    return int(m.group()) if m else 0

                for f in sorted(anim_dir.glob("*.png"), key=_frame_sort_key):
                    with Image.open(f) as loaded_img:
                        img = loaded_img.convert("RGBA")
                    raw_imgs.append(img)
                    resized = img.resize((w, h), RESAMPLE_LANCZOS)
                    tk_imgs.append(ImageTk.PhotoImage(resized))
            if not tk_imgs:
                blank = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                raw_imgs.append(blank)
                tk_imgs.append(ImageTk.PhotoImage(blank))
            self.raw_frames[anim] = raw_imgs
            self.frames[anim]     = tk_imgs

    def load_character(self, char_dir: Path):
        self._load_frames(char_dir)
        self.frame_index = 0

    def _update_screen_bounds(self):
        """Refreshes visible screen boundaries and floor based on usable desktop work area."""
        w, h = self.get_current_size()
        work = get_desktop_work_area()
        if work:
            left, top, right, bottom = work
            self._min_x = left
            self._max_x = max(left, right - w)
            self._min_y = top
            self.sw = right - left
            self.sh = bottom - top
            # Position floor safely 6px above taskbar
            self._floor_y = max(top, bottom - h - 6)
        else:
            self.sw = self.root.winfo_screenwidth()
            self.sh = self.root.winfo_screenheight()
            self._min_x = 0
            self._max_x = max(0, self.sw - w)
            self._min_y = 0
            self._floor_y = max(0, self.sh - 52 - h)

    def ensure_visible(self, force_x: int | None = None, force_y: int | None = None):
        """Unhides, lifts above other windows, and clamps pet strictly within visible bounds."""
        self._update_screen_bounds()

        if getattr(self, "_is_hidden", False):
            self.win.deiconify()
            self._is_hidden = False
            self._on_floor = True

        w, h = self.get_current_size()
        cur_x = self.win.winfo_x()
        cur_y = self.win.winfo_y()

        target_x = (force_x - w // 2) if force_x is not None else cur_x
        target_y = (force_y - h // 2) if force_y is not None else cur_y

        safe_x = max(self._min_x, min(target_x, self._max_x))
        safe_y = max(self._min_y, min(target_y, self._floor_y))

        self.win.geometry(f"+{safe_x}+{safe_y}")
        self._notify_move(safe_x, safe_y)
        try:
            self.win.lift()
            self.win.attributes("-topmost", True)
        except Exception:
            pass

    def set_scale(self, scale: float):
        self.scale = scale
        w, h = self.get_current_size()
        self.w = w   # keep exposed width in sync
        self.h = h
        self._update_screen_bounds()

        self.frames = {}
        self._flip_cache = {}
        for anim, raw_list in self.raw_frames.items():
            self.frames[anim] = [
                ImageTk.PhotoImage(img.resize((w, h), RESAMPLE_LANCZOS))
                for img in raw_list
            ]

        cur_x = max(self._min_x, min(self.win.winfo_x(), self._max_x))
        cur_y = max(self._min_y, min(self.win.winfo_y(), self._floor_y))
        self.win.geometry(f"{w}x{h}+{cur_x}+{cur_y}")
        self.canvas.config(width=w, height=h)
        self.canvas.coords(self._img_item, w // 2, h // 2)

    def set_speed(self, speed_px: int):
        self.walk_step_px = max(1, speed_px)
        self._base_walk_step_px = self.walk_step_px

    def flip_direction(self):
        self.facing_right = not self.facing_right

    def toggle_hide(self):
        if not hasattr(self, "_is_hidden"):
            self._is_hidden = False

        if self._is_hidden:
            self.ensure_visible()
            self._set_anim("jump")
        else:
            self.win.withdraw()
            self._is_hidden = True

    def summon_to_cursor(self):
        self._update_screen_bounds()
        if getattr(self, "_is_hidden", False):
            self.win.deiconify()
            self._is_hidden = False

        mx = self.win.winfo_pointerx()
        my = self.win.winfo_pointery()
        w, h = self.get_current_size()

        safe_x = max(self._min_x, min(mx - w // 2, self._max_x))
        safe_y = max(self._min_y, min(my - h // 2, self._floor_y))

        self.win.geometry(f"{w}x{h}+{safe_x}+{safe_y}")
        try:
            self.win.lift()
            self.win.attributes("-topmost", True)
        except Exception:
            pass
        self._vx = 0.0
        self._vy = 0.5
        self._on_floor = False
        self._set_anim("jump")

    def get_collar_position(self) -> tuple[int, int]:
        """Returns the screen coordinates for leash attachment at the pet's collar."""
        if not self.win.winfo_exists():
            return (0, 0)
        px, py = self.win.winfo_x(), self.win.winfo_y()
        w, h = self.get_current_size()
        # Collar is center horizontal and slightly above pet center
        return (px + w // 2, py + int(h * 0.35))

    def leash_pull(self, step_x: int, step_y: int, facing_right: bool):
        """Steps the pet in the direction it is pulled by the leash and triggers walk animation."""
        if not self.win.winfo_exists() or self._held or getattr(self, "_is_hidden", False):
            return

        # Wake pet up if sleeping or idling
        if getattr(self, "_sleeping", False):
            self._sleeping = False
            self._wake_up()

        self.facing_right = facing_right
        self._state = "walk"
        self._set_anim("walk")

        self._update_screen_bounds()
        cur_x = self.win.winfo_x()
        cur_y = self.win.winfo_y()

        nx = max(self._min_x, min(cur_x + step_x, self._max_x))
        ny = max(self._min_y, min(cur_y + step_y, self._floor_y))
        self.win.geometry(f"+{nx}+{ny}")
        self._notify_move(nx, ny)
        self._vx = 0.0
        self._vy = 0.0


    def _animate(self):
        if self.chase_mouse and self._state in ("idle", "walk") and not self._busy():
            target_x = self.win.winfo_pointerx()
            cur_x = self.win.winfo_x()
            
            if abs(target_x - cur_x) > 40:
                if self._state != "walk":
                    self._cancel_id("_walk_sched_id")
                    self._state = "walk"
                    self._set_anim("walk")
            else:
                if self._state != "idle":
                    self._state = "idle"
                    self._set_anim("idle")
                    self.step_count = 0

        anim   = self.current_anim
        frames = self.frames[anim]
        self.frame_index %= len(frames)

        if anim == "walk" and not self.facing_right:
            frame = self._get_flipped(anim, self.frame_index)
        else:
            frame = frames[self.frame_index]

        self.canvas.itemconfig(self._img_item, image=frame)
        self._current_photo = frame   
        self.frame_index += 1

        if self.is_jumping and self.frame_index >= len(self.frames["jump"]):
            self.is_jumping   = False
            self.frame_index  = 0
            if self._sleeping:
                self.current_anim = "sleep"
            elif self._is_hovered:
                self.current_anim = "idle"
            elif self.continuous_patrol or self._state == "walk":
                self.current_anim = "walk"
            else:
                self.current_anim = "idle"

        delay = JUMP_MS if anim == "jump" else FRAME_MS
        if self.win.winfo_exists():
            self.win.after(delay, self._animate)

        if anim == "walk":
            self._do_walk_step()

    def _get_flipped(self, anim: str, idx: int) -> ImageTk.PhotoImage:
        key = f"{anim}_flip_{idx}_{self.scale}"
        if key not in self._flip_cache:
            w, h = self.get_current_size()
            if anim in self.raw_frames and idx < len(self.raw_frames[anim]):
                img = self.raw_frames[anim][idx].transpose(FLIP_HORIZONTAL)
                resized = img.resize((w, h), RESAMPLE_LANCZOS)
                self._flip_cache[key] = ImageTk.PhotoImage(resized)
            else:
                self._flip_cache[key] = self.frames[anim][idx % len(self.frames[anim])]
        return self._flip_cache[key]

    def _physics_tick(self):
        if not self.win.winfo_exists():
            return
        if self._is_hidden:
            self.win.after(PHYSICS_MS, self._physics_tick)
            return
        if not self._held:
            cur_x = self.win.winfo_x()
            cur_y = self.win.winfo_y()

            self._vy += self.gravity

            if self._on_floor:
                self._vx *= FLOOR_FRICTION_X
            else:
                self._vx *= AIR_FRICTION_X

            if abs(self._vx) < MIN_STOP_VX:
                self._vx = 0.0

            new_x = cur_x + self._vx
            new_y = cur_y + self._vy

            # Horizontal Bounce
            if new_x <= self._min_x:
                new_x = self._min_x
                self._vx = -self._vx * self.bounciness
                self.facing_right = True
            elif new_x >= self._max_x:
                new_x = self._max_x
                self._vx = -self._vx * self.bounciness
                self.facing_right = False

            # Ceiling Bounce
            if new_y <= self._min_y:
                new_y = self._min_y
                self._vy = -self._vy * self.bounciness

            # Floor Bounce
            if new_y >= self._floor_y:
                new_y = self._floor_y
                self._vy = -self._vy * self.bounciness
                if abs(self._vy) < MIN_BOUNCE_VY:
                    self._vy = 0.0
                    self._on_floor = True
                    if not self.is_jumping and self.current_anim == "jump":
                        self._set_anim("idle")
                else:
                    self._on_floor = False
            else:
                self._on_floor = False

            if int(new_x) != cur_x or int(new_y) != cur_y:
                self.win.geometry(f"+{int(new_x)}+{int(new_y)}")
                self._notify_move(int(new_x), int(new_y))

        if self.win.winfo_exists():
            self.win.after(PHYSICS_MS, self._physics_tick)

    def set_anim(self, anim: str):
        self._set_anim(anim)

    def _set_anim(self, anim: str):
        if anim != self.current_anim:
            self.current_anim = anim
            self.frame_index  = 0

    def _cancel_id(self, attr: str):
        aid = getattr(self, attr, None)
        if aid:
            try:
                self.win.after_cancel(aid)
            except Exception:
                pass
            setattr(self, attr, None)

    def _busy(self) -> bool:
        return self._held or not self._on_floor or abs(self._vx) > 0.5 or getattr(self, "_sleeping", False)

    def _schedule_sleep(self):
        self._cancel_id("_sleep_sched_id")  
        delay = random.randint(SLEEP_MIN_MS, SLEEP_MAX_MS)
        if self.win.winfo_exists():
            self._sleep_sched_id = self.win.after(delay, self._start_sleep)

    def _start_sleep(self):
        if self._busy() or self._state in ("eat",):
            if self.win.winfo_exists():
                self._sleep_sched_id = self.win.after(60_000, self._start_sleep)
            return
        self._state    = "sleep"
        self._sleeping = True
        self._walk_target_x = None
        self._set_anim("sleep")
        if self.win.winfo_exists():
            self._wake_sched_id = self.win.after(SLEEP_DUR_MS, self._wake_up)

    def _wake_up(self):
        if not self._sleeping:
            return
        self._sleeping = False
        self._cancel_id("_wake_sched_id")
        self._state = "walk"
        self._set_anim("walk")
        self._pick_walk_target()
        self._schedule_sleep()

    def _schedule_walk(self):
        self._cancel_id("_walk_sched_id")  
        delay = random.randint(WALK_MIN_MS, WALK_MAX_MS)
        if self.win.winfo_exists():
            self._walk_sched_id = self.win.after(delay, self._start_walk)

    def _start_walk(self):
        if self._busy() or self._sleeping or self._state == "eat":
            if self.win.winfo_exists():
                self._walk_sched_id = self.win.after(30_000, self._start_walk)
            return
        self._state = "walk"
        self._set_anim("walk")
        self.step_count = 0   # Bug #10 fix: reset complaint counter on every new walk
        self._pick_walk_target()

    def toggle_mouse_chase(self) -> bool:
        self.chase_mouse = not self.chase_mouse
        if self.chase_mouse:
            self.continuous_patrol = False
            self._cancel_id("_walk_sched_id")
        else:
            if self._state == "walk":
                self._state = "idle"
                self._set_anim("idle")
                self.step_count = 0
            self._schedule_walk() 
        return self.chase_mouse

    def toggle_continuous_patrol(self) -> bool:
        self.continuous_patrol = not self.continuous_patrol
        if self.continuous_patrol:
            self.chase_mouse = False
            self._cancel_id("_walk_sched_id")
            if self._state not in ("walk", "eat") and not self._sleeping and not self._busy():
                self._state = "walk"
                self._set_anim("walk")
                self._pick_walk_target()
        else:
            if self._state == "walk":
                self._state = "idle"
                self._set_anim("idle")
                self.step_count = 0 
            self._schedule_walk() 
        return self.continuous_patrol

    def _pick_walk_target(self):
        self.facing_right = random.choice([True, False])
        self._walk_duration_steps = random.randint(150, 400)

    def _do_walk_step(self):
        if self._is_hovered or self._busy():
            return

        cur_x = self.win.winfo_x()
        cur_y = self.win.winfo_y()
        w, _ = self.get_current_size()

        self.step_count += 1
        if self.step_count >= MAX_WALK_STEPS:
            phrases = self._get_phrases("complain_messages", COMPLAIN_MESSAGES)
            self._fire_bubble(random.choice(phrases))
            self.step_count = 0

        if self.chase_mouse:
            target_x = self.win.winfo_pointerx()
            diff = target_x - cur_x
            self.facing_right = diff > 0
            step = self.walk_step_px if diff > 0 else -self.walk_step_px
            next_x = max(self._min_x, min(cur_x + step, self._max_x))
            self.win.geometry(f"+{next_x}+{cur_y}")
            self._notify_move(next_x, cur_y)
                
        else:
            if not hasattr(self, '_walk_duration_steps'):
                self._walk_duration_steps = 200

            if not self.continuous_patrol:
                self._walk_duration_steps -= 1
                if self._walk_duration_steps <= 0:
                    self._state = "idle"
                    self._set_anim("idle")
                    self.step_count = 0
                    self._schedule_walk()
                    return

            step = self.walk_step_px if self.facing_right else -self.walk_step_px
            next_x = cur_x + step
            
            if next_x <= self._min_x:
                next_x = self._min_x
                self.facing_right = True
                if getattr(self, "_panic_sched_id", None):
                    self._cancel_id("_panic_sched_id")
                    self.walk_step_px = getattr(self, "_base_walk_step_px", 2)
            elif next_x >= self._max_x:
                next_x = self._max_x
                self.facing_right = False
                if getattr(self, "_panic_sched_id", None):
                    self._cancel_id("_panic_sched_id")
                    self.walk_step_px = getattr(self, "_base_walk_step_px", 2)

            self.win.geometry(f"+{next_x}+{cur_y}")
            self._notify_move(next_x, cur_y)

    def _schedule_eat(self):
        self._cancel_id("_eat_sched_id")
        if self.win.winfo_exists():
            self._eat_sched_id = self.win.after(EAT_EVERY_MS, self._start_eat)

    def _start_eat(self):
        if self._busy() or self._sleeping:
            if self.win.winfo_exists():
                self._eat_sched_id = self.win.after(60_000, self._start_eat)
            return
        self._walk_target_x = None
        self._state = "eat"
        self._set_anim("eat")
        if self.win.winfo_exists():
            self._eat_end_id = self.win.after(EAT_DUR_MS, self._end_eat)

    def _end_eat(self):
        self._state = "idle"
        self._set_anim("idle")
        self._schedule_eat()

    def feed(self):
        if self._held or self._sleeping:
            return
        self._cancel_id("_eat_end_id")
        self._walk_target_x = None
        self._state = "eat"
        self._set_anim("eat")
        eat_dur = max(1500, len(self.frames.get("eat", [None])) * FRAME_MS * 2)
        if self.win.winfo_exists():
            self._eat_end_id = self.win.after(eat_dur, self._end_eat)

    def _on_enter(self, event):
        self._is_hovered = True
        try:
            self.win.lift()
            self.win.attributes("-topmost", True)
        except Exception:
            pass
        if not self.is_jumping and not self._held and not self._sleeping:
            self.is_jumping = True
            self._set_anim("jump")
            phrases = self._get_phrases("pat_messages", PAT_MESSAGES)
            self._fire_bubble(random.choice(phrases))

    def _on_leave(self, event):
        self._is_hovered = False
        if not self._sleeping and not self.is_jumping:
            if self.continuous_patrol or self._state == "walk":
                self._set_anim("walk")

    def _dispatch_click(self):
        count = self._click_count
        self._click_count = 0
        self._click_timer = None
        try:
            self.win.lift()
            self.win.attributes("-topmost", True)
        except Exception:
            pass

        if count >= 2:
            self.on_double_click()
            return

        if self._sleeping:
            self._wake_up()
            phrases = self._get_phrases("sleep_messages", SLEEP_MESSAGES)
            self._fire_bubble(random.choice(phrases))
        elif self._state == "eat":
            phrases = self._get_phrases("eat_messages", EAT_MESSAGES)
            self._fire_bubble(random.choice(phrases))
        else:
            if not self.is_jumping and not self._held:
                self.is_jumping = True
                self._set_anim("jump")
            phrases = self._get_phrases("pat_messages", PAT_MESSAGES)
            self._fire_bubble(random.choice(phrases))

    def _fire_bubble(self, message: str):
        if self.on_bubble:
            self.on_bubble(message)

    def _schedule_idle_bubble(self):
        if self.win.winfo_exists():
            self.win.after(IDLE_BUBBLE_CHECK_MS, self._maybe_idle_bubble)

    def _maybe_idle_bubble(self):
        if self._state == "idle" and self._on_floor and not self._held:
            if random.random() < self.chatter_chance:
                phrases = self._get_phrases("idle_messages", IDLE_MESSAGES)
                self._fire_bubble(random.choice(phrases))
        self._schedule_idle_bubble()

    def get_position(self) -> tuple[int, int]:
        return self.win.winfo_x(), self.win.winfo_y()

    def set_position(self, x: int, y: int):
        self._update_screen_bounds()
        safe_x = max(self._min_x, min(x, self._max_x))
        safe_y = max(self._min_y, min(y, self._floor_y))
        self.win.geometry(f"+{safe_x}+{safe_y}")
        self._notify_move(safe_x, safe_y)

    def _notify_move(self, x: int, y: int):
        fn = getattr(self, "on_move", None)
        if callable(fn):
            try:
                fn(x, y, getattr(self, "w", 60))
            except Exception:
                pass

    def whip_hit(self, crack_x: int, crack_y: int, origin_x: int | None = None, origin_y: int | None = None):
        """Reacts when struck by the whip."""
        self.ensure_visible()
        if not self.win.winfo_exists():
            return

        # Wake up or interrupt eating immediately
        if self._sleeping:
            self._wake_up()
        if self._state == "eat":
            self._cancel_id("_eat_end_id")
            self._cancel_id("_eat_sched_id")
            self._state = "walk"
            self._schedule_eat()

        cur_x = self.win.winfo_x()
        w, h = self.get_current_size()
        pet_cx = cur_x + w // 2

        # Fling pet away from whip origin (cursor) or crack point
        ref_x = origin_x if origin_x is not None else crack_x
        direction = 1 if pet_cx >= ref_x else -1
        if abs(pet_cx - ref_x) < 8:
            direction = random.choice([1, -1])

        fling_vx = direction * random.uniform(16.0, 24.0)
        fling_vy = -random.uniform(14.0, 20.0)

        self._held = False
        self._on_floor = False
        self._vx = fling_vx
        self._vy = fling_vy
        self.facing_right = (direction > 0)

        self.is_jumping = True
        self._set_anim("jump")

        # Comedic scream speech bubble
        phrases = self._get_phrases("whip_messages", WHIP_MESSAGES)
        self._fire_bubble(random.choice(phrases))

        # Panic sprint for a few seconds
        self._start_panic_sprint(direction)

    def _start_panic_sprint(self, direction: int):
        self._cancel_id("_panic_sched_id")
        base = getattr(self, "_base_walk_step_px", 2)
        sprint_speed = max(8, base * 4)

        self.walk_step_px = sprint_speed
        self.facing_right = (direction > 0)
        self._walk_duration_steps = 180
        self._state = "walk"

        def _end_panic():
            self.walk_step_px = getattr(self, "_base_walk_step_px", 2)
            self._panic_sched_id = None

        self._panic_sched_id = self.win.after(3500, _end_panic)

    def bomb_blast(self, bomb_x: int, bomb_y: int, blast_power: float = 35.0):
        """Reacts when caught in a bomb explosion: launches pet radially away with high velocity."""
        self.ensure_visible()
        if not self.win.winfo_exists():
            return

        # Interrupt sleeping or eating immediately
        if self._sleeping:
            self._wake_up()
        if self._state == "eat":
            self._cancel_id("_eat_end_id")
            self._cancel_id("_eat_sched_id")
            self._state = "walk"
            self._schedule_eat()

        cur_x = self.win.winfo_x()
        cur_y = self.win.winfo_y()
        w, h = self.get_current_size()
        pet_cx = cur_x + w // 2
        pet_cy = cur_y + h // 2

        dx = pet_cx - bomb_x
        dy = pet_cy - bomb_y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < 8:
            direction = random.choice([1, -1])
            dx = direction * 8
            dist = 8.0
        else:
            direction = 1 if dx >= 0 else -1

        norm_x = dx / dist

        # Distance falloff:
        # Point-blank (<120px): full force
        # Mid-range (120px - 500px): smooth decay
        # Far-range (>500px): shockwave
        if dist < 120:
            scale = 1.0
        elif dist < 500:
            scale = 1.0 - (dist - 120) / 380 * 0.55
        else:
            scale = 0.45

        effective_power = blast_power * scale

        # Fling outward and launch high into the sky
        fling_vx = norm_x * effective_power * random.uniform(0.9, 1.25)
        fling_vy = -max(10.0, effective_power * random.uniform(0.85, 1.2))

        # Clamp max velocities dynamically according to configured blast_power
        max_vel = max(45.0, blast_power * 1.6)
        self._vx = max(-max_vel, min(max_vel, fling_vx))
        self._vy = max(-max_vel, min(max_vel, fling_vy))

        self._held = False
        self._on_floor = False
        self.facing_right = (direction > 0)
        self.is_jumping = True
        self._set_anim("jump")

        # Comedic explosion speech bubble
        phrases = self._get_phrases("bomb_messages", BOMB_MESSAGES)
        self._fire_bubble(random.choice(phrases))

        # Start panic sprint
        self._start_panic_sprint(direction)