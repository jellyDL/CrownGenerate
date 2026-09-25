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
    "our_singlejaw.png",
    "gt_singlejaw.png",
),)
COLORBAR_WIDTH = 62


def make_colorbar(height: int) -> Image.Image:
    """Create a vertical turbo colorbar matching method_comparison_preview2."""
    values = np.linspace(1.0, 0.0, height)
    rgb = (colormaps["turbo"](values)[:, :3] * 255).astype(np.uint8)
    bar_width = 18
    bar = Image.fromarray(np.repeat(rgb[:, None, :], bar_width, axis=1), "RGB")
    canvas = Image.new("RGB", (COLORBAR_WIDTH, height), "white")
    canvas.paste(bar, (0, 0))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    # Six evenly spaced ticks, with the largest positive value at the top.
    labels = ["0.03", "0.02", "0.01", "0.00", "-0.01", "-0.02", "-0.03"]
    for index, label in enumerate(labels):
        y = round(index * (height - 1) / (len(labels) - 1))
        draw.line((bar_width, y, bar_width + 4, y), fill="black", width=1)
        text_y = max(0, min(height - 11, y - 5))
        draw.text((bar_width + 7, text_y), label, fill="black", font=font)
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
    parser.add_argument("--gap", type=int, default=12,
                        help="gap between tiles in pixels (default: 12)")
    parser.add_argument("--background", default="white",
                        help="background colour (default: white)")
    args = parser.parse_args()

    root = args.folder.resolve()
    output = (args.output or root / "merged_all.png").resolve()
    sample_dirs = sorted(
        path for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name != "__pycache__"
    )
    if not sample_dirs:
        parser.error(f"no subfolders found in {root}")

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
    canvas_width = (args.gap + columns * tile_width + (columns - 1) * args.gap
                    + args.gap + COLORBAR_WIDTH + args.gap)
    canvas_height = args.gap + len(images) * tile_height + (len(images) - 1) * args.gap + args.gap
    canvas = Image.new("RGB", (canvas_width, canvas_height), args.background)

    for row_index, row in enumerate(images):
        y = args.gap + row_index * (tile_height + args.gap)
        for col_index, image in enumerate(row):
            x = args.gap + col_index * (tile_width + args.gap)
            tile = ImageOps.contain(image, (tile_width, tile_height))
            canvas.paste(tile, (x + (tile_width - tile.width) // 2,
                                y + (tile_height - tile.height) // 2))
        colorbar = make_colorbar(tile_height)
        colorbar_x = args.gap + columns * tile_width + columns * args.gap
        canvas.paste(colorbar, (colorbar_x, y))

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(f"saved {output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
