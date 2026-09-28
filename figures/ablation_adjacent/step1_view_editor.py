#!/usr/bin/env python3
"""Choose and save the camera view for the occlusion heatmap."""
from __future__ import annotations

import argparse, json
from pathlib import Path
import pyvista as pv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    folder = args.folder.resolve()
    gt = pv.read(folder / "gt.stl")
    plotter = pv.Plotter(window_size=(900, 700))
    plotter.set_background("#f4f7f4")
    gt_actor = plotter.add_mesh(gt, color="#d8d8d0", smooth_shading=True, opacity=1.0)
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
        plotter.render()

    step = 0.5
    plotter.add_key_event("Left", lambda: move(-step, 0))
    plotter.add_key_event("Right", lambda: move(step, 0))
    plotter.add_key_event("Up", lambda: move(0, step))
    plotter.add_key_event("Down", lambda: move(0, -step))
    plotter.show()


if __name__ == "__main__":
    main()
