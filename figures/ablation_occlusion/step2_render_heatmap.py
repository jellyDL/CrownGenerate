#!/usr/bin/env python3
"""Render crown meshes using the supplied exocad Intersection color scale.

Distances from MIN to MAX: red, orange, yellow, green, cyan, dark blue.
Below MIN saturates red; above MAX is white. Default range: -1..0 mm.
Geometry and distance computation are unchanged by this visual mapping.
The opposing jaw is selected from the FDI prefix of <FDI>-margin.xyz.
"""
from __future__ import annotations

import argparse, json, re
from pathlib import Path
import numpy as np
import pyvista as pv
from occlusion_colormap import (
    BACKGROUND_COLOR, DEFAULT_LIMITS, PENETRATION_COLOR, occlusion_colormap,
)


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
    parser.add_argument("--clim", nargs="+", type=float, default=DEFAULT_LIMITS,
                        help="distance range in mm: MIN or MIN MAX (default: -1 0); a single MIN uses MAX=0; any finite MIN < MAX is allowed")
    # 删除多少三角面片，值越大删除越多
    parser.add_argument("--jaw-reduction", type=float, default=0.9,
                        help="∂ 0 keeps all (default: 0.9)")
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    if len(args.clim) not in (1, 2):
        parser.error("--clim expects MIN or MIN MAX")
    vmin, vmax = (args.clim[0], 0.0) if len(args.clim) == 1 else args.clim
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
        parser.error("--clim requires finite MIN < MAX")
    if not np.isfinite(args.jaw_reduction) or not 0 <= args.jaw_reduction < 1:
        parser.error('--jaw-reduction must be finite and in [0, 1)')
    folder = args.folder.expanduser().resolve()
    try:
        tooth_number, jaw_path = select_opposing_jaw(folder)
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    print(f"FDI {tooth_number}: opposing jaw = {jaw_path.name}")
    view = json.loads((folder / "occlusion_view.json").read_text()).get("camera")
    jaw = pv.read(jaw_path).triangulate()
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
        except Exception as exc:
            raise RuntimeError(
                f"Cannot compute signed distance for {stem}; an unsigned "
                "nearest-neighbor fallback cannot identify penetration."
            ) from exc
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Non-finite signed distances in {stem}")
        # Use the signed distance directly: MIN maps to red and MAX to blue.
        # Positive distances remain visible whenever MAX includes clearance.
        contact_values = values.astype(float, copy=True)
        contact_values[contact_values > vmax] = np.nan
        crown["surface_distance"] = contact_values
        plotter = pv.Plotter(off_screen=True, window_size=(900, 700))
        plotter.set_background("white")
        plotter.add_mesh(wire_jaw, color="#a8aaa5", style="wireframe", line_width=2.0,
                         opacity=0.32, show_edges=True)
        plotter.add_mesh(crown, scalars="surface_distance", cmap=occlusion_colormap(),
                         clim=(vmin, vmax), smooth_shading=True,
                         below_color=PENETRATION_COLOR,
                         nan_color=BACKGROUND_COLOR, nan_opacity=1.0,
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
