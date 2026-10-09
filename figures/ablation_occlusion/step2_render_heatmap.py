#!/usr/bin/env python3
"""Render gt.stl as an implicit-distance heatmap with a transparent wire jaw."""
from __future__ import annotations

import argparse, json
from pathlib import Path
import numpy as np
import pyvista as pv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--clim", type=float, default=0.2)
    # 删除多少三角面片，值越大删除越多
    parser.add_argument("--jaw-reduction", type=float, default=0.9,
                        help="∂ 0 keeps all (default: 0.9)")
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    if not np.isfinite(args.jaw_reduction) or not 0 <= args.jaw_reduction < 1:
        parser.error('--jaw-reduction must be finite and in [0, 1)')
    folder = args.folder.resolve()
    view = json.loads((folder / "occlusion_view.json").read_text()).get("camera")
    jaw = pv.read(folder / "upperjaw.ply").triangulate()
    translation = view.get("translation", [0.0, 0.0, 0.0]) if view else [0.0, 0.0, 0.0]
    jaw.points = np.asarray(jaw.points) + np.asarray(translation)
    # Only simplify the displayed wireframe; distances use the full surface.
    wire_jaw = jaw.decimate(args.jaw_reduction, inplace=False) if args.jaw_reduction else jaw
    for stem in ("gt", "our", "ablation"):
        crown = pv.read(folder / f"{stem}.stl")
        crown.points = np.asarray(crown.points) + np.asarray(translation)
        try:
            result = crown.compute_implicit_distance(jaw, inplace=False)
            values = np.asarray(result["implicit_distance"])
        except Exception:
            from scipy.spatial import cKDTree
            values = cKDTree(np.asarray(jaw.points)).query(np.asarray(crown.points), k=1)[0]
        contact_values = values.astype(float, copy=True)
        contact_values[np.abs(contact_values) > abs(args.clim)] = np.nan
        crown["implicit_distance"] = contact_values
        plotter = pv.Plotter(off_screen=True, window_size=(900, 700))
        plotter.set_background("white")
        plotter.add_mesh(wire_jaw, color="#a8aaa5", style="wireframe", line_width=2.0,
                         opacity=0.32, show_edges=True)
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
