"""
npc_graphics.py
Procedural walker sprite generator and compositor for DesktopPet.
Generates customizable chibi walker frames (idle + walk cycles) with modular
clothing (shirts, pants, shoes), face mounting, bobblehead scaling, and directional flipping.
"""

from __future__ import annotations
import math
from typing import Any
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageFont

# Default base canvas dimensions for the walker sprite
BASE_W, BASE_H = 100, 140

# Color palettes for clothing
SHIRT_COLORS = {
    "Navy": "#1E3A8A",
    "Coral Red": "#EF4444",
    "Forest Green": "#15803D",
    "Charcoal": "#374151",
    "Pastel Pink": "#F472B6",
    "Sunny Yellow": "#F59E0B",
    "Classic White": "#F9FAFB",
    "Deep Purple": "#7C3AED",
    "Sky Blue": "#38BDF8",
    "Olive": "#4D7C0F",
}

PANTS_COLORS = {
    "Denim Blue": "#2563EB",
    "Jet Black": "#18181B",
    "Khaki Tan": "#D97706",
    "Heather Grey": "#6B7280",
    "Cargo Olive": "#365314",
    "Clean White": "#F3F4F6",
}

SHOE_COLORS = {
    "Sneakers (White)": "#F9FAFB",
    "Sneakers (Red)": "#DC2626",
    "Boots (Brown)": "#78350F",
    "Dress (Black)": "#111827",
}

SHIRT_STYLES = ["Hoodie", "T-Shirt", "Suit / Blazer", "Striped Polo", "Athletic Jersey"]
PANTS_STYLES = ["Jeans", "Joggers", "Shorts", "Dress Slacks"]


def create_oval_mask(width: int, height: int) -> Image.Image:
    """Creates a smooth anti-aliased oval mask for face cropping."""
    scale = 4
    mask = Image.new("L", (width * scale, height * scale), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, width * scale - 1, height * scale - 1), fill=255)
    return mask.resize((width, height), Image.Resampling.LANCZOS)


