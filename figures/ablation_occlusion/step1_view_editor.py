#!/usr/bin/env python3
"""Choose and save the camera view for the occlusion heatmap."""
from __future__ import annotations

import argparse, json, re
from pathlib import Path
import pyvista as pv


def select_opposing_jaw(folder: Path) -> tuple[int, Path]:
    """Select the antagonist for the single tooth identified by its margin file."""
    margins = sorted(p for p in folder.glob("*-margin.xyz") if p.is_file())
    if len(margins) != 1:
        raise ValueError(
            f"Expected exactly one <FDI>-margin.xyz in {folder}; "
            f"found {len(margins)}: {', '.join(p.name for p in margins)}"
        )
    match = re.fullmatch(r"(\d{2})-margin\.xyz", margins[0].name)
    if match is None:
        raise ValueError(f"Invalid margin filename: {margins[0].name}; expected <FDI>-margin.xyz")
    tooth_number = int(match.group(1))
    if 31 <= tooth_number <= 37 or 41 <= tooth_number <= 47:
        candidates = ("upperjaw.ply",)
    elif 11 <= tooth_number <= 17 or 21 <= tooth_number <= 27:
        candidates = ("lowerjaw.ply", "lower.ply")
    else:
        raise ValueError(
            f"Unsupported FDI {tooth_number}; expected 11–17, 21–27, 31–37 or 41–47"
        )
    for name in candidates:
        path = folder / name
        if path.is_file():
            return tooth_number, path
    raise FileNotFoundError(
        f"Missing opposing jaw for FDI {tooth_number} in {folder}; "
        f"expected {' or '.join(candidates)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    folder = args.folder.expanduser().resolve()
    try:
        tooth_number, jaw_path = select_opposing_jaw(folder)
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    print(f"FDI {tooth_number}: opposing jaw = {jaw_path.name}")
    gt = pv.read(folder / "gt.stl")
    jaw = pv.read(jaw_path).decimate(0.95, inplace=False)
    plotter = pv.Plotter(window_size=(900, 700))
    plotter.set_background("#f4f7f4")
    gt_actor = plotter.add_mesh(gt, color="#d8d8d0", smooth_shading=True, opacity=1.0)
    jaw_actor = plotter.add_mesh(jaw, color="#a8aaa5", style="wireframe", line_width=2.0,
                                 opacity=0.35, show_edges=True)
    translation = [0.0, 0.0, 0.0]
    plotter.add_text("Adjust view, then press P to save | Esc to quit", position="upper_left")
    output = (args.output or folder / "occlusion_view.json").resolve()

    def save() -> None:
        camera = plotter.camera
        payload = {"camera": {
            "position": list(camera.position),
            "focal_point": list(camera.focal_point),
            "viewup": list(camera.up),
            "parallel_scale": float(camera.parallel_scale),
            "parallel_projection": bool(camera.parallel_projection),
            "view_angle": float(camera.view_angle),
            "clipping_range": list(camera.clipping_range),
            "translation": translation,
        }}
        output.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"saved {output}")

    plotter.add_key_event("p", save)
    def move(dx: float, dy: float) -> None:
        translation[0] += dx
        translation[1] += dy
        gt_actor.SetPosition(*translation)
        jaw_actor.SetPosition(*translation)
        plotter.render()

    step = 0.5
    plotter.add_key_event("Left", lambda: move(-step, 0))
    plotter.add_key_event("Right", lambda: move(step, 0))
    plotter.add_key_event("Up", lambda: move(0, step))
    plotter.add_key_event("Down", lambda: move(0, -step))
    plotter.show()


if __name__ == "__main__":
    main()
