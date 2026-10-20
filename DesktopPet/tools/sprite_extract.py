#!/usr/bin/env python3
"""
sprite_extract.py

将精灵图表（每行一个动画序列）切分为独立的单帧图片，
自动去除背景色（即便背景色是接近角色自身毛发或高光颜色的近白色/灰白色），
并将提取后的每帧保存至 assets/<角色名>/<动画名>/NN.png。

------------------------------------------------------------------
工作原理
------------------------------------------------------------------
不同于假设所有图表都具备绝对均匀的像素网格（手绘或AI生成的图表很少具备完全一致的像素对齐），
也不同于简单粗暴地将所有接近背景色的像素抠掉（这会导致浅色毛发被扣出透明空洞）：

  1. 自动检测背景色（默认采样左上角首个像素），除非手动显式指定了 BG_COLOR。
  2. 从图片外边缘开始进行背景泛洪填充（Flood-fill）——仅与外边界“相连通”的像素才会被判定为背景。
     即使角色体内有被深色轮廓包裹的纯白肚皮，由于未与外部边缘连通，依然会完整保留不透明度。
  3. 在边界处进行柔和边缘羽化（部分 Alpha 透明度过渡），避免硬切导致的锯齿杂边，使边缘平滑自然。
  4. 自动检测前景连通块的边界框（无需固定网格），并智能合并附近的微小碎块（如跳跃动作下方的投影阴影）。
  5. 将检测到的各帧按从上到下划分为行、行内按从左到右排序，并映射到你所配置的动画名称上。

------------------------------------------------------------------
快速开始
------------------------------------------------------------------
1. 修改下方的配置参数（CONFIG 区块）：
     - SHEET_PATH: 精灵图表文件路径
     - SUBJECT: 角色根目录名（例如 "pet" -> assets/pet/...）
     - ROWS: 按图表上从上到下的顺序，配置每个动画行的名称及该行包含的帧数。

2. 先执行预览模式，检查边界框检测是否准确对齐：
       python3 sprite_extract.py --preview
   这将在精灵图同级目录下生成 preview_grid.png，每个检测到的动作帧都会被红框标出并标注动画名与帧序号。
   请检查确认每个角色/小猫是否都被准确框选。

3. 正式执行切图与提取：
       python3 sprite_extract.py
   将自动生成 assets/<角色名>/<动画名>/01.png, 02.png, ...

------------------------------------------------------------------
参数微调
------------------------------------------------------------------
- 若检测出的连通块数量不正确，可调整 FLOOD_TOLERANCE（用于泛洪填充起点的背景颜色容差阈值），
  或核对 ROWS 中配置的总帧数是否与图表完全吻合。
- MERGE_MAX_GAP 控制碎小连通块（如投影、碎杂点）与主体帧的最大合并距离像素值。
- PADDING 用于在裁剪前为每个动作帧外扩若干像素内边距，防止平滑边缘或猫胡须被截断。
- 依赖项：numpy, scipy 以及 Pillow（安装命令：pip install numpy scipy pillow）。
"""

from pathlib import Path
import argparse
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

# 确保在 Windows 控制台环境下输出中文字符不发生编码错误
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    getattr(sys.stderr, "reconfigure")(encoding="utf-8", errors="replace")

# ==================================================================
# 配置区域（CONFIG） -- 请根据你的精灵图表修改以下参数
# ==================================================================

SHEET_PATH = "sprite_sheet.png"
SUBJECT = "pet"
OUTPUT_ROOT = "assets"

# 每一行动画对应一项，严格按照图表上【从上到下】的顺序排列。
ROWS = [
    {"name": "idle",  "frames": 4},
    {"name": "walk",  "frames": 4},
    {"name": "jump",  "frames": 4},
    {"name": "sleep", "frames": 4},
    {"name": "eat",   "frames": 4},
]

# 要移除的背景颜色。"auto" 表示自动采样左上角像素颜色。
BG_COLOR = "auto"

# 边缘背景泛洪填充的颜色距离容差阈值。
# 只有颜色距离在此阈值以内、且与图片外边缘连通的像素才会被判定为背景移除；
# 角色内部闭合区域即使颜色与背景相近，也不会被误删。
FLOOD_TOLERANCE = 20

