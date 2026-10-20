#!/usr/bin/env python3
"""
sprite_extract.py

Slice a sprite sheet (one row per animation) into individual frames,
remove the background (even when it's a near-white/off-white color
close to the character's own fur/highlight colors), and save each
frame into assets/<subject>/<animation>/NN.png

------------------------------------------------------------------
HOW IT WORKS
------------------------------------------------------------------
Rather than assuming a perfectly even pixel grid (hand/AI-drawn
sheets are rarely pixel-exact) or naively chroma-keying every pixel
close to the background color (which eats holes in light-colored fur
that happens to be a similar color to the background), this script:

  1. Finds the background color automatically (top-left corner
     pixel) unless you set BG_COLOR explicitly.
  2. Flood-fills the background starting from the sheet's outer edge
     -- only pixels *connected* to the border are treated as
     background. A white belly enclosed by a dark outline stroke
     stays opaque even though its color is close to the background,
     because it isn't connected to the outside.
  3. Feathers a few pixels at the boundary (partial alpha) instead of
     a hard cutout, so edges look smooth instead of jagged.
  4. Auto-detects each frame's bounding box from the remaining
     foreground blobs (instead of assuming a rigid grid), and merges
     small nearby blobs (like a drop-shadow under a jump frame) into
     the frame they belong to.
  5. Sorts detected frames into rows (top-to-bottom) and columns
     (left-to-right) and maps each row to the animation name you
     configured.

------------------------------------------------------------------
QUICK START
------------------------------------------------------------------
1. Edit the CONFIG block below:
     - SHEET_PATH: path to your sprite sheet image
     - SUBJECT: top-level folder name (e.g. "pet" -> assets/pet/...)
     - ROWS: one entry per animation, in top-to-bottom order on the
       sheet, with how many frames are in that row.

2. Preview first to make sure detection lines up:
       python3 sprite_extract.py --preview
   Writes preview_grid.png next to your sheet with a red box drawn
   around every detected frame, labeled with the animation name and
   frame number. Check every cat/character has exactly one box.

3. Extract for real:
       python3 sprite_extract.py
   Creates assets/<subject>/<animation>/01.png, 02.png, ...

------------------------------------------------------------------
TUNING
------------------------------------------------------------------
- If detection finds the wrong number of blobs, adjust FLOOD_TOLERANCE
  (how close a pixel must be to the background color to seed the
  flood fill) or check ROWS frame counts add up to the true total.
- MERGE_MAX_GAP controls how far away a small extra blob (like a
  shadow) can be from a main frame and still get merged into it.
- PADDING adds a few extra pixels around each detected frame before
  cropping, in case anti-aliased edges get clipped too tight.
- Requires numpy, scipy and Pillow (pip install numpy scipy pillow).
"""

from pathlib import Path
import argparse
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

# ==================================================================
# CONFIG -- edit this block for your sprite sheet
# ==================================================================

SHEET_PATH = "sprite_sheet.png"
SUBJECT = "pet"
OUTPUT_ROOT = "assets"

# One entry per row, TOP TO BOTTOM as it appears on the sheet.
ROWS = [
    {"name": "idle",  "frames": 4},
    {"name": "walk",  "frames": 4},
    {"name": "jump",  "frames": 4},
    {"name": "sleep", "frames": 4},
    {"name": "eat",   "frames": 4},
]

# Background color to remove. "auto" samples the top-left pixel.
BG_COLOR = "auto"

# Color-distance tolerance for seeding the background flood fill.
# Only pixels this close to BG_COLOR *and* connected to the sheet's
# outer edge are removed -- enclosed light fur/highlights are safe
# even if their color is close to this.
FLOOD_TOLERANCE = 20

# Soft edge feathering: pixels within this color distance of the
# background, sitting right at the boundary, get partial alpha for a
# smooth (non-jagged) edge instead of a hard cutout.
FEATHER_TOLERANCE = 60
FEATHER_DILATE_PX = 3

# Extra pixels of padding added around each detected frame's box
# before cropping (helps avoid clipping whiskers/anti-aliased edges).
PADDING = 4

# Small nearby blobs (e.g. a drop-shadow under a jump pose) within
# this many pixels of a detected frame get merged into that frame
# instead of being discarded as noise or treated as their own frame.
MERGE_MAX_GAP = 40

# Drop frames that end up fully transparent.
SKIP_BLANK_FRAMES = True

FRAME_NAME_PADDING = 2

# ==================================================================
# IMPLEMENTATION -- shouldn't need to edit below this line
# ==================================================================


def get_bg_color(arr):
    if BG_COLOR != "auto":
        return np.array(BG_COLOR, dtype=float)
    corner = arr[0, 0].astype(float)
    print(f"[auto] sampled background color from top-left corner: {tuple(corner.astype(int))}")
    return corner


def remove_background(arr, bg_color):
    """arr: HxWx3 uint8 RGB numpy array. Returns HxWx4 uint8 RGBA array."""
    dist = np.sqrt(((arr.astype(float) - bg_color) ** 2).sum(axis=2))

    hardmask = dist <= FLOOD_TOLERANCE
    lbl, _ = ndimage.label(hardmask, structure=np.ones((3, 3)))  # type: ignore[misc]
    border_labels = set(lbl[0, :]) | set(lbl[-1, :]) | set(lbl[:, 0]) | set(lbl[:, -1])
    border_labels.discard(0)
    bg_region = np.isin(lbl, list(border_labels)) if border_labels else np.zeros_like(hardmask)

    dilated = ndimage.binary_dilation(bg_region, iterations=FEATHER_DILATE_PX)
    band = np.logical_and(dilated, ~bg_region)

    alpha = np.full(dist.shape, 255.0)
    alpha[bg_region] = 0
    alpha[band] = np.clip(dist[band] / FEATHER_TOLERANCE, 0, 1) * 255

    rgba = np.dstack([arr, alpha.astype(np.uint8)])
    return rgba, ~bg_region