def create_default_face(size: int = 50) -> Image.Image:
    """Creates a cute default chibi face if no custom photo is uploaded."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Skin base
    skin_col = "#FFDBAC"
    outline_col = "#7C4A27"
    draw.ellipse((2, 2, size - 3, size - 3), fill=skin_col, outline=outline_col, width=2)
    
    # Hair / Cap
    hair_col = "#4A2E18"
    draw.chord((2, 2, size - 3, size - 3), 180, 360, fill=hair_col, outline=outline_col, width=2)
    # Hair bangs
    draw.polygon([(size * 0.2, size * 0.4), (size * 0.35, size * 0.55), (size * 0.45, size * 0.4)], fill=hair_col)
    draw.polygon([(size * 0.5, size * 0.4), (size * 0.65, size * 0.55), (size * 0.78, size * 0.4)], fill=hair_col)

    # Eyes (happy anime style)
    eye_col = "#1F2937"
    ew = max(2, size // 10)
    eh = max(3, size // 7)
    draw.ellipse((size * 0.3 - ew // 2, size * 0.55, size * 0.3 + ew // 2, size * 0.55 + eh), fill=eye_col)
    draw.ellipse((size * 0.7 - ew // 2, size * 0.55, size * 0.7 + ew // 2, size * 0.55 + eh), fill=eye_col)
    
    # Eye highlights
    draw.ellipse((size * 0.3, size * 0.56, size * 0.3 + 1, size * 0.56 + 1), fill="#FFFFFF")
    draw.ellipse((size * 0.7, size * 0.56, size * 0.7 + 1, size * 0.56 + 1), fill="#FFFFFF")

    # Blush cheeks
    blush_col = "#F87171"
    draw.ellipse((size * 0.2, size * 0.68, size * 0.32, size * 0.76), fill=blush_col)
    draw.ellipse((size * 0.68, size * 0.68, size * 0.8, size * 0.76), fill=blush_col)

    # Smile
    draw.arc((size * 0.42, size * 0.68, size * 0.58, size * 0.8), start=0, end=180, fill=outline_col, width=2)
    return img


def draw_walker_body_frame(
    frame_type: str,
    walk_phase: float,
    shirt_style: str = "Hoodie",
    shirt_color: str = "#1E3A8A",
    pants_style: str = "Jeans",
    pants_color: str = "#2563EB",
    shoe_color: str = "#F9FAFB",
    custom_shirt_img: Image.Image | None = None,
) -> tuple[Image.Image, tuple[int, int]]:
    """
    Renders one frame of the walker body (torso, walking legs, arm holding leash).
    Returns (body_image, (hand_x, hand_y)).
    """
    img = Image.new("RGBA", (BASE_W, BASE_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Torso & leg positions
    torso_cx = BASE_W // 2
    torso_top = 58
    torso_w = 34
    torso_h = 42
    
    # Walk cycle leg offsets
    if frame_type == "walk":
        # Sinusoidal walking stride
        left_leg_angle = math.sin(walk_phase) * 22
        right_leg_angle = -left_leg_angle
        body_bob = int(abs(math.sin(walk_phase)) * 4)
    else:
        left_leg_angle = 0.0
        right_leg_angle = 0.0
        # Subtle idle breath
        body_bob = int(math.sin(walk_phase) * 2)

    torso_y = torso_top + body_bob
    pelvis_y = torso_y + torso_h - 2

    # Draw legs (Back leg first, then front leg)
    leg_len = 34
    leg_thick = 9 if pants_style != "Shorts" else 8
    skin_col = "#FFDBAC"

    for is_front, leg_deg in [(False, left_leg_angle), (True, right_leg_angle)]:
        rad = math.radians(leg_deg)
        hip_x = torso_cx - 6 if not is_front else torso_cx + 6
        foot_x = int(hip_x + math.sin(rad) * leg_len)
        foot_y = int(pelvis_y + math.cos(rad) * leg_len)

        cur_pants_col = pants_color

        if pants_style == "Shorts":
            knee_x = int(hip_x + math.sin(rad) * (leg_len * 0.55))
            knee_y = int(pelvis_y + math.cos(rad) * (leg_len * 0.55))
            draw.line([(hip_x, pelvis_y), (knee_x, knee_y)], fill=cur_pants_col, width=leg_thick)
            draw.line([(knee_x, knee_y), (foot_x, foot_y)], fill=skin_col, width=leg_thick - 2)
        else:
            draw.line([(hip_x, pelvis_y), (foot_x, foot_y)], fill=cur_pants_col, width=leg_thick)
            if pants_style == "Joggers":
                draw.line([(foot_x - 2, foot_y - 3), (foot_x + 2, foot_y - 3)], fill="#1F2937", width=2)

        # Shoes
        draw.ellipse((foot_x - 6, foot_y - 2, foot_x + 6, foot_y + 5), fill=shoe_color, outline="#1F2937", width=1)

    # Torso (Shirt)
    t_left = torso_cx - torso_w // 2
    t_right = torso_cx + torso_w // 2
    t_bottom = pelvis_y

    draw.rounded_rectangle(
        (t_left, torso_y, t_right, t_bottom),
        radius=6,
        fill=shirt_color,
        outline="#111827",
        width=2,
    )

    # Shirt style accents
    if shirt_style == "Hoodie":
        draw.rounded_rectangle((t_left + 6, t_bottom - 16, t_right - 6, t_bottom - 2), radius=3, fill=shirt_color, outline="#111827", width=1)
        draw.line([(torso_cx - 3, torso_y + 4), (torso_cx - 3, torso_y + 16)], fill="#FFFFFF", width=2)
        draw.line([(torso_cx + 3, torso_y + 4), (torso_cx + 3, torso_y + 16)], fill="#FFFFFF", width=2)
    elif shirt_style == "Suit / Blazer":
        draw.polygon([(torso_cx - 6, torso_y), (torso_cx + 6, torso_y), (torso_cx, torso_y + 18)], fill="#FFFFFF")
        draw.polygon([(torso_cx - 2, torso_y + 3), (torso_cx + 2, torso_y + 3), (torso_cx, torso_y + 16)], fill="#DC2626")
    elif shirt_style == "Striped Polo":
        draw.line([(t_left + 3, torso_y + 10), (t_right - 3, torso_y + 10)], fill="#FFFFFF", width=2)
        draw.line([(t_left + 3, torso_y + 20), (t_right - 3, torso_y + 20)], fill="#FFFFFF", width=2)
        draw.line([(t_left + 3, torso_y + 30), (t_right - 3, torso_y + 30)], fill="#FFFFFF", width=2)
    elif shirt_style == "Athletic Jersey":
        try:
            jersey_font = ImageFont.truetype("arialbd.ttf", 9)
        except Exception:
            try:
                jersey_font = ImageFont.truetype("segoeuib.ttf", 9)
            except Exception:
                jersey_font = ImageFont.load_default()
        draw.text((torso_cx - 6, torso_y + 11), "07", fill="#FFFFFF", font=jersey_font)

    # Custom shirt graphic stamp
    if custom_shirt_img is not None:
        try:
            gw = torso_w - 10
            gh = torso_h - 16
            stamp = custom_shirt_img.resize((gw, gh), Image.Resampling.LANCZOS)
            img.paste(stamp, (t_left + 5, torso_y + 8), stamp if stamp.mode == "RGBA" else None)
        except Exception:
            pass

    # Left Arm (Back arm)
    back_arm_rad = math.radians(-left_leg_angle * 0.8)
    shoulder_bx = torso_cx - 14
    shoulder_by = torso_y + 6
    elbow_bx = int(shoulder_bx + math.sin(back_arm_rad) * 16)
    elbow_by = int(shoulder_by + math.cos(back_arm_rad) * 16)
    draw.line([(shoulder_bx, shoulder_by), (elbow_bx, elbow_by)], fill=shirt_color, width=7)
    draw.ellipse((elbow_bx - 3, elbow_by - 3, elbow_bx + 3, elbow_by + 3), fill=skin_col)

    # Right Arm (Holding leash handle forward/down)
    shoulder_fx = torso_cx + 12
    shoulder_fy = torso_y + 6
    elbow_fx = shoulder_fx + 10
    elbow_fy = shoulder_fy + 14
    hand_x = elbow_fx + 10
    hand_y = elbow_fy + 6 + (body_bob // 2)

    draw.line([(shoulder_fx, shoulder_fy), (elbow_fx, elbow_fy)], fill=shirt_color, width=7)
    draw.line([(elbow_fx, elbow_fy), (hand_x, hand_y)], fill=shirt_color, width=6)
    
    # Hand
    draw.ellipse((hand_x - 4, hand_y - 4, hand_x + 4, hand_y + 4), fill=skin_col, outline="#111827", width=1)
    
    # Leash handle ring / grip
    draw.arc((hand_x - 3, hand_y - 6, hand_x + 5, hand_y + 6), start=45, end=270, fill="#8B4513", width=3)

    return img, (hand_x, hand_y)


def compose_full_walker_frame(
    head_img: Image.Image,
    frame_type: str,
    walk_phase: float,
    face_scale: Any = 1.0,
    face_offset_x: Any = 0,
    face_offset_y: Any = 0,
    char_scale: Any = 1.0,
    is_flipped: Any = False,
    shirt_style: Any = "Hoodie",
    shirt_color: Any = "#1E3A8A",
    pants_style: Any = "Jeans",
    pants_color: Any = "#2563EB",
    shoe_color: Any = "#F9FAFB",
    custom_shirt_img: Image.Image | None = None,
) -> tuple[Image.Image, tuple[int, int]]:
    """
    Composites the head and animated body together into a complete walker frame.
    Returns (final_image, (hand_anchor_x, hand_anchor_y)).
    """
    face_scale = float(face_scale)
    face_offset_x = int(face_offset_x)
    face_offset_y = int(face_offset_y)
    char_scale = float(char_scale)
    is_flipped = bool(is_flipped)
    shirt_style = str(shirt_style)
    shirt_color = str(shirt_color)
    pants_style = str(pants_style)
    pants_color = str(pants_color)
    shoe_color = str(shoe_color)
    body_img, (hx, hy) = draw_walker_body_frame(
        frame_type=frame_type,
        walk_phase=walk_phase,
        shirt_style=shirt_style,
        shirt_color=shirt_color,
        pants_style=pants_style,
        pants_color=pants_color,
        shoe_color=shoe_color,
        custom_shirt_img=custom_shirt_img,
    )

    base_head_w = int(54 * face_scale)
    base_head_h = int(54 * face_scale)
    scaled_head = head_img.resize((base_head_w, base_head_h), Image.Resampling.LANCZOS)

    body_bob = int(abs(math.sin(walk_phase)) * 4) if frame_type == "walk" else int(math.sin(walk_phase) * 2)

    head_x = (BASE_W // 2) - (base_head_w // 2) + face_offset_x
    head_y = 60 - base_head_h + face_offset_y + body_bob

    full_img = Image.new("RGBA", (BASE_W, BASE_H), (0, 0, 0, 0))
    full_img.paste(body_img, (0, 0), body_img)
    full_img.paste(scaled_head, (head_x, head_y), scaled_head if scaled_head.mode == "RGBA" else None)

    if char_scale != 1.0:
        target_w = max(40, int(BASE_W * char_scale))
        target_h = max(50, int(BASE_H * char_scale))
        full_img = full_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        hx = int(hx * char_scale)
        hy = int(hy * char_scale)
    else:
        target_w = BASE_W
        target_h = BASE_H

    if is_flipped:
        full_img = ImageOps.mirror(full_img)
        hx = target_w - hx

    return full_img, (hx, hy)


def generate_full_animation_set(
    head_img: Image.Image,
    face_scale: Any = 1.0,
    face_offset_x: Any = 0,
    face_offset_y: Any = 0,
    char_scale: Any = 1.0,
    is_mirror_base: Any = False,
    shirt_style: Any = "Hoodie",
    shirt_color: Any = "#1E3A8A",
    pants_style: Any = "Jeans",
    pants_color: Any = "#2563EB",
    shoe_color: Any = "#F9FAFB",
    custom_shirt_img: Image.Image | None = None,
) -> dict[str, list[tuple[Image.Image, tuple[int, int]]]]:
    """
    Generates full dictionary of frames with hand coordinates for 'idle' and 'walk'.
    Format: {"idle": [(img, (hx, hy)), ...], "walk": [(img, (hx, hy)), ...]}
    """
    face_scale = float(face_scale)
    face_offset_x = int(face_offset_x)
    face_offset_y = int(face_offset_y)
    char_scale = float(char_scale)
    is_mirror_base = bool(is_mirror_base)
    shirt_style = str(shirt_style)
    shirt_color = str(shirt_color)
    pants_style = str(pants_style)
    pants_color = str(pants_color)
    shoe_color = str(shoe_color)
    head = head_img.copy()
    if is_mirror_base:
        head = ImageOps.mirror(head)

    idle_frames = []
    for i in range(4):
        phase = (i / 4.0) * math.pi * 2
        f_img, hand = compose_full_walker_frame(
            head_img=head,
            frame_type="idle",
            walk_phase=phase,
            face_scale=face_scale,
            face_offset_x=face_offset_x,
            face_offset_y=face_offset_y,
            char_scale=char_scale,
            is_flipped=False,
            shirt_style=shirt_style,
            shirt_color=shirt_color,
            pants_style=pants_style,
            pants_color=pants_color,
            shoe_color=shoe_color,
            custom_shirt_img=custom_shirt_img,
        )
        idle_frames.append((f_img, hand))

    walk_frames = []
    for i in range(6):
        phase = (i / 6.0) * math.pi * 2
        f_img, hand = compose_full_walker_frame(
            head_img=head,
            frame_type="walk",
            walk_phase=phase,
            face_scale=face_scale,
            face_offset_x=face_offset_x,
            face_offset_y=face_offset_y,
            char_scale=char_scale,
            is_flipped=False,
            shirt_style=shirt_style,
            shirt_color=shirt_color,
            pants_style=pants_style,
            pants_color=pants_color,
            shoe_color=shoe_color,
            custom_shirt_img=custom_shirt_img,
        )
        walk_frames.append((f_img, hand))

    return {"idle": idle_frames, "walk": walk_frames}


def export_walker_assets(
    out_dir: Path,
    anim_set: dict[str, list[tuple[Image.Image, tuple[int, int]]]]
) -> dict[str, list[tuple[int, int]]]:
    """
    Saves generated PNG frames into out_dir/idle and out_dir/walk.
    Returns metadata dictionary of hand anchor offsets for each frame.
    """
    hand_offsets: dict[str, list[tuple[int, int]]] = {}
    
    for anim_name, frames in anim_set.items():
        anim_dir = out_dir / anim_name
        anim_dir.mkdir(parents=True, exist_ok=True)
        hand_offsets[anim_name] = []

        for idx, (img, (hx, hy)) in enumerate(frames):
            img_path = anim_dir / f"{idx}.png"
            img.save(img_path, "PNG")
            hand_offsets[anim_name].append((hx, hy))

    return hand_offsets
