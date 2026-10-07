#!/usr/bin/env python3
"""Render crown-to-jaw surface distances, selecting the jaw by margin FDI."""
from __future__ import annotations

import argparse, json, re
from pathlib import Path
import numpy as np
import pyvista as pv


def fit_margin_plane(margin_points: np.ndarray, reference_points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Orient the fitted cervical plane normal toward the GT crown body."""
    center = margin_points.mean(axis=0)
    _, singular_values, axes = np.linalg.svd(margin_points - center, full_matrices=False)
    if len(margin_points) < 3 or singular_values[1] <= 1e-12:
        raise ValueError("margin points must define a plane")
    normal = axes[-1]
    if np.median((reference_points - center) @ normal) < 0:
        normal = -normal
    return center, normal


def crown_heatmap_values(crown: pv.PolyData, jaw: pv.PolyData,
                         center: np.ndarray, normal: np.ndarray,
                         bottom_height: float, clim: float) -> np.ndarray:
    """Evaluate absolute surface distances above the excluded bottom region."""
    eligible = (np.asarray(crown.points) - center) @ normal > bottom_height
    values = np.full(crown.n_points, np.nan, dtype=float)
    if np.any(eligible):
        query = pv.PolyData(np.asarray(crown.points)[eligible])
        result = query.compute_implicit_distance(jaw, inplace=False)
        values[eligible] = np.abs(np.asarray(result["implicit_distance"]))
    values[values > clim] = np.nan
    return values


def select_jaw_path(folder: Path) -> Path:
    margin_files = sorted(path for path in folder.glob("*-margin.xyz") if path.is_file())
    if len(margin_files) != 1:
        raise ValueError(f"expected exactly one *-margin.xyz file in {folder}, found {len(margin_files)}")
    match = re.fullmatch(r"(\d+)-margin\.xyz", margin_files[0].name)
    if not match:
        raise ValueError(f"invalid FDI margin filename: {margin_files[0].name}")
    fdi = int(match.group(1))
    if 11 <= fdi <= 17 or 21 <= fdi <= 27:
        return folder / "upperjaw.ply"
    if 31 <= fdi <= 37 or 41 <= fdi <= 47:
        return folder / "lowerjaw.ply"
    raise ValueError(f"unsupported FDI tooth number: {fdi}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--clim", type=float, default=0.2)
    parser.add_argument("--bottom-height", type=float, default=1.3,
                        help="exclude vertices at/below this height above the fitted margin plane, in model units (default: 1.3)")
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    if not np.isfinite(args.clim) or args.clim <= 0:
        parser.error('--clim must be a finite positive number')
    if not np.isfinite(args.bottom_height) or args.bottom_height < 0:
        parser.error('--bottom-height must be a finite nonnegative number')
    folder = args.folder.resolve()
    try:
        jaw_path = select_jaw_path(folder)
    except ValueError as exc:
        parser.error(str(exc))
    if not jaw_path.is_file():
        parser.error(f"jaw model does not exist: {jaw_path}")
    view = json.loads((folder / "occlusion_view.json").read_text()).get("camera")
    parallel_scale = None
    if view:
        if view.get("parallel_projection", False):
            parallel_scale = float(view["parallel_scale"])
        else:
            # Match the saved perspective view at its focal plane, then use
            # one orthographic scale for both directions and all crowns.
            distance = np.linalg.norm(np.asarray(view["position"]) - np.asarray(view["focal_point"]))
            parallel_scale = float(distance * np.tan(np.deg2rad(view.get("view_angle", 30.0)) / 2.0))
    # Keep the full surface for accurate distances; the jaw is not displayed.
    jaw = pv.read(jaw_path).triangulate()
    translation = view.get("translation", [0.0, 0.0, 0.0]) if view else [0.0, 0.0, 0.0]
    jaw.points = np.asarray(jaw.points) + np.asarray(translation)
    margin_path = next(path for path in folder.glob("*-margin.xyz") if path.is_file())
    try:
        margin_points = np.loadtxt(margin_path, ndmin=2)
        if margin_points.shape[1] < 3 or not np.all(np.isfinite(margin_points[:, :3])):
            raise ValueError("margin file must contain finite XYZ coordinates")
        reference = pv.read(folder / "gt.stl")
        center, normal = fit_margin_plane(margin_points[:, :3], np.asarray(reference.points))
        center = center + np.asarray(translation)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    for stem in ("gt", "our", "ablation_match"):
        if not (folder / f"{stem}.stl").is_file():
            continue
        crown = pv.read(folder / f"{stem}.stl")
        crown.points = np.asarray(crown.points) + np.asarray(translation)
        crown["surface_distance"] = crown_heatmap_values(
            crown, jaw, center, normal, args.bottom_height, args.clim)
        for reverse_view in (False, True):
            plotter = pv.Plotter(off_screen=True, window_size=(900, 700))
            plotter.set_background("white")
            # Reversed jet maps zero distance to red and the limit to blue.
            plotter.add_mesh(crown, scalars="surface_distance", cmap="jet_r",
                             clim=(0.0, args.clim), smooth_shading=True,
                             nan_color="white", nan_opacity=1.0,
                             show_scalar_bar=False)
            if view:
                position = np.asarray(view["position"], dtype=float)
                focal_point = np.asarray(view["focal_point"], dtype=float)
                if reverse_view:
                    position = 2.0 * focal_point - position
                plotter.camera.position = position
                plotter.camera.focal_point = focal_point
                plotter.camera.up = view["viewup"]
                plotter.camera.parallel_scale = parallel_scale
                plotter.camera.parallel_projection = True
                if "view_angle" in view:
                    plotter.camera.view_angle = view["view_angle"]
                # The saved clipping range may not fit the reversed view.
                plotter.reset_camera_clipping_range()
            suffix = "_heatmap2.png" if reverse_view else "_heatmap.png"
            output = args.output if args.output and stem == "gt" and not reverse_view else folder / f"{stem}{suffix}"
            plotter.show(screenshot=str(output), auto_close=True)
            print(output)


if __name__ == "__main__":
    main()
