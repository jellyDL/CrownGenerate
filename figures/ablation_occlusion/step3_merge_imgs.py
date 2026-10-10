#!/usr/bin/env python3
"""Merge occlusion-ablation heatmaps into a labelled contact sheet."""
from __future__ import annotations
import argparse, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from matplotlib import colormaps

SCRIPT_DIR = Path(__file__).resolve().parent
ROW_FILES = ("gt_heatmap.png", "ablation_heatmap.png", "our_heatmap.png")

def load_font(size: int, bold: bool = False):
    names = ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "DejaVuSans-Bold.ttf") if bold else ("/System/Library/Fonts/Supplemental/Arial.ttf", "DejaVuSans.ttf")
    for name in names:
        try: return ImageFont.truetype(name, size)
        except OSError: pass
    return ImageFont.load_default(size=size)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", nargs="?", type=Path, default=SCRIPT_DIR)
    parser.add_argument("-o", "--output", type=Path, default=Path("merged_heatmaps.png"))
    parser.add_argument("--gap", type=int, default=60, help="tile gap and outer margin (pixels)")
    parser.add_argument("--header-gap", type=int, default=25, help="gap below column labels (pixels)")
    parser.add_argument("--font-size", type=int, default=90, help="column label font size")
    parser.add_argument("--labels", nargs=3, default=("GT", "Without Intersection", "With Intersection"), metavar=("GT", "WITHOUT", "WITH"))
    parser.add_argument("--background", default="white")
    parser.add_argument("--clim", nargs="+", type=float, default=[0.0, 0.2], help="colorbar limits: MAX or MIN MAX")
    parser.add_argument("--colorbar-font-size", type=int, default=50)
    parser.add_argument("--colorbar-length", type=int, default=None, help="vertical colorbar length; default is 70%% of image height")
    parser.add_argument("--colorbar-thickness", type=int, default=35)
    parser.add_argument("--colorbar-gap", type=int, default=50)
    parser.add_argument("--colorbar-position", nargs=2, type=int, default=None, metavar=("X", "Y"), help="colorbar top-left position; default is right of images")
    args = parser.parse_args()
    if len(args.clim) not in (1, 2): parser.error("--clim expects MAX or MIN MAX")
    vmin, vmax = (0.0, args.clim[0]) if len(args.clim) == 1 else args.clim
    if not all(math.isfinite(v) for v in (vmin, vmax)) or vmin >= vmax: parser.error("--clim must contain finite limits with MIN < MAX")
    if min(args.gap, args.header_gap, args.colorbar_gap) < 0 or args.font_size <= 0: parser.error("gaps must be nonnegative and font-size must be positive")
    if args.colorbar_thickness <= 0 or args.colorbar_font_size <= 0: parser.error("colorbar dimensions and font size must be positive")
    root = args.folder.expanduser().resolve()
    if not root.is_dir(): parser.error(f"folder does not exist: {root}")
    sample_dirs = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__")
    rows = []
    for sample_dir in sample_dirs:
        paths = tuple(sample_dir / name for name in ROW_FILES)
        missing = [p.name for p in paths if not p.is_file()]
        if missing:
            print(f"skip {sample_dir.name}/{', '.join(missing)} (missing)"); continue
        with_images = []
        for path in paths:
            with Image.open(path) as image: with_images.append(image.convert("RGB"))
        rows.append(with_images)
    if not rows: parser.error(f"no complete image rows found in {root}")
    tile_width = max(image.width for row in rows for image in row)
    tile_height = max(image.height for row in rows for image in row)
    font = load_font(args.font_size)
    header_height = args.font_size + args.header_gap
    image_height = len(rows) * tile_height + (len(rows) - 1) * args.gap
    image_left = args.gap; image_right = image_left + 3 * tile_width + 2 * args.gap
    bar_length = args.colorbar_length or max(2, round(image_height * 0.7))
    if bar_length > image_height: parser.error(f"colorbar-length must not exceed image region height ({image_height} pixels)")
    bar_x, bar_y = args.colorbar_position or (image_right + args.colorbar_gap, args.gap + header_height + image_height - bar_length)
    if min(bar_x, bar_y) < 0: parser.error("colorbar-position coordinates must be nonnegative")
    colorbar_font = load_font(args.colorbar_font_size)
    tick_labels = [f"{vmin + (vmax - vmin) * i / 4:.4g}" for i in range(5)]
    tick_width = max(colorbar_font.getlength(x) for x in tick_labels)
    canvas_width = max(image_right + args.gap, bar_x + args.colorbar_thickness + 20 + int(tick_width) + args.gap)
    canvas_height = max(args.gap + header_height + image_height + args.gap, bar_y + bar_length + args.colorbar_font_size + args.gap)
    canvas = Image.new("RGB", (canvas_width, canvas_height), args.background); draw = ImageDraw.Draw(canvas)
    for column, label in enumerate(args.labels):
        x = image_left + column * (tile_width + args.gap) + tile_width // 2
        draw.text((x, args.gap + args.font_size // 2), label, font=font, fill="black", anchor="mm")
    for row_index, row in enumerate(rows):
        y = args.gap + header_height + row_index * (tile_height + args.gap)
        for column, image in enumerate(row):
            x = image_left + column * (tile_width + args.gap); tile = ImageOps.contain(image, (tile_width, tile_height))
            canvas.paste(tile, (x + (tile_width - tile.width) // 2, y + (tile_height - tile.height) // 2))
    draw.text((bar_x, bar_y - 12), "(mm)", font=colorbar_font, fill="black", anchor="lb")
    cmap = colormaps["jet_r"]
    for index in range(bar_length):
        color = tuple(round(c * 255) for c in cmap(1 - index / (bar_length - 1))[:3])
        draw.line((bar_x, bar_y + index, bar_x + args.colorbar_thickness - 1, bar_y + index), fill=color)
    draw.rectangle((bar_x, bar_y, bar_x + args.colorbar_thickness - 1, bar_y + bar_length - 1), outline="black")
    for i, label in enumerate(tick_labels):
        tick_y = bar_y + round((bar_length - 1) * (1 - i / 4))
        draw.line((bar_x + args.colorbar_thickness, tick_y, bar_x + args.colorbar_thickness + 8, tick_y), fill="black")
        draw.text((bar_x + args.colorbar_thickness + 14, tick_y), label, font=colorbar_font, fill="black", anchor="lm")
    output = args.output.expanduser(); output = output if output.is_absolute() else SCRIPT_DIR / output
    output.parent.mkdir(parents=True, exist_ok=True); canvas.save(output)
    print(f"saved {output.resolve()} ({len(rows)} rows)")

if __name__ == "__main__": main()
