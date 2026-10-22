"""
speech_bubble.py
A small comic-style speech bubble that appears above the pet
when a countdown timer fires. Auto-dismisses after a few seconds.
"""

import tkinter as tk
from pathlib import Path
import sys

try:
    import paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths

import themes

CHROMA       = "#010101"
AUTO_HIDE_MS = 4000   # bubble disappears after 4 s
MAX_W        = 180    # max bubble width in px

# Fonts available for the speech bubble (family name → display label)
BUBBLE_FONTS = [
    "Georgia",
    "Comic Sans MS",
    "Arial",
    "Helvetica",
    "Verdana",
    "Trebuchet MS",
    "Courier New",
    "Times New Roman",
    "Segoe UI",
    "Tahoma",
    "Palatino Linotype",
    "Impact",
]
DEFAULT_FONT_FAMILY = "Georgia"
DEFAULT_FONT_SIZE   = 8


class SpeechBubble:
    def __init__(self, root: tk.Tk, on_click=None, get_pet_pos=None):
        self.root = root
        self.on_click = on_click
        self.get_pet_pos = get_pet_pos
        self._after_id = None
        self._track_timer = None

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", CHROMA)
        self.win.configure(bg=CHROMA)
        self.win.withdraw()

        self._visible = False
        self._bw = 60
        self._bh = 40
        self._pet_w = 60

    # ── show ─────────────────────────────────────────────────────────────
    def show(self, message: str, pet_x: int, pet_y: int, pet_w: int = 60):
        """Display bubble above the pet at (pet_x, pet_y)."""
        t = themes.get()

        # Safe fallbacks: a missing theme key must never silence the pet.
        bub_bg  = t.get("bubble_bg")  or t.get("bg_card", "#ffffff")
        bub_out = t.get("bubble_out") or t.get("border",  "#333333")
        txt_fg  = t.get("bubble_fg")  or t.get("fg_main", "#333333")

        font_family = t.get("bubble_font_family") or DEFAULT_FONT_FAMILY
        raw_size = t.get("bubble_font_size")
        try:
            font_size = int(raw_size) if raw_size is not None and int(raw_size) > 0 else DEFAULT_FONT_SIZE
        except (ValueError, TypeError):
            font_size = DEFAULT_FONT_SIZE
        font_msg    = (font_family, font_size, "bold")

        for w in self.win.winfo_children():
            w.destroy()

        PAD  = 8
        TAIL = 8

        outer = tk.Frame(self.win, bg=CHROMA)
        outer.pack()

        canvas = tk.Canvas(outer, bg=CHROMA, highlightthickness=0)
        canvas.pack()

        # measure text
        tmp = tk.Label(self.win, text=message, font=font_msg,
                       wraplength=MAX_W - PAD * 2)
        tmp.update_idletasks()
        tw = min(tmp.winfo_reqwidth() + PAD * 2, MAX_W)
        th = tmp.winfo_reqheight() + PAD * 2
        tmp.destroy()

        bw = max(tw, 60)
        bh = th + TAIL + 2

        self._bw = bw
        self._bh = bh
        self._pet_w = pet_w

        canvas.config(width=bw, height=bh)

        # bubble body
        _rounded_rect(canvas, 0, 0, bw, bh - TAIL, 8,
                      fill=bub_bg, outline=bub_out, width=2)

        # tail
        mid = bw // 2
        canvas.create_polygon(
            mid - 6, bh - TAIL,
            mid + 6, bh - TAIL,
            mid,     bh,
            fill=bub_bg, outline=bub_out, width=2,
        )
        # cover seam
        canvas.create_rectangle(
            mid - 5, bh - TAIL - 1,
            mid + 5, bh - TAIL + 1,
            fill=bub_bg, outline=bub_bg,
        )

        lbl = tk.Label(
            canvas, text=message, font=font_msg,
            bg=bub_bg, fg=txt_fg,
            wraplength=MAX_W - PAD * 2, justify="center",
            padx=PAD, pady=PAD // 2,
        )
        canvas.create_window(bw // 2, (bh - TAIL) // 2, window=lbl)

        # Click speech bubble to find pet or dismiss
        def _handle_click(event=None):
            if self.on_click:
                self.on_click()
            self.hide()

        canvas.config(cursor="hand2")
        canvas.bind("<Button-1>", _handle_click)
        lbl.config(cursor="hand2")
        lbl.bind("<Button-1>", _handle_click)
        outer.bind("<Button-1>", _handle_click)
        self.win.bind("<Button-1>", _handle_click)

        self.win.update_idletasks()
        self.reposition(pet_x, pet_y, pet_w)
        try:
            self.win.lift()
            self.win.attributes("-topmost", True)
        except Exception:
            pass
        self.win.deiconify()
        self._visible = True
        self._start_tracking()

        # longer auto-hide for multi-word messages
        duration = max(AUTO_HIDE_MS, len(message) * 80)
        if self._after_id:
            try:
                self.win.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.win.after(duration, self.hide)

    def reposition(self, pet_x: int, pet_y: int, pet_w: int | None = None):
        """Updates bubble position so it stays directly above the moving pet."""
        if not self.win.winfo_exists():
            return
        if pet_w is not None:
            self._pet_w = pet_w
        bw = getattr(self, "_bw", 60)
        bh = getattr(self, "_bh", 40)
        pw = getattr(self, "_pet_w", 60)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        x = pet_x + pw // 2 - bw // 2
        y = pet_y - bh - 4
        x = max(4, min(x, sw - bw - 4))
        y = max(4, min(y, sh - bh - 4))
        self.win.geometry(f"+{x}+{y}")

    def _start_tracking(self):
        self._cancel_tracking()
        self._track_step()

    def _track_step(self):
        if not self._visible or not self.win.winfo_exists():
            self._track_timer = None
            return
        if self.get_pet_pos:
            try:
                pos = self.get_pet_pos()
                if pos:
                    if len(pos) >= 3:
                        self.reposition(pos[0], pos[1], pos[2])
                    else:
                        self.reposition(pos[0], pos[1])
                else:
                    self.hide()
                    return
            except Exception:
                pass
        self._track_timer = self.win.after(20, self._track_step)

    def _cancel_tracking(self):
        tid = getattr(self, "_track_timer", None)
        if tid is not None:
            try:
                self.win.after_cancel(tid)
            except Exception:
                pass
            self._track_timer = None

    def hide(self):
        self._cancel_tracking()
        if self._after_id:
            try:
                self.win.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self._visible = False
        try:
            if self.win.winfo_exists():
                self.win.withdraw()
        except Exception:
            pass

    def apply_theme(self):
        """Re-show with current theme if visible — called on theme change."""
        pass  # bubble is rebuilt on each show() call, nothing extra needed


# ── helper ────────────────────────────────────────────────────────────────
def _rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
        x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)