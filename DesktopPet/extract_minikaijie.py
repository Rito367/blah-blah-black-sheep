"""
extract_minikaijie.py

Slices minikaijie_spritesheet.jpeg into individual animation frames,
removes the off-white background, and saves them to:
  assets/mini kaijie/<animation>/01.png ... 04.png

Layout detected: 4 columns x 5 rows, ~205x205 px per cell.
Row order (top to bottom): idle, walk, jump, sleep, eat
"""

from pathlib import Path
from PIL import Image
import numpy as np

# ── config ────────────────────────────────────────────────────────────────
SHEET_PATH  = Path("minikaijie_spritesheet.jpeg")
OUTPUT_DIR  = Path("assets") / "mini kaijie"
ANIM_ORDER  = ["idle", "walk", "jump", "sleep", "eat"]
COLS        = 4
ROWS        = 5
OUTPUT_SIZE = (60, 60)          # match the pet sprite size used in pet.py

# Background removal tolerance (flood-fill from border)
FLOOD_TOL   = 30                # pixels within this CIELAB-ish distance get removed
# ──────────────────────────────────────────────────────────────────────────


def color_dist(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Per-pixel Euclidean distance in RGB space. a: HxWx3, b: shape(3,)"""
    return np.sqrt(((a.astype(float) - b.astype(float)) ** 2).sum(axis=2))


def remove_bg_flood(rgb: np.ndarray, tol: float) -> np.ndarray:
    """
    Flood-fill the background starting from all four edges of `rgb`.
    Returns an RGBA uint8 array with the background set to alpha=0.
    Enclosed light regions (belly, highlights) are kept opaque.
    """
    h, w = rgb.shape[:2]
    bg_color = rgb[0, 0].astype(float)          # sample top-left corner

    dist = color_dist(rgb, bg_color)
    candidate = dist <= tol                      # pixels CLOSE to bg color

    # BFS flood-fill from border pixels that are 'candidate'
    from collections import deque
    visited = np.zeros((h, w), dtype=bool)
    q = deque()
    for y in range(h):
        for x in [0, w - 1]:
            if candidate[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((y, x))
    for x in range(w):
        for y in [0, h - 1]:
            if candidate[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((y, x))

    while q:
        cy, cx = q.popleft()
        for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and candidate[ny, nx]:
                visited[ny, nx] = True
                q.append((ny, nx))

    # visited = background mask
    alpha = np.where(visited, 0, 255).astype(np.uint8)
    rgba  = np.dstack([rgb, alpha])
    return rgba


def extract():
    img = Image.open(SHEET_PATH).convert("RGB")
    arr = np.array(img)
    sheet_h, sheet_w = arr.shape[:2]

    cell_w = sheet_w // COLS
    cell_h = sheet_h // ROWS

    print(f"Sheet: {sheet_w}x{sheet_h}  |  cell: {cell_w}x{cell_h}")

    for row_idx, anim_name in enumerate(ANIM_ORDER):
        out_dir = OUTPUT_DIR / anim_name
        out_dir.mkdir(parents=True, exist_ok=True)

        for col_idx in range(COLS):
            # crop the raw cell
            x0 = col_idx * cell_w
            y0 = row_idx * cell_h
            x1 = x0 + cell_w
            y1 = y0 + cell_h
            cell_rgb = arr[y0:y1, x0:x1]

            # remove background
            cell_rgba = remove_bg_flood(cell_rgb, FLOOD_TOL)
            frame_img = Image.fromarray(cell_rgba, "RGBA")

            # resize to game sprite size
            frame_img = frame_img.resize(OUTPUT_SIZE, Image.LANCZOS)

            fname = out_dir / f"{col_idx + 1:02d}.png"
            frame_img.save(fname)

        print(f"  {anim_name}: {COLS} frames -> {out_dir}/")

    print(f"\nDone! Frames saved under {OUTPUT_DIR}/")
    print("You can now select 'Mini Kaijie' from the Character menu in the app.")


if __name__ == "__main__":
    extract()
