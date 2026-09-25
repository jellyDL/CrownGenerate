#!/usr/bin/env python3
"""Interactive STL viewer and rigid-pose editor.

Example usage:
python step1_stl_pose_editor.py 26-preparation.stl

Keys: arrows/WASD translate in X/Y, Q/E translate in Z; I/K rotate X,
J/L rotate Y, U/O rotate Z; pinch or two-finger scroll: zoom; R reset; P save; Esc quit.
The saved pose is a 4x4 row-major homogeneous matrix in JSON and TXT.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pyvista as pv


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stl", type=Path, help="input STL file or folder containing gt.stl")
    ap.add_argument("-o", "--output", type=Path, help="pose stem (default: input stem_rt)")
    ap.add_argument("--step", type=float, default=0.5, help="translation step in mesh units")
    ap.add_argument("--angle", type=float, default=2.0, help="rotation step in degrees")
    args = ap.parse_args()
    input_dir = args.stl if args.stl.is_dir() else args.stl.parent
    if args.stl.is_dir():
        args.stl = args.stl / "gt.stl"
    if not args.stl.is_file():
        ap.error(f"STL not found: {args.stl}")
    stem = args.output or args.stl.with_name(args.stl.stem + "_singlejaw_rt")
    crown_mesh = pv.read(args.stl)
    crown_mesh["display_rgb"] = np.tile([199, 146, 88], (crown_mesh.n_points, 1)).astype(np.uint8)
    # Build one combined actor so mouse interaction and the saved transform
    # apply to the upper jaw, lower jaw, and crown as a single rigid object.
    jaw_paths = []
    parts = []
    for name in ("upperjaw.ply", "lowerjaw.ply", "upperjaw.stl", "lowerjaw.stl"):
        candidate = input_dir / name
        if candidate.is_file():
            jaw_paths.append(candidate)
    # Show only the jaw containing/nearest to the crown.  This keeps the
    # editor focused on the relevant single-jaw context when both jaws are
    # present in the input folder.
    if len(jaw_paths) > 1:
        crown_center = np.asarray(crown_mesh.points).mean(axis=0)
        def bbox_distance(path: Path) -> float:
            jaw_points = np.asarray(pv.read(path).points)
            lower, upper = jaw_points.min(axis=0), jaw_points.max(axis=0)
            delta = np.maximum(np.maximum(lower - crown_center, 0), crown_center - upper)
            return float(np.linalg.norm(delta))
        jaw_paths = [min(jaw_paths, key=bbox_distance)]
    for jaw_path in jaw_paths:
        jaw_mesh = pv.read(jaw_path)
        jaw_mesh["display_rgb"] = np.tile([167, 167, 167], (jaw_mesh.n_points, 1)).astype(np.uint8)
        parts.append(jaw_mesh)
    parts.append(crown_mesh)
    mesh = pv.merge(parts, merge_points=False)
    original = np.asarray(mesh.points).copy()
    pose = np.eye(4)
    plotter = pv.Plotter(window_size=(600, 800))
    plotter.set_background('#f4f7f4')
    actor = plotter.add_mesh(mesh, scalars="display_rgb", rgb=True,
                             smooth_shading=True, show_edges=False)
    plotter.enable_trackball_actor_style()
    # VTK exposes trackpad pinch as PinchEvent; apply its scale to the camera.
    interactor = plotter.iren.interactor
    pinch_scale = [1.0]
    def on_pinch_start(obj, event):
        pinch_scale[0] = float(obj.GetScale())
    def on_pinch(obj, event):
        scale = float(obj.GetScale())
        if scale > 0 and pinch_scale[0] > 0:
            plotter.camera.zoom(scale / pinch_scale[0])
            pinch_scale[0] = scale
            plotter.render()
    interactor.AddObserver("StartPinchEvent", on_pinch_start)
    interactor.AddObserver("PinchEvent", on_pinch)
    # macOS trackpads commonly expose two-finger gestures as wheel events.
    def on_wheel_forward(obj, event):
        plotter.camera.zoom(1.12); plotter.render()
    def on_wheel_backward(obj, event):
        plotter.camera.zoom(1 / 1.12); plotter.render()
    interactor.AddObserver("MouseWheelForwardEvent", on_wheel_forward)
    interactor.AddObserver("MouseWheelBackwardEvent", on_wheel_backward)
    plotter.add_axes()
    plotter.add_text(
        "Mouse: select/drag/rotate | Two-finger pinch/scroll: zoom | Arrows/WASD: XY | Q/E: Z | I/K/J/L/U/O: rotate | R reset | P save",
        position="upper_left", font_size=10,
    )

    def redraw() -> None:
        mesh.points = (original @ pose[:3, :3].T) + pose[:3, 3]
        plotter.render()

    def move(dx: float = 0, dy: float = 0, dz: float = 0) -> None:
        nonlocal pose
        delta = np.eye(4); delta[:3, 3] = [dx, dy, dz]
        pose = delta @ pose; redraw()

    def rotate(axis: str, degrees: float) -> None:
        nonlocal pose
        t = np.deg2rad(degrees); c, s = np.cos(t), np.sin(t)
        r = np.eye(4)
        if axis == "x": r[:3, :3] = [[1, 0, 0], [0, c, -s], [0, s, c]]
        if axis == "y": r[:3, :3] = [[c, 0, s], [0, 1, 0], [-s, 0, c]]
        if axis == "z": r[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
        pose = r @ pose; redraw()

    def current_pose() -> np.ndarray:
        # Trackball interaction updates the actor's computed matrix, not
        # necessarily its user matrix.  GetMatrix() therefore captures the
        # actual mouse rotation and its pivot translation.
        matrix = actor.GetMatrix()
        actor_pose = np.array(
            [[matrix.GetElement(i, j) for j in range(4)] for i in range(4)],
            dtype=float,
        )
        return actor_pose @ pose

    def save() -> None:
        matrix = current_pose()
        camera = plotter.camera
        payload = {
            "source": str(args.stl.resolve()),
            "transform": matrix.tolist(),
            "convention": "p' = R p + t",
            # Preserve the final editor view so the offline renderer can
            # reproduce the same framing and orientation.
            "camera": {
                "position": list(camera.position),
                "focal_point": list(camera.focal_point),
                "viewup": list(camera.up),
                "parallel_scale": float(camera.parallel_scale),
                "parallel_projection": bool(camera.parallel_projection),
                "view_angle": float(camera.view_angle),
                "clipping_range": list(camera.clipping_range),
            },
        }
        stem.parent.mkdir(parents=True, exist_ok=True)
        stem.with_suffix(".json").write_text(json.dumps(payload, indent=2) + "\n")
        print(f"saved {stem.with_suffix('.json')}")

    plotter.add_key_event("Left", lambda: move(dx=-args.step)); plotter.add_key_event("Right", lambda: move(dx=args.step))
    plotter.add_key_event("Up", lambda: move(dy=args.step)); plotter.add_key_event("Down", lambda: move(dy=-args.step))
    plotter.add_key_event("a", lambda: move(dx=-args.step)); plotter.add_key_event("d", lambda: move(dx=args.step))
    plotter.add_key_event("w", lambda: move(dy=args.step)); plotter.add_key_event("s", lambda: move(dy=-args.step))
    for key, dz in (("q", args.step), ("e", -args.step)): plotter.add_key_event(key, lambda dz=dz: move(dz=dz))
    for key, axis, sign in (("i", "x", 1), ("k", "x", -1), ("j", "y", 1), ("l", "y", -1), ("u", "z", 1), ("o", "z", -1)):
        plotter.add_key_event(key, lambda axis=axis, sign=sign: rotate(axis, sign * args.angle))
    plotter.add_key_event("r", lambda: (pose.__setitem__((slice(None), slice(None)), np.eye(4)), redraw()))
    plotter.add_key_event("p", save)
    plotter.show()


if __name__ == "__main__":
    main()
