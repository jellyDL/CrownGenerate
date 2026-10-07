#!/usr/bin/env python3
"""Merge ordered case folders into one image with two rows per case.

exp. python step3_merge_imgs.py --folders "01bd10c4-0849-5ad8-a874-3be804541e00" "000b8258-0e4a-5d78-8187-e1c5621492be"
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


SCRIPT_DIR = Path(__file__).resolve().parent
ROW_FILES = (
    ("gt_heatmap.png", "ablation_match_heatmap.png", "our_heatmap.png"),
    ("gt_heatmap2.png", "ablation_match_heatmap2.png", "our_heatmap2.png"),
)
COLUMN_LABELS = ("GT", "With out Intersection", "With Intersection")


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
    parser.add_argument("--block_space", "--block-space", type=int, default=80,
                        help="vertical gap between case blocks (default: 80)")
    parser.add_argument("--font-size", type=int, default=68,
                        help="column title font size (default: 68)")
    parser.add_argument("--background", default="white")
    args = parser.parse_args()
    if min(args.gap, args.line_space, args.block_space) < 0:
        parser.error("gap, line_space and block_space must be nonnegative")
    if args.font_size <= 0:
        parser.error("font-size must be positive")

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
    for font_path in ("/System/Library/Fonts/Supplemental/Arial.ttf", "DejaVuSans.ttf"):
        try:
            font = ImageFont.truetype(font_path, args.font_size)
            break
        except OSError:
            continue
    else:
        font = ImageFont.load_default()
    header_height = args.font_size + 40
    block_height = 2 * tile_height + args.line_space
    canvas_width = 3 * tile_width + 4 * args.gap
    canvas_height = (2 * args.gap + header_height + len(blocks) * block_height
                     + (len(blocks) - 1) * args.block_space)
    canvas = Image.new("RGB", (canvas_width, canvas_height), args.background)
    draw = ImageDraw.Draw(canvas)
    for column, label in enumerate(COLUMN_LABELS):
        center_x = args.gap + column * (tile_width + args.gap) + tile_width // 2
        draw.text((center_x, args.gap + header_height // 2), label,
                  font=font, fill="black", anchor="mm")
    for block_index, block in enumerate(blocks):
        block_y = args.gap + header_height + block_index * (block_height + args.block_space)
        for row_index, row in enumerate(block):
            y = block_y + row_index * (tile_height + args.line_space)
            for column, image in enumerate(row):
                x = args.gap + column * (tile_width + args.gap)
                tile = ImageOps.contain(image, (tile_width, tile_height))
                canvas.paste(tile, (x + (tile_width - tile.width) // 2,
                                    y + (tile_height - tile.height) // 2))
    output = args.output.expanduser()
    if not output.is_absolute():
        output = SCRIPT_DIR / output
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(f"saved {output.resolve()} ({len(blocks)} blocks)")


if __name__ == "__main__":
    main()
