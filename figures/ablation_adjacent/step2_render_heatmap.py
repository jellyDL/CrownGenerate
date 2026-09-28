#!/usr/bin/env python3
"""Render local crown-to-lowerjaw surface distances using the saved view."""
from __future__ import annotations

import argparse, json
from pathlib import Path
import numpy as np
import pyvista as pv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--clim", type=float, default=0.2)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    if not np.isfinite(args.clim) or args.clim <= 0:
        parser.error('--clim must be a finite positive number')
    folder = args.folder.resolve()
    view = json.loads((folder / "occlusion_view.json").read_text()).get("camera")
    # Keep the full surface for accurate distances; the jaw is not displayed.
    jaw = pv.read(folder / "lowerjaw.ply").triangulate()
    translation = view.get("translation", [0.0, 0.0, 0.0]) if view else [0.0, 0.0, 0.0]
    jaw.points = np.asarray(jaw.points) + np.asarray(translation)
    for stem in ("gt",):
        crown = pv.read(folder / f"{stem}.stl")
        crown.points = np.asarray(crown.points) + np.asarray(translation)
        result = crown.compute_implicit_distance(jaw, inplace=False)
        values = np.asarray(result["implicit_distance"])
        contact_values = values.astype(float, copy=True)
        contact_values[np.abs(contact_values) > abs(args.clim)] = np.nan
        crown["implicit_distance"] = contact_values
        plotter = pv.Plotter(off_screen=True, window_size=(900, 700))
        plotter.set_background("white")
        plotter.add_mesh(crown, scalars="implicit_distance", cmap="jet",
                         clim=(-abs(args.clim), abs(args.clim)), smooth_shading=True,
                         nan_color="white", nan_opacity=1.0,
                         show_scalar_bar=False)
        if view:
            plotter.camera.position = view["position"]
            plotter.camera.focal_point = view["focal_point"]
            plotter.camera.up = view["viewup"]
            plotter.camera.parallel_scale = view["parallel_scale"]
            plotter.camera.parallel_projection = view.get("parallel_projection", False)
            if "view_angle" in view:
                plotter.camera.view_angle = view["view_angle"]
            if "clipping_range" in view:
                plotter.camera.clipping_range = view["clipping_range"]
        output = args.output if args.output and stem == "gt" else folder / f"{stem}_heatmap.png"
        plotter.show(screenshot=str(output), auto_close=True)
        print(output)


if __name__ == "__main__":
    main()
