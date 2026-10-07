#!/usr/bin/env python3
"""Merge ordered case folders into one image with two rows per case.

exp. python step3_merge_imgs.py --folders "01bd10c4-0849-5ad8-a874-3be804541e00" "000b8258-0e4a-5d78-8187-e1c5621492be"
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from matplotlib import colormaps


SCRIPT_DIR = Path(__file__).resolve().parent
ROW_FILES = (
    ("gt_heatmap.png", "ablation_match_heatmap.png", "our_heatmap.png"),
    ("gt_heatmap2.png", "ablation_match_heatmap2.png", "our_heatmap2.png"),
)
COLUMN_LABELS = ("GT", "With out Intersection", "With Intersection")
BLOCK_LABELS = ("premolar", "molar")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = (("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "DejaVuSans-Bold.ttf")
             if bold else ("/System/Library/Fonts/Supplemental/Arial.ttf", "DejaVuSans.ttf"))
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", nargs="?", type=Path, default=SCRIPT_DIR,
                        help="parent folder containing cases (default: script directory)")

    # 指定文件夹和显示顺序，每个文件夹占两行。
    parser.add_argument("--folders", nargs="+", help="case folder names in display order")
    parser.add_argument("-o", "--output", type=Path, default=Path("merged_heatmaps.png"),
                        help="output filename; relative paths use the script directory")
    parser.add_argument("--gap", type=int, default=80,
                        help="column gap and outer margin in pixels (default: 80)")
    # 板块内两行间距，单位像素。
    parser.add_argument("--line_space", "--line-space", type=int, default=80,
                        help="gap between the two rows in each block (default: 80)")
    # 板块之间的竖直间距，单位像素。
    parser.add_argument("--block_space", "--block-space", type=int, default=140,
                        help="vertical gap between case blocks (default: 80)")
     # 上方文字字体大小
    parser.add_argument("--font-size", type=int, default=90,
                        help="column title font size (default: 68)")
    # 左侧文字字体大小
    parser.add_argument("--block-font-size", "--block_font_size", type=int, default=90,
                        help="left-side block label font size (default: 68)")
    # 左侧文字是否加粗
    parser.add_argument("--block-bold", "--block_bold", action="store_true",
                        help="use bold font for the left-side block labels")
    parser.add_argument("--background", default="white")
    parser.add_argument("--clim", nargs="+", type=float, default=[0.0, 0.2],
                        help="colorbar limits: MAX (min=0) or MIN MAX (default: 0 0.2)")
    # 色带图字体大小
    parser.add_argument("--colorbar-font-size", type=int, default=100,
                        help="colorbar tick font size (default: 80)")
    # 色带图宽度
    parser.add_argument("--colorbar-length", "--colorbar-width", "--colorbar_width", dest="colorbar_width", type=int, default=1800,
                        help="vertical colorbar length in pixels (default: automatic)")
    # 色带图带宽
    parser.add_argument("--colorbar-thickness", type=int, default=50,
                        help="vertical colorbar thickness in pixels (default: 30)")
    parser.add_argument("--colorbar-gap", type=int, default=100,
                        help="horizontal gap between images and colorbar (default: 80)")
    # 色带图位置
    parser.add_argument("--colorbar-position", "--colorbar_position", nargs=2, type=int,
                        default=(3600, 1300), metavar=("X", "Y"),
                        help="colorbar top-left pixel coordinates; origin is image top-left (default: 3500 1500)")
    args = parser.parse_args()
    if len(args.clim) not in (1, 2):
        parser.error("--clim expects MAX or MIN MAX")
    vmin, vmax = (0.0, args.clim[0]) if len(args.clim) == 1 else args.clim
    if not all(math.isfinite(value) for value in (vmin, vmax)) or vmin >= vmax:
        parser.error("--clim must contain finite limits with MIN < MAX")
    if min(args.gap, args.line_space, args.block_space, args.colorbar_gap) < 0:
        parser.error("gap, line_space, block_space and colorbar-gap must be nonnegative")
    if min(args.font_size, args.block_font_size, args.colorbar_font_size) <= 0:
        parser.error("all font sizes must be positive")
    if args.colorbar_width is not None and args.colorbar_width < 2:
        parser.error("colorbar-length must be at least 2 pixels")
    if args.colorbar_thickness <= 0:
        parser.error("colorbar-thickness must be positive")
    if args.colorbar_position is not None and min(args.colorbar_position) < 0:
        parser.error("colorbar-position coordinates must be nonnegative")

    root = args.folder.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"folder does not exist: {root}")
    if args.folders:
        sample_dirs = [root / name.strip() for name in args.folders]
    else:
        sample_dirs = sorted(path for path in root.iterdir()
                             if path.is_dir() and not path.name.startswith(".")
                             and path.name != "__pycache__")
    blocks = []
    for sample_dir in sample_dirs:
        if not sample_dir.is_dir():
            parser.error(f"case folder does not exist: {sample_dir}")
        rows = [[sample_dir / name for name in names] for names in ROW_FILES]
        missing = [str(path) for row in rows for path in row if not path.is_file()]
        if missing:
            if args.folders:
                parser.error("missing images: " + ", ".join(missing))
            print(f"skip {sample_dir.name}: missing images")
            continue
        images = []
        for row in rows:
            image_row = []
            for path in row:
                with Image.open(path) as image:
                    image_row.append(image.convert("RGB"))
            images.append(image_row)
        blocks.append(images)
    if not blocks:
        parser.error(f"no complete case blocks found in {root}")

    tile_width = max(image.width for block in blocks for row in block for image in row)
    tile_height = max(image.height for block in blocks for row in block for image in row)
    font = load_font(args.font_size)
    block_font = load_font(args.block_font_size, bold=args.block_bold)
    labels = BLOCK_LABELS[:len(blocks)]
    label_width = max(block_font.getbbox(label)[2] - block_font.getbbox(label)[0]
                      for label in labels)
    left_width = label_width + 40
    header_height = args.font_size + 40
    colorbar_font = load_font(args.colorbar_font_size)
    block_height = 2 * tile_height + args.line_space
    image_height = len(blocks) * block_height + (len(blocks) - 1) * args.block_space
    tick_labels = [f"{vmin + (vmax - vmin) * tick / 4:.4g}" for tick in range(5)]
    max_tick_width = math.ceil(max(colorbar_font.getlength(label) for label in [*tick_labels, "(mm)"]))
    bar_length = args.colorbar_width if args.colorbar_width is not None else max(2, round(image_height * 0.7))
    if bar_length > image_height:
        parser.error(f"colorbar-length must not exceed the image region height ({image_height} pixels)")
    image_right = left_width + 3 * tile_width + 3 * args.gap
    bar_x = image_right + args.colorbar_gap
    # Anchor the vertical colorbar to the bottom-right of the image region.
    bar_y = args.gap + header_height + image_height - bar_length
    if args.colorbar_position is not None:
        bar_x, bar_y = args.colorbar_position
    canvas_width = max(image_right + args.gap,
                       bar_x + args.colorbar_thickness + 16 + max_tick_width + max(args.gap, 20))
    canvas_height = max(2 * args.gap + header_height + image_height,
                        bar_y + bar_length + args.colorbar_font_size + 20)
    canvas = Image.new("RGB", (canvas_width, canvas_height), args.background)
    draw = ImageDraw.Draw(canvas)
    for column, label in enumerate(COLUMN_LABELS):
        center_x = left_width + args.gap + column * (tile_width + args.gap) + tile_width // 2
        draw.text((center_x, args.gap + header_height // 2), label,
                  font=font, fill="black", anchor="mm")
    for block_index, block in enumerate(blocks):
        block_y = args.gap + header_height + block_index * (block_height + args.block_space)
        if block_index < len(BLOCK_LABELS):
            draw.text((args.gap + label_width // 2, block_y + block_height // 2),
                      BLOCK_LABELS[block_index], font=block_font, fill="black", anchor="mm")
        for row_index, row in enumerate(block):
            y = block_y + row_index * (tile_height + args.line_space)
            for column, image in enumerate(row):
                x = left_width + args.gap + column * (tile_width + args.gap)
                tile = ImageOps.contain(image, (tile_width, tile_height))
                canvas.paste(tile, (x + (tile_width - tile.width) // 2,
                                    y + (tile_height - tile.height) // 2))
    unit_y = bar_y - args.colorbar_font_size - 20
    if unit_y < args.colorbar_font_size:
        # At the top edge, put the unit below the bar to keep it visible.
        unit_y = bar_y + bar_length + args.colorbar_font_size + 10
    draw.text((bar_x, unit_y), "(mm)", font=colorbar_font, fill="black", anchor="lb")
    # High distances are blue at the top; low distances are red at the bottom.
    cmap = colormaps["jet_r"]
    for index in range(bar_length):
        color = tuple(round(channel * 255) for channel in cmap(1 - index / (bar_length - 1))[:3])
        draw.line((bar_x, bar_y + index, bar_x + args.colorbar_thickness - 1, bar_y + index), fill=color)
    draw.rectangle((bar_x, bar_y, bar_x + args.colorbar_thickness - 1, bar_y + bar_length - 1), outline="black")
    for tick, label in enumerate(tick_labels):
        tick_y = bar_y + round((bar_length - 1) * (1 - tick / 4))
        draw.line((bar_x + args.colorbar_thickness, tick_y, bar_x + args.colorbar_thickness + 6, tick_y), fill="black")
        draw.text((bar_x + args.colorbar_thickness + 12, tick_y), label,
                  font=colorbar_font, fill="black", anchor="lm")
    output = args.output.expanduser()
    if not output.is_absolute():
        output = SCRIPT_DIR / output
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(f"saved {output.resolve()} ({len(blocks)} blocks)")


if __name__ == "__main__":
    main()