# 边缘平滑羽化容差：处于边界处、且颜色与背景接近的像素将获得渐变 Alpha 透明度，
# 从而实现边缘平滑过渡，避免出现生硬锯齿。
FEATHER_TOLERANCE = 60
FEATHER_DILATE_PX = 3

# 每个检测框在裁切前额外扩展的外边距像素（有助于避免切断边缘抗锯齿区域或细小毛发）。
PADDING = 4

# 与主帧距离在此像素范围内的小碎块（例如跳跃动作下方的投影阴影）
# 会自动合并到该主帧中，而不会被当作杂点丢弃或误判为单独一帧。
MERGE_MAX_GAP = 40

# 自动跳过最终完全透明的空白帧。
SKIP_BLANK_FRAMES = True

FRAME_NAME_PADDING = 2

# ==================================================================
# 核心实现逻辑 -- 以下内容通常无需修改
# ==================================================================


def get_bg_color(arr):
    """获取背景颜色基准值。"""
    if BG_COLOR != "auto":
        return np.array(BG_COLOR, dtype=float)
    corner = arr[0, 0].astype(float)
    print(f"[自动采样] 从左上角采样背景颜色: {tuple(corner.astype(int))}")
    return corner


def remove_background(arr, bg_color):
    """arr: 高x宽x3 的 uint8 RGB numpy 数组。返回: 高x宽x4 的 uint8 RGBA 数组及前景掩码。"""
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
    """检测 `total_frames` 个主要前景连通块，并将附近的小连通块（如投影阴影等）
    智能合并到最近的主块中。返回各帧的边界框列表 [(左, 上, 右, 下), ...]"""
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

    # 将附近的碎小连通块（阴影、游离像素）合并到距离最近的主帧框中
    for i in extra_ids:
        ys, xs = np.where(lbl == i)
        if len(xs) < 30:
            continue  # 忽略微小噪点杂色
        ex_box = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]

        best, best_dist = None, None
        for mid, mbox in boxes.items():
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
    """根据 rows_cfg 中的帧数设定，先按从上到下将边界框归类为各行，
    再在每一行动画内部按从左到右进行排列。"""
    boxes = sorted(boxes, key=lambda b: (b[1] + b[3]) / 2)
    result = []
    idx = 0
    for row_cfg in rows_cfg:
        n = int(row_cfg["frames"])
        chunk = boxes[idx:idx + n]
        idx += n
        chunk.sort(key=lambda b: (b[0] + b[2]) / 2)
        result.append((str(row_cfg["name"]), chunk))
    if idx != len(boxes):
        print(f"警告: 检测到 {len(boxes)} 个帧区域，但 ROWS 配置的总帧数为 "
              f"{sum(int(r['frames']) for r in rows_cfg)}。请检查并调整 ROWS 或 FLOOD_TOLERANCE。")
    return result


def pad_box(box, w, h):
    """为边界框添加内边距并限制在图像宽高范围内。"""
    l, t, r, b = box
    return (max(0, l - PADDING), max(0, t - PADDING),
            min(w, r + PADDING), min(h, b + PADDING))


def main():
    parser = argparse.ArgumentParser(description="将精灵图表（Sprite Sheet）自动切分为独立的动画序列帧。")
    parser.add_argument("--preview", action="store_true", help="生成带检测边框的预览网格图，而不执行实际切图提取。")
    parser.add_argument("--sheet", default=SHEET_PATH, help="精灵图表文件的路径。")
    args = parser.parse_args()

    sheet_path = Path(args.sheet)
    if not sheet_path.exists():
        print(f"错误: 未找到精灵图表文件 '{sheet_path}'。")
        sys.exit(1)

    img = Image.open(sheet_path).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    total_frames = sum(int(r["frames"]) for r in ROWS)
    print(f"图表尺寸: {w}x{h}  |  配置行数: {len(ROWS)}  |  预期总帧数: {total_frames}")

    bg_color = get_bg_color(arr)
    rgba, fg_mask = remove_background(arr, bg_color)

    boxes = detect_frames(fg_mask, total_frames)
    print(f"已检测到 {len(boxes)} 个动画帧连通区域。")

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
        print(f"预览图已保存至 {out_path} -- 在运行正式提取之前，请先确认每个动作帧均有且仅有一个红框标识。")
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
        print(f"  {name}: {count} 帧 -> {out_dir}/")

    print(f"\n提取完成。所有动画帧已保存至 {root}/")


if __name__ == "__main__":
    main()
