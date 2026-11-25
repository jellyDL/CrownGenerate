#!/usr/bin/env python3
"""Merge ordered case folders into one image with two rows per case.

exp. python step3_merge_imgs.py --folders "01bd10c4-0849-5ad8-a874-3be804541e00" "000b8258-0e4a-5d78-8187-e1c5621492be"
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
from matplotlib import colormaps


SCRIPT_DIR = Path(__file__).resolve().parent
ROW_FILES = (
    ("gt_heatmap.png", "ablation_match_heatmap.png", "our_heatmap.png"),
    ("gt_heatmap2.png", "ablation_match_heatmap2.png", "our_heatmap2.png"),
)
COLUMN_LABELS = ("Reference Crown", "Single-stage", "Two-stage")
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


def row_crop_bounds(rows: list[list[Image.Image]], tile_height: int, padding: int) -> tuple[int, int]:
    # One vertical crop for all six tiles retains alignment across methods and views.
    top, bottom = tile_height, 0
    for row in rows:
        for tile in row:
            foreground = ImageChops.difference(tile, Image.new("RGB", tile.size, "white")).getbbox()
            if foreground is not None:
                offset = (tile_height - tile.height) // 2
                top = min(top, offset + foreground[1])
                bottom = max(bottom, offset + foreground[3])
    if top >= bottom:
        return 0, tile_height
    return max(0, top - padding), min(tile_height, bottom + padding)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", nargs="?", type=Path, default=SCRIPT_DIR,
                        help="parent folder containing cases (default: script directory)")

    # 指定文件夹和显示顺序，每个文件夹占两行。
    parser.add_argument("--folders", nargs="+", help="case folder names in display order")
    parser.add_argument("-o", "--output", type=Path, default=Path("merged_heatmaps.png"),
                        help="output filename; relative paths use the script directory")
    parser.add_argument("--gap", type=int, default=30,
                        help="outer margin in pixels (default: %(default)s)")
    # 列间距
    parser.add_argument("--column-gap", "--column_gap", type=int, default=380,
                        help="horizontal gap between columns in pixels (default: %(default)s)")
    # 板块内两行间距，单位像素。
    parser.add_argument("--line_space", "--line-space", type=int, default=0,
                        help="extra gap between the two rows in each block (default: %(default)s)")
    # 每个板块的行间距
    parser.add_argument("--row-padding", type=int, metavar="PX", default=80,
                        help="trim the white top and bottom margins of the tiles in each case, keeping PX of padding")
    # 板块之间的竖直间距，单位像素。
    parser.add_argument("--block_space", "--block-space", type=int, default=80,
                        help="vertical gap between case blocks (default: 80)")
    # 上方文字字体大小
    parser.add_argument("--font-size", type=int, default=120,
                        help="column title font size (default: 68)")
    # 上方文字离图片距离
    parser.add_argument("--header-gap", "--header_gap", type=int, metavar="PX", default=80,
                        help="gap from the bottom of the column labels to the first image row in pixels")
    # 左侧标签与第一列图片的间距
    parser.add_argument("--left-label-gap", "--left_label_gap", type=int, default=400,
                        help="gap from left-side labels to the first image column in pixels (default: %(default)s)")
    # 左侧文字字体大小
    parser.add_argument("--block-font-size", "--block_font_size", type=int, default=130,
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
    default_colorbar_length = 900
    parser.add_argument("--colorbar-length", "--colorbar-width", "--colorbar_width",
                        dest="colorbar_width", type=int,
                        help=f"vertical colorbar length in pixels (default: {default_colorbar_length}, or shorter with row cropping)")
    # 色带图带宽
    parser.add_argument("--colorbar-thickness", type=int, default=70,
                        help="vertical colorbar thickness in pixels (default: 30)")
    parser.add_argument("--colorbar-gap", type=int, default=80,
                        help="horizontal gap between images and colorbar (default: 80)")
    # 色带图位置
    parser.add_argument("--colorbar-position", "--colorbar_position", nargs=2, type=int,
                        default=(4750, 1680), metavar=("X", "Y"),
                        help="colorbar top-left pixel coordinates; origin is image top-left (default: 3500 1500)")
    args = parser.parse_args()
    if len(args.clim) not in (1, 2):
        parser.error("--clim expects MAX or MIN MAX")
    vmin, vmax = (0.0, args.clim[0]) if len(args.clim) == 1 else args.clim
    if not all(math.isfinite(value) for value in (vmin, vmax)) or vmin >= vmax:
        parser.error("--clim must contain finite limits with MIN < MAX")
    column_gap = args.gap if args.column_gap is None else args.column_gap
    if min(args.gap, column_gap, args.line_space, args.block_space, args.colorbar_gap) < 0:
        parser.error("gap, column-gap, line-space, block-space and colorbar-gap must be nonnegative")
    if args.header_gap is not None and args.header_gap < 0:
        parser.error("header-gap must be nonnegative")
    if args.left_label_gap < 0:
        parser.error("left-label-gap must be nonnegative")
    if args.row_padding is not None and args.row_padding < 0:
        parser.error("row-padding must be nonnegative")
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
    blocks = [[[ImageOps.contain(image, (tile_width, tile_height)) for image in row]
               for row in block] for block in blocks]
    crop_bounds = ([(0, tile_height)] * len(blocks) if args.row_padding is None else
                   [row_crop_bounds(block, tile_height, args.row_padding) for block in blocks])
    font = load_font(args.font_size)
    block_font = load_font(args.block_font_size, bold=args.block_bold)
    labels = BLOCK_LABELS[:len(blocks)]
    label_width = max(block_font.getbbox(label)[2] - block_font.getbbox(label)[0]
                      for label in labels)
    left_width = label_width + args.left_label_gap
    header_height = args.font_size + 40
    header_center = header_height // 2
    if args.header_gap is not None:
        label_bottom = max(font.getbbox(label, anchor="mm")[3] for label in COLUMN_LABELS)
        header_height = header_center + label_bottom + args.header_gap
    colorbar_font = load_font(args.colorbar_font_size)
    block_heights = [2 * (bottom - top) + args.line_space for top, bottom in crop_bounds]
    image_height = sum(block_heights) + (len(blocks) - 1) * args.block_space
    tick_labels = [f"{vmin + (vmax - vmin) * tick / 4:.4g}" for tick in range(5)]
    max_tick_width = math.ceil(max(colorbar_font.getlength(label) for label in [*tick_labels, "(mm)"]))
    bar_length = args.colorbar_width
    if bar_length is None:
        bar_length = default_colorbar_length
        if args.row_padding is not None:
            bar_length = min(bar_length, image_height)
    if bar_length > image_height:
        parser.error(f"colorbar-length must not exceed the image region height ({image_height} pixels)")
    image_left = left_width + args.gap
    column_stride = tile_width + column_gap
    image_right = image_left + (len(COLUMN_LABELS) - 1) * column_stride + tile_width
    bar_x, bar_y = args.colorbar_position or default_colorbar_position
    if args.colorbar_position is None and args.left_label_gap > args.left_label_gap:
        bar_x = max(bar_x, image_right + args.colorbar_gap)
    if args.colorbar_position is None and args.row_padding is not None:
        bar_y = args.gap + header_height + (image_height - bar_length) // 2
    canvas_width = max(image_right + args.gap,
                       bar_x + args.colorbar_thickness + 16 + max_tick_width + max(args.gap, 20))
    canvas_height = max(2 * args.gap + header_height + image_height,
                        bar_y + bar_length + args.colorbar_font_size + 20)
    canvas = Image.new("RGB", (canvas_width, canvas_height), args.background)
    draw = ImageDraw.Draw(canvas)
    for column, label in enumerate(COLUMN_LABELS):
        center_x = image_left + column * column_stride + tile_width // 2
        draw.text((center_x, args.gap + header_center), label,
                  font=font, fill="black", anchor="mm")
    block_y = args.gap + header_height
    for block_index, (block, (top, bottom), block_height) in enumerate(zip(blocks, crop_bounds, block_heights)):
        if block_index < len(BLOCK_LABELS):
            draw.text((args.gap + label_width // 2, block_y + block_height // 2),
                      BLOCK_LABELS[block_index], font=block_font, fill="black", anchor="mm")
        for row_index, row in enumerate(block):
            y = block_y + row_index * (bottom - top + args.line_space)
            for column, tile in enumerate(row):
                x = image_left + column * column_stride
                offset = (tile_height - tile.height) // 2
                crop_top = max(0, top - offset)
                crop_bottom = min(tile.height, bottom - offset)
                if crop_top < crop_bottom:
                    canvas.paste(tile.crop((0, crop_top, tile.width, crop_bottom)),
                                 (x + (tile_width - tile.width) // 2, y + offset + crop_top - top))
        block_y += block_height + args.block_space
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
