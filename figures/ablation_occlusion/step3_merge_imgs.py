#!/usr/bin/env python3
"""Merge occlusion-ablation heatmaps with the shared Shining3D-style legend."""
from __future__ import annotations
import argparse, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from occlusion_colormap_shining3d import DEFAULT_LIMITS, PENETRATION_COLOR, occlusion_colormap

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
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--cases", nargs="+", metavar="DIR", help="case folders in top-to-bottom order, relative to folder or absolute")
    selection.add_argument("--list", dest="case_list", type=Path, help="file listing case folders in top-to-bottom order")
    parser.add_argument("-o", "--output", type=Path, default=Path("merged_heatmaps.png"))
    parser.add_argument("--gap", type=int, default=60, help="tile gap and outer margin (pixels)")
    # 上方文字和图片的距离
    parser.add_argument("--header-gap", type=int, default=80, help="distance from the bottom of column label text to images (pixels)")
    parser.add_argument("--font-size", type=int, default=80, help="column label font size")
    parser.add_argument("--labels", nargs=3, default=("Reference Crown", "Without Intersection", "With Intersection"), metavar=("GT", "WITHOUT", "WITH"))
    parser.add_argument("--background", default="white")
    parser.add_argument("--clim", nargs="+", type=float, default=DEFAULT_LIMITS, help="clearance limits in mm: MAX or 0 MAX (default: 0 0.2); use the same limits as step2")
    parser.add_argument("--colorbar-font-size", type=int, default=80)
    parser.add_argument("--colorbar-unit-gap", type=int, default=30, help="vertical distance between (mm) and the top tick label (pixels)")
    parser.add_argument("--colorbar-length", type=int, default=1200, help="vertical colorbar length; default is 70%% of image height")
    parser.add_argument("--colorbar-thickness", type=int, default=40)
    parser.add_argument("--colorbar-gap", type=int, default=100)
    parser.add_argument("--colorbar-position", nargs=2, type=int, default=(3100,580), metavar=("X", "Y"), help="colorbar top-left position; default is right of images")
    args = parser.parse_args()
    if len(args.clim) not in (1, 2): parser.error("--clim expects MAX or MIN MAX")
    vmin, vmax = (0.0, args.clim[0]) if len(args.clim) == 1 else args.clim
    if not all(math.isfinite(v) for v in (vmin, vmax)) or vmin != 0 or vmax <= 0: parser.error("--clim requires MIN=0 and finite MAX>0; negative distances use the penetration color")
    if min(args.gap, args.header_gap, args.colorbar_gap, args.colorbar_unit_gap) < 0 or args.font_size <= 0: parser.error("gaps must be nonnegative and font-size must be positive")
    if args.colorbar_thickness <= 0 or args.colorbar_font_size <= 0: parser.error("colorbar dimensions and font size must be positive")
    root = args.folder.expanduser().resolve()
    if root.is_file():
        if args.case_list or args.cases:
            parser.error("a positional list file cannot be combined with --list or --cases")
        args.case_list = root
        root = SCRIPT_DIR
    if not root.is_dir(): parser.error(f"folder does not exist: {root}")
    entries = args.cases
    if args.case_list:
        try:
            entries = [line.strip() for line in args.case_list.expanduser().read_text(encoding="utf-8-sig").splitlines()
                       if line.strip() and not line.lstrip().startswith("#")]
        except (OSError, UnicodeError) as exc:
            parser.error(f"cannot read case list: {exc}")
    if entries is not None:
        sample_dirs = [Path(entry).expanduser() for entry in entries]
        sample_dirs = [p if p.is_absolute() else root / p for p in sample_dirs]
    else:
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
        print(f"row {len(rows)}: {sample_dir.name}")
    if not rows: parser.error(f"no complete image rows found in {root}")
    tile_width = max(image.width for row in rows for image in row)
    tile_height = max(image.height for row in rows for image in row)
    font = load_font(args.font_size)
    header_boxes = [font.getbbox(label, anchor="lt") for label in args.labels]
    header_text_height = max(box[3] for box in header_boxes)
    header_height = header_text_height + args.header_gap
    image_height = len(rows) * tile_height + (len(rows) - 1) * args.gap
    image_left = args.gap; image_right = image_left + 3 * tile_width + 2 * args.gap
    bar_length = args.colorbar_length or max(2, round(image_height * 0.7))
    if not 2 <= bar_length <= image_height: parser.error(f"colorbar-length must be between 2 and image region height ({image_height} pixels)")
    bar_x, bar_y = args.colorbar_position or (image_right + args.colorbar_gap, args.gap + header_height + image_height - bar_length)
    if min(bar_x, bar_y) < 0: parser.error("colorbar-position coordinates must be nonnegative")
    colorbar_font = load_font(args.colorbar_font_size)
    tick_count = 5
    tick_labels = [f"{vmin + (vmax - vmin) * i / (tick_count - 1):.4g}" for i in range(tick_count)]
    tick_width = max(colorbar_font.getlength(x) for x in tick_labels + ["<0"])
    penetration_height = max(12, args.colorbar_font_size)
    cap_top = bar_y - penetration_height
    top_tick_box = colorbar_font.getbbox("<0", anchor="lm")
    unit_bottom = cap_top + top_tick_box[1] - args.colorbar_unit_gap
    unit_box = colorbar_font.getbbox("(mm)", anchor="lb")
    if unit_bottom + unit_box[1] < 0: parser.error("colorbar unit would extend above canvas; increase colorbar-position Y or reduce colorbar-unit-gap")
    canvas_width = max(image_right + args.gap, bar_x + args.colorbar_thickness + 20 + math.ceil(tick_width) + args.gap, bar_x + unit_box[2] + args.gap)
    canvas_height = max(args.gap + header_height + image_height + args.gap, bar_y + bar_length + args.colorbar_font_size + args.gap)
    canvas = Image.new("RGB", (canvas_width, canvas_height), args.background); draw = ImageDraw.Draw(canvas)
    for column, label in enumerate(args.labels):
        x = image_left + column * (tile_width + args.gap) + tile_width // 2
        label_height = header_boxes[column][3]
        draw.text((x, args.gap + header_text_height - label_height), label, font=font, fill="black", anchor="mt")
    for row_index, row in enumerate(rows):
        y = args.gap + header_height + row_index * (tile_height + args.gap)
        for column, image in enumerate(row):
            x = image_left + column * (tile_width + args.gap); tile = ImageOps.contain(image, (tile_width, tile_height))
            canvas.paste(tile, (x + (tile_width - tile.width) // 2, y + (tile_height - tile.height) // 2))
    draw.text((bar_x, unit_bottom), "(mm)", font=colorbar_font, fill="black", anchor="lb")
    # Negative distance is blue-violet. Clearance runs from red at zero
    # through yellow to green, using the exact same lookup table as step2.
    cmap = occlusion_colormap()
    draw.rectangle((bar_x, cap_top, bar_x + args.colorbar_thickness - 1, bar_y - 1), fill=PENETRATION_COLOR, outline="black")
    draw.text((bar_x + args.colorbar_thickness + 14, cap_top), "<0", font=colorbar_font, fill="black", anchor="lm")
    for index in range(bar_length):
        color = tuple(round(c * 255) for c in cmap(index / (bar_length - 1))[:3])
        draw.line((bar_x, bar_y + index, bar_x + args.colorbar_thickness - 1, bar_y + index), fill=color)
    draw.rectangle((bar_x, bar_y, bar_x + args.colorbar_thickness - 1, bar_y + bar_length - 1), outline="black")
    for i, label in enumerate(tick_labels):
        tick_y = bar_y + round((bar_length - 1) * i / (tick_count - 1))
        draw.line((bar_x + args.colorbar_thickness, tick_y, bar_x + args.colorbar_thickness + 8, tick_y), fill="black")
        draw.text((bar_x + args.colorbar_thickness + 14, tick_y), label, font=colorbar_font, fill="black", anchor="lm")
    output = args.output.expanduser(); output = output if output.is_absolute() else SCRIPT_DIR / output
    output.parent.mkdir(parents=True, exist_ok=True); canvas.save(output)
    print(f"saved {output.resolve()} ({len(rows)} rows)")

if __name__ == "__main__": main()
