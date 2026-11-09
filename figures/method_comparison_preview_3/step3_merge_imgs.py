#!/usr/bin/env python3
"""Merge preview-1 sample renderings into one contact sheet.

For every subfolder, one row is appended in this order::

    singlejaw.png  sample1_match_singlejaw.png  sample2_match_singlejaw.png
    sample3_match_singlejaw.png  our_singlejaw.png  gt_singlejaw.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
from matplotlib import colormaps


ROW_FILES = ((
    "singlejaw.png",
    "sample1_match_singlejaw.png",
    "sample2_match_singlejaw.png",
    "sample3_match_singlejaw.png",
    "sample4_match_singlejaw.png",    
    "our_singlejaw.png",
    "gt_singlejaw.png",
),)
COLUMN_LABELS = ("Prep Tooth", "VF-Net", "DMCv2", "VBCD", "MADCrowner", "Ours", "Reference Crown")
COLORBAR_WIDTH = 260
COLORBAR_GAP = 60 #色带与最后一张图片之间间距
COLORBAR_MIN = -0.3
COLORBAR_MAX = 0.3

# Desired row order by sample-folder name; set to () for the default alphabetical order.
ROW_ORDER = (
    "001fa0b0-53d6-5e37-b93b-74570e867a02",
    "021a7b93-011f-5b10-818f-7b70e5b6037a",
    "000b8258-0e4a-5d78-8187-e1c5621492be",
    "00e13b2d-5753-51fa-98ff-2a0b3d2854b0",
)


def make_colorbar(height: int, bar_width: int = 60, font_size: int = 60,
                  unit: str = "(mm)") -> Image.Image:
    """Create a vertical turbo colorbar for the fixed [-0.3, 0.3] scale."""
    top_pad = 50  # extra clear space above the unit label
    margin_y = 100 # 色带本体上下留白
    bar_height = max(1, height - 2 * margin_y)
    # Render from +0.3 at the top to -0.3 at the bottom, matching the
    # vertical orientation and normalization used by PyVista in step2.
    values = np.linspace(COLORBAR_MAX, COLORBAR_MIN, bar_height)
    normalized = (values - COLORBAR_MIN) / (COLORBAR_MAX - COLORBAR_MIN)
    rgb = (colormaps["turbo"](normalized)[:, :3] * 255).astype(np.uint8)
    bar = Image.fromarray(np.repeat(rgb[:, None, :], bar_width, axis=1), "RGB")
    canvas = Image.new("RGB", (COLORBAR_WIDTH, height + top_pad), "white")
    canvas.paste(bar, (0, margin_y + top_pad))
    draw = ImageDraw.Draw(canvas)
    # Frame the color strip so the scale is visually explicit.
    margin_y += top_pad
    draw.rectangle((0, margin_y, bar_width - 1, margin_y + bar_height - 1),
                   outline="black", width=2)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    # Six evenly spaced ticks, with the largest positive value at the top.
    labels = ["0.3", "0.2", "0.1", "0.0", "-0.1", "-0.2", "-0.3"]
    for index, label in enumerate(labels):
        y = margin_y + round(index * (bar_height - 1) / (len(labels) - 1))
        draw.line((bar_width - 4, y, bar_width + 8, y), fill="black", width=2)
        text_y = max(0, min(height - font_size, y - font_size // 2))
        draw.text((bar_width + 20, text_y), label, fill="black", font=font)
    # Unit label above the scale.
    # Keep the unit fully inside the colorbar canvas and clearly above the
    # first numeric tick label.
    # Keep the complete unit visible at the top edge; the first tick starts
    # lower down at ``margin_y``, so the labels do not overlap.
    draw.text((COLORBAR_WIDTH // 2, 0), unit, fill="black", font=font, anchor="mt")
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "folder", nargs="?", type=Path,
        default=Path("../method_comparison_preview_1"),
        help="folder containing sample folders (default: ../method_comparison_preview_1)",
    )
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="output image (default: <folder>/merged_singlejaw.png)")
    parser.add_argument("--gap", type=int, default=120,
                        help="gap between tiles and rows in pixels (default: 24)")
    parser.add_argument("--background", default="white",
                        help="background colour (default: white)")
    parser.add_argument("--font-size", type=int, default=100,
                        help="column heading font size")
    # 上方文字和图片的距离
    parser.add_argument("--header-gap", type=int, default=60,
                        help="distance from heading text to images in pixels")
    parser.add_argument("--colorbar-x", type=int, default=5200,
                        help="colorbar left position in pixels (default: right of images)")
    parser.add_argument("--colorbar-y", type=int, default=2580,
                        help="colorbar top position in pixels (default: bottom aligned)")
    parser.add_argument("--colorbar-length", type=int, default=1300,
                        help="colorbar length in pixels (default: 70%% of image height)")
    parser.add_argument("--colorbar-thickness", type=int, default=60,
                        help="colorbar strip thickness in pixels")
    parser.add_argument("--colorbar-font-size", type=int, default=90,
                        help="colorbar tick and unit font size in pixels")
    args = parser.parse_args()
    if args.colorbar_length is not None and args.colorbar_length < 2:
        parser.error("colorbar-length must be at least 2 pixels")
    if args.colorbar_thickness <= 0:
        parser.error("colorbar-thickness must be positive")
    if args.colorbar_font_size <= 0:
        parser.error("colorbar-font-size must be positive")
    if args.font_size <= 0 or args.header_gap < 0:
        parser.error("font-size must be positive and header-gap nonnegative")

    root = args.folder.resolve()
    output = (args.output or root / "method_comparison_preview.png").resolve()
    sample_dirs = sorted(
        path for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name != "__pycache__"
    )
    if not sample_dirs:
        parser.error(f"no subfolders found in {root}")
    if ROW_ORDER:
        by_name = {path.name: path for path in sample_dirs}
        missing = [name for name in ROW_ORDER if name not in by_name]
        if missing:
            parser.error("row-order folders not found: " + ", ".join(missing))
        sample_dirs = ([by_name[name] for name in ROW_ORDER]
                       + [path for path in sample_dirs if path.name not in ROW_ORDER])
        print("row order: " + ", ".join(path.name for path in sample_dirs))

    rows: list[tuple[Path, ...]] = []
    for sample_dir in sample_dirs:
        for names in ROW_FILES:
            paths = tuple(sample_dir / name for name in names)
            missing = [str(path.name) for path in paths if not path.is_file()]
            if missing:
                print(f"skip {sample_dir.name}/{', '.join(missing)} (missing)")
                continue
            rows.append(paths)

    if not rows:
        parser.error("no complete image rows found")

    images = [[Image.open(path).convert("RGB") for path in row] for row in rows]
    tile_width = max(image.width for row in images for image in row)
    tile_height = max(image.height for row in images for image in row)
    columns = max(len(row) for row in images)
    header_height = args.font_size + args.header_gap
    bar_length = args.colorbar_length or max(2, round(tile_height * 0.7))
    default_x = (args.gap + columns * tile_width + (columns - 1) * args.gap
                 + COLORBAR_GAP)
    colorbar_x = default_x if args.colorbar_x is None else args.colorbar_x
    canvas_height = (args.gap + header_height + len(images) * tile_height
                     + (len(images) - 1) * args.gap + args.gap)
    colorbar_y = (canvas_height - args.gap - (bar_length + 50)
                  if args.colorbar_y is None else args.colorbar_y)
    if min(colorbar_x, colorbar_y) < 0:
        parser.error("colorbar position must be nonnegative")
    canvas_width = max(args.gap + columns * tile_width + (columns - 1) * args.gap
                       + args.gap, colorbar_x + COLORBAR_WIDTH + args.gap)
    canvas_height = max(canvas_height, colorbar_y + bar_length + 50 + args.gap)
    canvas = Image.new("RGB", (canvas_width, canvas_height), args.background)
    draw = ImageDraw.Draw(canvas)
    try:
        heading_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", args.font_size)
    except OSError:
        heading_font = ImageFont.load_default(size=args.font_size)
    for column, label in enumerate(COLUMN_LABELS[:columns]):
        x = args.gap + column * (tile_width + args.gap) + tile_width // 2
        draw.text((x, args.gap + args.font_size // 2), label,
                  font=heading_font, fill="black", anchor="mm")

    for row_index, row in enumerate(images):
        y = args.gap + header_height + row_index * (tile_height + args.gap)
        for col_index, image in enumerate(row):
            x = args.gap + col_index * (tile_width + args.gap)
            tile = ImageOps.contain(image, (tile_width, tile_height))
            canvas.paste(tile, (x + (tile_width - tile.width) // 2,
                                y + (tile_height - tile.height) // 2))
    # Draw one shared colorbar, defaulting to the lower-right corner.
    # Overlay one shared colorbar only after the complete image grid is drawn.
    colorbar = make_colorbar(bar_length, args.colorbar_thickness,
                             args.colorbar_font_size, "(mm)")
    canvas.paste(colorbar, (colorbar_x, colorbar_y))

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(f"saved {output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
