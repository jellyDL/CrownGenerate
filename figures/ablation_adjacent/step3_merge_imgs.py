#!/usr/bin/env python3
"""Merge preview-1 sample renderings into one contact sheet.

For every subfolder, one row is appended in this order::

    gt_heatmap.png  ablation_heatmap.png  our_heatmap.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
from matplotlib import colormaps


ROW_FILES = (
    ("gt_heatmap.png", "ablation_heatmap.png", "our_heatmap.png"),
    ("gt_heatmap2.png", "ablation_heatmap2.png", "our_heatmap2.png"),
)
COLUMN_LABELS = ("GT", "With out Intersection", "With Intersection")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "folder", nargs="?", type=Path,
        default=Path("."),
        help="folder containing sample folders (default: current directory)",
    )
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="output image (default: <folder>/merged_singlejaw.png)")
    parser.add_argument("--gap", type=int, default=80,
                        help="gap between tiles and rows in pixels (default: 24)")
    parser.add_argument("--background", default="white",
                        help="background colour (default: white)")
    args = parser.parse_args()

    root = args.folder.resolve()
    sample_dirs = sorted(
        path for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name != "__pycache__"
    )
    if not sample_dirs:
        parser.error(f"no subfolders found in {root}")

    for sample_dir in sample_dirs:
        rows = [tuple(sample_dir / name for name in names) for names in ROW_FILES]
        missing = sorted({path.name for row in rows for path in row if not path.is_file()})
        if missing:
            print(f"skip {sample_dir.name}/{', '.join(missing)} (missing)")
            continue
        images = [[Image.open(path).convert("RGB") for path in row] for row in rows]
        tile_width = max(image.width for row in images for image in row)
        tile_height = max(image.height for row in images for image in row)
        columns = 3
        font_size = 68 # 显示字体大小
        for font_path in ("/System/Library/Fonts/Supplemental/Arial.ttf", "DejaVuSans.ttf"):
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except OSError:
                continue
        else:
            font = ImageFont.load_default()
        header_height = font_size + 40
        canvas_width = args.gap + columns * tile_width + (columns - 1) * args.gap + args.gap
        canvas_height = header_height + args.gap + 2 * tile_height + args.gap + args.gap
        canvas = Image.new("RGB", (canvas_width, canvas_height), args.background)
        draw = ImageDraw.Draw(canvas)
        for col_index, label in enumerate(COLUMN_LABELS):
            center_x = args.gap + col_index * (tile_width + args.gap) + tile_width // 2
            draw.text((center_x, args.gap + header_height // 2), label,
                      font=font, fill="black", anchor="mm")
        for row_index, row in enumerate(images):
            y = args.gap + header_height + row_index * (tile_height + args.gap)
            for col_index, image in enumerate(row):
                x = args.gap + col_index * (tile_width + args.gap)
                tile = ImageOps.contain(image, (tile_width, tile_height))
                canvas.paste(tile, (x + (tile_width - tile.width) // 2,
                                    y + (tile_height - tile.height) // 2))
        output = (args.output / f"{sample_dir.name}_merged.png" if args.output
                  else sample_dir / "merged_heatmaps.png").resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output)
        print(f"saved {output}")


if __name__ == "__main__":
    main()
