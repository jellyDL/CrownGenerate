#!/usr/bin/env python3
"""Merge preview-1 sample renderings into one contact sheet.

For every subfolder, one row is appended in this order::

    our_diff_gt.png  gt_all.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


ROW_FILES = (("our_diff_gt.png", "gt_all.png"),)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "folder", nargs="?", type=Path,
        default=Path("../method_comparison_preview_1"),
        help="folder containing sample folders (default: ../method_comparison_preview_1)",
    )
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="output image (default: <folder>/merged.png)")
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

    rows: list[tuple[Path, Path]] = []
    for sample_dir in sample_dirs:
        for names in ROW_FILES:
            first = sample_dir / names[0]
            # Older step2 outputs used our_diff_all.png; accept it as a
            # compatibility fallback while preferring the requested name.
            if not first.is_file() and names[0] == "our_diff_gt.png":
                fallback = sample_dir / "our_diff_all.png"
                if fallback.is_file():
                    first = fallback
            paths = (first, sample_dir / names[1])
            missing = [str(path.name) for path in paths if not path.is_file()]
            if missing:
                print(f"skip {sample_dir.name}/{', '.join(missing)} (missing)")
                continue
            rows.append(paths)  # type: ignore[arg-type]

    if not rows:
        parser.error("no complete image rows found")

    images = [[Image.open(path).convert("RGB") for path in row] for row in rows]
    tile_width = max(image.width for row in images for image in row)
    tile_height = max(image.height for row in images for image in row)
    canvas_width = args.gap + 2 * tile_width + args.gap
    canvas_height = args.gap + len(images) * tile_height + (len(images) - 1) * args.gap + args.gap
    canvas = Image.new("RGB", (canvas_width, canvas_height), args.background)

    for row_index, row in enumerate(images):
        y = args.gap + row_index * (tile_height + args.gap)
        for col_index, image in enumerate(row):
            x = args.gap + col_index * (tile_width + args.gap)
            tile = ImageOps.contain(image, (tile_width, tile_height))
            canvas.paste(tile, (x + (tile_width - tile.width) // 2,
                                y + (tile_height - tile.height) // 2))

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(f"saved {output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
