#!/usr/bin/env python3
"""Inspect principal mesh axes, scale along one axis, or deform a local region.

Examples:
    # 查看最长、最短方向及长度
    python mesh_deform.py info case/gt.stl
    # 沿最长方向放大 10%
    python mesh_deform.py scale case/gt.stl --axis longest --factor 1.1
    # 沿同时垂直于长轴和短轴的第三轴缩放
    python mesh_deform.py scale case/gt.stl --axis perpendicular --factor 1.1
    # 局部平移：中心为 (0, 0, 5)、半径为 2，沿 X 方向移动：
    python mesh_deform.py local case/gt.stl --center 0 0 5 --radius 2 --offset 0.5 0 0
    局部缩放：
    python mesh_deform.py local case/gt.stl --center 0 0 5 --radius 2 --factor 1.2

All coordinates, radii and offsets use the mesh's original coordinate units.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv


def _points(mesh: pv.PolyData) -> np.ndarray:
    if not isinstance(mesh, pv.PolyData) or mesh.n_points < 3:
        raise ValueError("input must be a surface mesh with at least three vertices")
    points = np.asarray(mesh.points, dtype=float)
    if not np.all(np.isfinite(points)):
        raise ValueError("mesh coordinates must be finite")
    return points


def principal_axes(mesh: pv.PolyData) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return oriented-box center, PCA axes (rows), and descending spans.

Axes are PCA directions, ordered by actual projected extent rather than
variance. This is an approximate oriented bounding box, not a minimum box.
Repeated STL vertices are ignored while fitting the axes.
"""
    points = np.unique(_points(mesh), axis=0)
    if len(points) < 3:
        raise ValueError("mesh must contain at least three distinct vertices")
    origin = points.mean(axis=0)
    _, _, axes = np.linalg.svd(points - origin, full_matrices=False)
    # Choose a deterministic sign for reporting; scaling is sign independent.
    for axis in axes:
        if axis[np.argmax(np.abs(axis))] < 0:
            axis *= -1
    projected = (points - origin) @ axes.T
    lower, upper = projected.min(axis=0), projected.max(axis=0)
    spans = upper - lower
    center = origin + ((lower + upper) / 2) @ axes
    order = np.argsort(-spans, kind="stable")
    return center, axes[order], spans[order]


def _positive(value: float, name: str) -> None:
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")


def _vector(value: np.ndarray, name: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain three finite coordinates")
    return vector


def _with_points(mesh: pv.PolyData, points: np.ndarray) -> pv.PolyData:
    result = mesh.copy(deep=True)
    result.points = points
    # Stored normals no longer describe the deformed geometry.
    for attributes in (result.point_data, result.cell_data):
        if "Normals" in attributes:
            del attributes["Normals"]
    return result


def scale_axis(mesh: pv.PolyData, axis: str, factor: float,
               center: np.ndarray | None = None) -> pv.PolyData:
    """Scale coordinates along a PCA axis while retaining transverse distances."""
    _positive(factor, "factor")
    if axis not in {"longest", "middle", "shortest", "perpendicular"}:
        raise ValueError("axis must be longest, middle, shortest or perpendicular")
    default_center, axes, spans = principal_axes(mesh)
    index = {"longest": 0, "middle": 1, "shortest": 2, "perpendicular": 1}[axis]
    if spans[index] <= np.finfo(float).eps * max(1.0, spans[0]):
        raise ValueError(f"the {axis} direction has zero extent and cannot be scaled")
    pivot = default_center if center is None else _vector(center, "center")
    points = _points(mesh)
    direction = perpendicular_axis(axes) if axis == "perpendicular" else axes[index]
    displacement = ((points - pivot) @ direction)[:, None] * direction
    return _with_points(mesh, points + (factor - 1) * displacement)


def perpendicular_axis(axes: np.ndarray) -> np.ndarray:
    """Return the unit cross product of the longest and shortest PCA axes."""
    direction = np.cross(axes[0], axes[2])
    direction /= np.linalg.norm(direction)
    if np.dot(direction, axes[1]) < 0:
        direction = -direction
    return direction


def scale_perpendicular(mesh: pv.PolyData, factor: float,
                        center: np.ndarray | None = None) -> pv.PolyData:
    """Scale along the direction perpendicular to both long and short axes."""
    return scale_axis(mesh, "perpendicular", factor, center)


def deform_local(mesh: pv.PolyData, center: np.ndarray, radius: float,
                 offset: np.ndarray | None = None,
                 factor: float | None = None) -> pv.PolyData:
    """Smoothly translate or radially scale a spherical region.

Weight w=1-3t^2+2t^3, t=clip(distance/radius, 0, 1).
Vertices outside the sphere stay exactly fixed. Connectivity is retained.
"""
    center = _vector(center, "center")
    _positive(radius, "radius")
    if (offset is None) == (factor is None):
        raise ValueError("specify exactly one of offset or factor")
    points = _points(mesh)
    relative = points - center
    t = np.clip(np.linalg.norm(relative, axis=1) / radius, 0, 1)
    weights = 1 - 3 * t**2 + 2 * t**3
    if offset is not None:
        displacement = np.broadcast_to(_vector(offset, "offset"), points.shape)
    else:
        _positive(factor, "factor")
        displacement = (factor - 1) * relative
    return _with_points(mesh, points + weights[:, None] * displacement)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("info", "scale", "local"):
        command = commands.add_parser(name)
        command.add_argument("input", type=Path, help="input surface mesh, e.g. STL/PLY/VTP")
        if name != "info":
            command.add_argument("-o", "--output", type=Path,
                                 help="default: <input_stem>_<command><input_suffix>")
        if name == "scale":
            command.add_argument("--axis", choices=("longest", "middle", "shortest", "perpendicular"), default="longest",
                                 help="perpendicular is the cross product of longest and shortest (same axis as middle)")
            command.add_argument("--factor", type=float, required=True)
            command.add_argument("--center", nargs=3, type=float, help="optional scaling pivot X Y Z")
        if name == "local":
            command.add_argument("--center", nargs=3, type=float, required=True)
            command.add_argument("--radius", type=float, required=True)
            mode = command.add_mutually_exclusive_group(required=True)
            mode.add_argument("--offset", nargs=3, type=float, help="local translation DX DY DZ")
            mode.add_argument("--factor", type=float, help="local radial scale factor")
    args = parser.parse_args()
    input_path = args.input.expanduser().resolve()
    try:
        mesh = pv.read(input_path)
        center, axes, spans = principal_axes(mesh)
        print("Principal bounding-box center:", center.tolist())
        for label, direction, span in zip(("longest", "middle", "shortest"), axes, spans):
            print(f"{label}: direction={direction.tolist()}, span={span:.6g}")
        print("perpendicular (same axis as middle):", perpendicular_axis(axes).tolist())
        if args.command == "info":
            return
        if args.command == "scale":
            result = scale_axis(mesh, args.axis, args.factor, args.center)
        else:
            result = deform_local(mesh, args.center, args.radius, args.offset, args.factor)
        output = (args.output.expanduser().resolve() if args.output else
                  input_path.with_name(f"{input_path.stem}_{args.command}{input_path.suffix}"))
        if output == input_path:
            raise ValueError("output must differ from input to preserve the source mesh")
        output.parent.mkdir(parents=True, exist_ok=True)
        result.save(output)
        moved = np.count_nonzero(np.linalg.norm(result.points - mesh.points, axis=1) > 0)
        print(f"saved {output} ({moved}/{mesh.n_points} vertices moved)")
    except (ValueError, OSError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
