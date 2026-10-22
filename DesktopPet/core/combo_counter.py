"""
combo_counter.py

Arcade fighting game style combo counter for DesktopPet whip interactions.
Renders high-impact badges matching the classic arcade style:
- Collegiate/octagonal block numbers in crimson/magenta with white border + black outline
- Bold uppercase white "HITS" / "HIT" with black outline
- Elastic spring scale pop on hit, dynamic hit sparks, and floating tracking above pet.
"""

from __future__ import annotations

import math
import random
import time
from pathlib import Path
import tkinter as tk

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageTk

try:
    import paths
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths


class SparkParticle:
    """Dynamic hit spark particle that flies radially outward from impact."""
    __slots__ = ("x", "y", "vx", "vy", "color", "size", "life", "max_life")

    def __init__(self, x: float, y: float, vx: float, vy: float, color: str, size: float, life: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 220.0 * dt  # subtle gravity
        decay = pow(0.94, dt * 60.0)
        self.vx *= decay
        self.vy *= decay
        self.life -= dt
        return self.life > 0.0


class ComboBadgeRenderer:
    """Generates and caches PIL images and Tkinter PhotoImages for combo counts."""

    def __init__(self):
        self._cache: dict[tuple[int, int], ImageTk.PhotoImage] = {}
        self._pil_cache: dict[int, Image.Image] = {}

        # Resolve best available bold font for "HITS" text
        font_candidates = [
            r"C:\Windows\Fonts\impact.ttf",
            r"C:\Windows\Fonts\ariblk.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
        ]
        self.hits_font: ImageFont.FreeTypeFont | ImageFont.ImageFont | None = None
        for fp in font_candidates:
            if Path(fp).exists():
                try:
                    self.hits_font = ImageFont.truetype(fp, 68)
                    break
                except Exception:
                    pass
        if self.hits_font is None:
            self.hits_font = ImageFont.load_default()

    def _draw_octagonal_digit(self, char: str, w: int = 70, h: int = 126, chamfer: int = 18, lw: int = 19) -> Image.Image:
        """Draws an isolated binary alpha mask for an athletic octagonal block digit."""
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)

        outer_poly = [
            (chamfer, 0), (w - chamfer, 0),
            (w, chamfer), (w, h - chamfer),
            (w - chamfer, h), (chamfer, h),
            (0, h - chamfer), (0, chamfer)
        ]

        if char == "0":
            draw.polygon(outer_poly, fill=255)
            # octagonal inner hole
            draw.polygon([
                (lw + chamfer // 2, lw), (w - lw - chamfer // 2, lw),
                (w - lw, lw + chamfer // 2), (w - lw, h - lw - chamfer // 2),
                (w - lw - chamfer // 2, h - lw), (lw + chamfer // 2, h - lw),
                (lw, h - lw - chamfer // 2), (lw, lw + chamfer // 2)
            ], fill=0)

        elif char == "1":
            bar_w = lw + 4
            bx = (w - bar_w) // 2 + 4
            draw.rectangle([bx, 0, bx + bar_w, h], fill=255)
            # Top-left serif hook
            draw.polygon([(bx, 0), (bx - 18, 24), (bx, 24)], fill=255)

        elif char == "2":
            draw.polygon([
                (chamfer, 0), (w - chamfer, 0), (w, chamfer), (w, h // 2 - 2),
                (lw + 6, h - lw), (w, h - lw), (w, h), (0, h),
                (0, h - chamfer - 6), (w - lw - 2, h // 2 - 4), (w - lw, h // 2 - 10),
                (w - lw, chamfer + 2), (w - chamfer, lw), (chamfer, lw), (0, chamfer + 8), (0, chamfer)
            ], fill=255)

        elif char == "3":
            draw.polygon(outer_poly, fill=255)
            draw.rectangle([lw, lw, w - lw, h // 2 - lw // 2 + 2], fill=0)
            draw.rectangle([lw, h // 2 + lw // 2 - 2, w - lw, h - lw], fill=0)
            draw.rectangle([0, lw, lw, h // 2 - lw // 2 + 2], fill=0)
            draw.rectangle([0, h // 2 + lw // 2 - 2, lw, h - lw], fill=0)

        elif char == "4":
            draw.polygon([
                (0, 0), (lw, 0), (lw, h // 2 - lw // 2),
                (w - lw, h // 2 - lw // 2), (w - lw, 0), (w, 0),
                (w, h), (w - lw, h), (w - lw, h // 2 + lw // 2),
                (0, h // 2 + lw // 2)
            ], fill=255)
            draw.polygon([
                (lw, h // 2 - lw // 2), (w - lw, h // 2 - lw // 2),
                (w - lw, 0), (lw, h // 2 - lw // 2)
            ], fill=0)

        elif char == "5":
            draw.polygon([
                (0, 0), (w, 0), (w, lw),
                (lw, lw), (lw, h // 2 - 4),
                (w - chamfer, h // 2 - 4), (w, h // 2 - 4 + chamfer),
                (w, h - chamfer), (w - chamfer, h), (0, h),
                (0, h - lw), (w - lw, h - lw),
                (w - lw, h // 2 + lw - 4), (0, h // 2 + lw - 4)
            ], fill=255)

        elif char == "6":
            draw.polygon(outer_poly, fill=255)
            # Top open notch
            draw.rectangle([lw, 0, w, h // 2 - lw // 2 + 2], fill=0)
            # Bottom hole
            draw.rectangle([lw, h // 2 + lw // 2 - 2, w - lw, h - lw], fill=0)

        elif char == "7":
            draw.polygon([
                (0, 0), (w, 0), (w, h),
                (w - lw - 4, h), (w - lw - 4, lw), (0, lw)
            ], fill=255)

        elif char == "8":
            draw.polygon(outer_poly, fill=255)
            draw.rectangle([lw, lw, w - lw, h // 2 - lw // 2 + 2], fill=0)
            draw.rectangle([lw, h // 2 + lw // 2 - 2, w - lw, h - lw], fill=0)

        elif char == "9":
            draw.polygon(outer_poly, fill=255)
            # Top enclosed hole
            draw.rectangle([lw, lw, w - lw, h // 2 - 4], fill=0)
            # Bottom left open notch
            draw.rectangle([0, h // 2 + 4, w - lw, h - lw], fill=0)

        else:
            draw.polygon(outer_poly, fill=255)

        return mask

    def render_base_pil(self, count: int) -> Image.Image:
        """Generates the master unscaled PIL RGBA badge for a given count."""
        digit_w = 72
        digit_h = 128
        spacing = 9
        count_str = str(max(1, count))
        num_digits = len(count_str)

        digits_total_w = num_digits * digit_w + (num_digits - 1) * spacing
        digits_total_h = digit_h

        # Render individual digit masks
        digit_masks = [self._draw_octagonal_digit(c, digit_w, digit_h) for c in count_str]

        # Determine HITS text
        hits_text = "HIT" if count == 1 else "HITS"
        dummy = Image.new("RGBA", (1, 1))
        d_draw = ImageDraw.Draw(dummy)
        bbox = d_draw.textbbox((0, 0), hits_text, font=self.hits_font)
        hits_w = int(bbox[2] - bbox[0])
        hits_h = int(bbox[3] - bbox[1])

        pad = 26
        hits_gap = 14
        total_w = int(pad * 2 + digits_total_w + hits_gap + hits_w)
        total_h = int(pad * 2 + max(digits_total_h, hits_h))

        canvas = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))

        digits_x = int(pad)
        digits_y = int(pad + (total_h - 2 * pad - digits_total_h) // 2)

        hits_x = int(digits_x + digits_total_w + hits_gap)
        # Align bottom of HITS with bottom of digits
        hits_y = int(digits_y + digits_total_h - hits_h - 4)

        # Assemble full digits mask
        combined_digits = Image.new("L", (total_w, total_h), 0)
        for i, d_mask in enumerate(digit_masks):
            cx = int(digits_x + i * (digit_w + spacing))
            combined_digits.paste(d_mask, (cx, digits_y))

        # Assemble HITS text mask
        hits_mask = Image.new("L", (total_w, total_h), 0)
        h_draw = ImageDraw.Draw(hits_mask)
        h_draw.text((hits_x - int(bbox[0]), hits_y - int(bbox[1])), hits_text, fill=255, font=self.hits_font)

        # 1. Thick Outer Black Stroke + Drop Shadow
        digits_black_stroke = combined_digits.filter(ImageFilter.MaxFilter(19))
        hits_black_stroke = hits_mask.filter(ImageFilter.MaxFilter(15))
        combined_black = Image.fromarray(
            np.maximum(np.array(digits_black_stroke), np.array(hits_black_stroke))
        )
        black_color = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 255))
        canvas.paste(black_color, (0, 0), combined_black)

        # 2. Solid White Inner Border for Digits
        digits_white_stroke = combined_digits.filter(ImageFilter.MaxFilter(11))
        white_color = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
        canvas.paste(white_color, (0, 0), digits_white_stroke)

        # 3. Rich Crimson / Magenta Gradient Fill inside Digits
        grad_arr = np.zeros((total_h, total_w, 4), dtype=np.uint8)
        for y in range(total_h):
            t = y / max(1, total_h)
            # Crimson gradient: #d01060 (top) -> #860028 (bottom)
            r = int(212 * (1 - t) + 128 * t)
            g = int(14 * (1 - t) + 0 * t)
            b = int(92 * (1 - t) + 36 * t)
            grad_arr[y, :, 0] = r
            grad_arr[y, :, 1] = g
            grad_arr[y, :, 2] = b
            grad_arr[y, :, 3] = 255

        grad_img = Image.fromarray(grad_arr, "RGBA")
        canvas.paste(grad_img, (0, 0), combined_digits)

        # 4. Subtle Inner Pink Neon Glow
        eroded = combined_digits.filter(ImageFilter.MinFilter(5))
        inner_glow_mask = Image.fromarray(np.maximum(0, np.array(combined_digits) - np.array(eroded)))
        glow_color = Image.new("RGBA", (total_w, total_h), (255, 110, 190, 180))
        canvas.paste(glow_color, (0, 0), inner_glow_mask)

        # 5. Crisp Solid White HITS Text
        canvas.paste(white_color, (0, 0), hits_mask)

        # 6. Warm Arcade Impact Flare at Bottom Right
        flare_x = total_w - pad - 12
        flare_y = total_h - pad - 6
        glow = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow)
        radius = 55
        for r in range(radius, 0, -2):
            t = r / radius
            alpha = int(135 * (1.0 - t ** 0.65))
            red = 255
            green = int(255 * (1 - t) + 130 * t)
            blue = int(220 * (1 - t) + 30 * t)
            g_draw.ellipse(
                [flare_x - r, flare_y - int(r * 0.7), flare_x + r, flare_y + int(r * 0.7)],
                fill=(red, green, blue, alpha)
            )
        canvas = Image.alpha_composite(canvas, glow)

        # Crop tightly to non-transparent bounding box with 4px border
        bbox_cropped = canvas.getbbox()
        if bbox_cropped:
            x1 = max(0, bbox_cropped[0] - 4)
            y1 = max(0, bbox_cropped[1] - 4)
            x2 = min(total_w, bbox_cropped[2] + 4)
            y2 = min(total_h, bbox_cropped[3] + 4)
            canvas = canvas.crop((x1, y1, x2, y2))

        return canvas

    def get_photo_image(self, count: int, scale: float = 1.0) -> ImageTk.PhotoImage:
        """Returns a cached Tkinter PhotoImage for the specified count and scale."""
        # Quantize scale to 2 decimals to ensure high cache hit rate
        q_scale = round(scale, 2)
        key = (count, int(q_scale * 100))

        if key in self._cache:
            return self._cache[key]

        # Prevent unbounded cache growth
        if len(self._cache) >= 64:
            self._cache.pop(next(iter(self._cache)))

        if count not in self._pil_cache:
            if len(self._pil_cache) >= 32:
                self._pil_cache.pop(next(iter(self._pil_cache)))
            self._pil_cache[count] = self.render_base_pil(count)

        base = self._pil_cache[count]
        if abs(scale - 1.0) > 0.02:
            new_w = max(1, int(base.width * scale))
            new_h = max(1, int(base.height * scale))
            scaled = base.resize((new_w, new_h), Image.Resampling.BILINEAR)
        else:
            scaled = base

        photo = ImageTk.PhotoImage(scaled)
        self._cache[key] = photo
        return photo


class ComboCounter:
    """
    Manages interactive whip combo state, spring physics pop animations,
    floating pet tracking, and screen rendering.
    """

    def __init__(self):
        self.renderer = ComboBadgeRenderer()
        self.combo: int = 0
        self.active: bool = False
        self.last_hit_time: float = 0.0
        self.combo_timeout: float = 2.8  # Seconds before combo resets
        self.fade_duration: float = 0.45

        # Animation state
        self.current_scale: float = 1.0
        self.target_scale: float = 1.0
        self.scale_velocity: float = 0.0

        # Position tracking
        self.x: float = 0.0
        self.y: float = 0.0
        self.target_x: float = 0.0
        self.target_y: float = 0.0
        self.opacity: float = 1.0

        # Dynamic spark particles
        self.sparks: list[SparkParticle] = []

        # Retained Tkinter references to prevent garbage collection
        self._active_photo: ImageTk.PhotoImage | None = None

    def register_hit(self, hit_x: int, hit_y: int, pet_rect: tuple[int, int, int, int] | None = None) -> int:
        """Called whenever a whip crack strikes the pet."""
        now = time.time()
        if self.active and (now - self.last_hit_time <= self.combo_timeout):
            self.combo += 1
        else:
            self.combo = 1

        self.active = True
        self.last_hit_time = now
        self.opacity = 1.0

        # Elastic spring pop trigger
        self.current_scale = 1.38
        self.scale_velocity = 0.0

        # Determine target anchor position above pet
        if pet_rect:
            px, py, pw, ph = pet_rect
            pet_cx = px + pw // 2
            pet_top = py
            self.target_x = float(pet_cx)
            self.target_y = float(pet_top - 68)
        else:
            self.target_x = float(hit_x)
            self.target_y = float(hit_y - 75)

        # Snap position directly on first hit, otherwise smoothly chase
        if self.combo == 1 or abs(self.x) < 1.0:
            self.x = self.target_x
            self.y = self.target_y

        # Spawn explosive hit sparks
        spark_colors = ["#ffea00", "#ff1744", "#ffffff", "#ff9100", "#ff4081"]
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(140.0, 380.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 60.0
            color = random.choice(spark_colors)
            size = random.uniform(3.0, 6.5)
            life = random.uniform(0.18, 0.38)
            self.sparks.append(SparkParticle(self.x, self.y + 10, vx, vy, color, size, life))

        return self.combo

    def update(self, dt: float, pet_rect: tuple[int, int, int, int] | None = None):
        """Ticks physics, spring animation, position tracking, and timeout decay."""
        if not self.active:
            return

        now = time.time()
        elapsed = now - self.last_hit_time

        # Update target coordinates if pet moved
        if pet_rect:
            px, py, pw, ph = pet_rect
            pet_cx = px + pw // 2
            pet_top = py
            self.target_x = float(pet_cx)
            self.target_y = float(pet_top - 68)

        # Smooth position chasing (lerp)
        lerp_factor = min(1.0, 16.0 * dt)
        self.x += (self.target_x - self.x) * lerp_factor
        self.y += (self.target_y - self.y) * lerp_factor

        # Spring damper for scale pop
        k = 280.0
        damp = 18.0
        diff = self.current_scale - self.target_scale
        force = -k * diff - damp * self.scale_velocity
        self.scale_velocity += force * dt
        self.current_scale += self.scale_velocity * dt

        if abs(diff) < 0.008 and abs(self.scale_velocity) < 0.01:
            self.current_scale = self.target_scale
            self.scale_velocity = 0.0

        # Update sparks
        self.sparks = [s for s in self.sparks if s.update(dt)]

        # Check combo timeout & fade out
        if elapsed > self.combo_timeout:
            fade_elapsed = elapsed - self.combo_timeout
            if fade_elapsed < self.fade_duration:
                # Drift upward while fading out
                self.y -= 45.0 * dt
                self.opacity = max(0.0, 1.0 - (fade_elapsed / self.fade_duration))
            else:
                self.reset()

    def reset(self):
        """Resets combo state cleanly."""
        self.combo = 0
        self.active = False
        self.opacity = 0.0
        self.sparks.clear()
        self._active_photo = None

    def draw(self, canvas: tk.Canvas):
        """Draws the combo counter badge, spark particles, and rating ribbons on screen."""
        if not self.active or self.combo <= 0 or self.opacity <= 0.02:
            return

        # 1. Draw hit spark particles
        for s in self.sparks:
            t = s.life / s.max_life
            sz = s.size * t
            canvas.create_oval(
                s.x - sz, s.y - sz, s.x + sz, s.y + sz,
                fill=s.color, outline="", width=0
            )

        # 2. Render combo counter badge
        photo = self.renderer.get_photo_image(self.combo, scale=self.current_scale)
        self._active_photo = photo  # Keep live reference

        bx = int(self.x)
        by = int(self.y)
        canvas.create_image(bx, by, image=photo, anchor="center")

        # 3. Arcade Rating Milestone Subtitle
        subtitle: str | None = None
        sub_color = "#ffffff"
        if self.combo >= 99:
            subtitle = "👑 MAXIMUM HITS! 👑"
            sub_color = "#ffea00"
        elif self.combo >= 50:
            subtitle = "🔥 ULTRA COMBO! 🔥"
            sub_color = "#ff3d00"
        elif self.combo >= 25:
            subtitle = "⚡ SUPER COMBO! ⚡"
            sub_color = "#00e5ff"
        elif self.combo >= 10:
            subtitle = "★ GREAT COMBO! ★"
            sub_color = "#ffd700"

        if subtitle:
            sub_y = by + int(48 * self.current_scale)
            # Black shadow text
            canvas.create_text(
                bx + 2, sub_y + 2,
                text=subtitle, fill="#000000",
                font=("Impact", 13, "bold")
            )
            # Colored foreground text
            canvas.create_text(
                bx, sub_y,
                text=subtitle, fill=sub_color,
                font=("Impact", 13, "bold")
            )