def detect_frames(fg_mask, total_frames):
    """Find `total_frames` main blobs plus merge small nearby blobs (shadows etc)
    into their nearest main blob. Returns list of (left, top, right, bottom)."""
    lbl, n = ndimage.label(fg_mask, structure=np.ones((3, 3)))  # type: ignore[misc]
    if n == 0:
        return []

    sizes = ndimage.sum(fg_mask, lbl, range(1, n + 1))
    order = sorted(range(1, n + 1), key=lambda i: sizes[i - 1], reverse=True)

    main_ids = order[:total_frames]
    extra_ids = order[total_frames:]

    boxes = {}
    for i in main_ids:
        ys, xs = np.where(lbl == i)
        boxes[i] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]

    # merge small extra blobs (shadows, stray marks) into nearest main box
    for i in extra_ids:
        ys, xs = np.where(lbl == i)
        if len(xs) < 30:
            continue  # pure noise speck, ignore
        ex_box = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        ecx = (ex_box[0] + ex_box[2]) / 2
        ecy = (ex_box[1] + ex_box[3]) / 2

        best, best_dist = None, None
        for mid, mbox in boxes.items():
            mcx = (mbox[0] + mbox[2]) / 2
            mcy = (mbox[1] + mbox[3]) / 2
            gap_x = max(mbox[0] - ex_box[2], ex_box[0] - mbox[2], 0)
            gap_y = max(mbox[1] - ex_box[3], ex_box[1] - mbox[3], 0)
            gap = (gap_x ** 2 + gap_y ** 2) ** 0.5
            if best_dist is None or gap < best_dist:
                best, best_dist = mid, gap
        if best is not None and best_dist is not None and best_dist <= MERGE_MAX_GAP:
            b = boxes[best]
            b[0] = min(b[0], ex_box[0])
            b[1] = min(b[1], ex_box[1])
            b[2] = max(b[2], ex_box[2])
            b[3] = max(b[3], ex_box[3])

    return list(boxes.values())


def assign_rows(boxes, rows_cfg):
    """Sort boxes top-to-bottom into rows per rows_cfg frame counts, then
    left-to-right within each row."""
    boxes = sorted(boxes, key=lambda b: (b[1] + b[3]) / 2)
    result = []
    idx = 0
    for row_cfg in rows_cfg:
        n = row_cfg["frames"]
        chunk = boxes[idx:idx + n]
        idx += n
        chunk.sort(key=lambda b: (b[0] + b[2]) / 2)
        result.append((row_cfg["name"], chunk))
    if idx != len(boxes):
        print(f"WARNING: detected {len(boxes)} frames but ROWS config totals "
              f"{sum(r['frames'] for r in rows_cfg)}. Adjust ROWS or FLOOD_TOLERANCE.")
    return result


def pad_box(box, w, h):
    l, t, r, b = box
    return (max(0, l - PADDING), max(0, t - PADDING),
            min(w, r + PADDING), min(h, b + PADDING))


def main():
    parser = argparse.ArgumentParser(description="Slice a sprite sheet into animation frames.")
    parser.add_argument("--preview", action="store_true", help="Write a detection-overlay preview instead of extracting.")
    parser.add_argument("--sheet", default=SHEET_PATH, help="Path to the sprite sheet image.")
    args = parser.parse_args()

    sheet_path = Path(args.sheet)
    if not sheet_path.exists():
        print(f"ERROR: sprite sheet not found at '{sheet_path}'.")
        sys.exit(1)

    img = Image.open(sheet_path).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    total_frames = sum(r["frames"] for r in ROWS)
    print(f"Sheet size: {w}x{h}  |  rows configured: {len(ROWS)}  |  total frames expected: {total_frames}")

    bg_color = get_bg_color(arr)
    rgba, fg_mask = remove_background(arr, bg_color)

    boxes = detect_frames(fg_mask, total_frames)
    print(f"Detected {len(boxes)} frame blob(s).")

    rows = assign_rows(boxes, ROWS)

    if args.preview:
        preview = Image.fromarray(rgba, "RGBA").copy()
        draw = ImageDraw.Draw(preview)
        for name, chunk in rows:
            for i, box in enumerate(chunk, start=1):
                pb = pad_box(box, w, h)
                draw.rectangle(pb, outline=(255, 0, 0, 255), width=3)
                draw.text((pb[0] + 4, pb[1] + 4), f"{name} {i}", fill=(255, 0, 0, 255))
        out_path = sheet_path.with_name("preview_grid.png")
        preview.save(out_path)
        print(f"Preview written to {out_path} -- check every frame has exactly one "
              f"labeled box before running the real extraction.")
        return

    root = Path(OUTPUT_ROOT) / SUBJECT
    full_rgba_img = Image.fromarray(rgba, "RGBA")

    for name, chunk in rows:
        out_dir = root / name
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for i, box in enumerate(chunk, start=1):
            pb = pad_box(box, w, h)
            frame = full_rgba_img.crop(pb)
            extrema = frame.getextrema()
            if SKIP_BLANK_FRAMES and len(extrema) >= 4 and extrema[3] == (0, 0):  # type: ignore[index]
                continue
            count += 1
            fname = f"{count:0{FRAME_NAME_PADDING}d}.png"
            frame.save(out_dir / fname)
        print(f"  {name}: {count} frames -> {out_dir}/")

    print(f"\nDone. Frames written under {root}/")


if __name__ == "__main__":
    main()
