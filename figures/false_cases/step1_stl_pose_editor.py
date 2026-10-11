#!/usr/bin/env python3
"""Interactive STL viewer and rigid-pose editor.

Example usage:
python3 step1_stl_pose_editor.py <folder path>

Keys: arrows/WASD translate in X/Y, Q/E translate in Z; I/K rotate X,
J/L rotate Y, U/O rotate Z; pinch or two-finger scroll: zoom; R reset; P save; Esc quit.
The saved pose is a 4x4 row-major homogeneous matrix in JSON and TXT.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pyvista as pv


def resolve_jaw(folder: Path) -> tuple[int, Path]:
    """Select the arch from the FDI prefix of a unique margin file."""
    margins = sorted(folder.glob("*-margin.xyz"))
    if len(margins) != 1:
        raise ValueError(f"Expected one *-margin.xyz in {folder}, found {len(margins)}")
    match = re.fullmatch(r"([1-4][1-8]|[5-8][1-5])-margin\.xyz", margins[0].name)
    if match is None:
        raise ValueError(f"Invalid FDI margin filename: {margins[0].name}")
    fdi = int(match.group(1))
    jaw_name = "upperjaw" if fdi // 10 in (1, 2, 5, 6) else "lowerjaw"
    for suffix in (".ply", ".stl"):
        path = folder / (jaw_name + suffix)
        if path.is_file():
            return fdi, path
    raise ValueError(f"Missing {jaw_name}.ply or {jaw_name}.stl in {folder}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stl", type=Path, help="input STL file or folder containing gt.stl")
    ap.add_argument("-o", "--output", type=Path, help="pose stem (default: input stem_rt)")
    ap.add_argument("--step", type=float, default=0.5, help="translation step in mesh units")
    ap.add_argument("--angle", type=float, default=2.0, help="rotation step in degrees")
    args = ap.parse_args()
    if args.stl.is_dir():
        args.stl = args.stl / "gt.stl"
    if not args.stl.is_file():
        ap.error(f"STL not found: {args.stl}")
    stem = args.output or args.stl.with_name(args.stl.stem + "_rt")
    try:
        fdi, jaw_path = resolve_jaw(args.stl.parent)
    except ValueError as exc:
        ap.error(str(exc))
    # A single actor keeps the crown and its arch aligned during pose editing.
    mesh = pv.merge([pv.read(jaw_path), pv.read(args.stl)], merge_points=False)
    print(f"FDI {fdi}: displaying {jaw_path.name} with {args.stl.name}")
    original = np.asarray(mesh.points).copy()
    pose = np.eye(4)
    # Match step2_render_stl_rt.py so a saved camera produces the same frame.
    plotter = pv.Plotter(window_size=(900, 900))
    actor = plotter.add_mesh(mesh, color="#c79258", smooth_shading=True, show_edges=False)
    # VTK's trackball-actor style lets the user select the mesh and drag/rotate it.
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
        matrix = actor.GetUserMatrix()
        if matrix is None:
            return pose.copy()
        actor_matrix = np.array(
            [[matrix.GetElement(i, j) for j in range(4)] for i in range(4)],
            dtype=float,
        )
        # Keyboard edits are applied to mesh.points, while trackball edits
        # are stored on the actor.  The saved transform must include both.
        return actor_matrix @ pose

    def save_rt(filename: str, scope: str) -> None:
        if scope == "all":
            # The all-mesh view is saved as an orthographic projection so the
            # jaw and crown can be compared without perspective distortion.
            saved_position = tuple(plotter.camera.position)
            saved_focal = tuple(plotter.camera.focal_point)
            saved_up = tuple(plotter.camera.up)
            was_parallel = bool(plotter.camera.parallel_projection)
            if was_parallel:
                saved_scale = float(plotter.camera.parallel_scale)
            else:
                # Convert the current perspective framing to an equivalent
                # orthographic half-height for the square 900x900 viewport.
                distance = float(np.linalg.norm(np.asarray(saved_position) - np.asarray(saved_focal)))
                view_angle = np.deg2rad(float(plotter.camera.view_angle))
                saved_scale = distance * np.tan(view_angle / 2.0)
            plotter.camera.parallel_projection = True
            # VTK may reset the camera while changing projection type.
            plotter.camera_position = (saved_position, saved_focal, saved_up)
            plotter.camera.parallel_scale = saved_scale
            plotter.render()
        matrix = current_pose()
        payload = {
            "source": str(args.stl.resolve()),
            "jaw_source": str(jaw_path.resolve()),
            "fdi": fdi,
            "scope": scope,
            "transform": matrix.tolist(),
            "camera": {
                "position": list(plotter.camera.position),
                "focal_point": list(plotter.camera.focal_point),
                "view_up": list(plotter.camera.up),
                "parallel_scale": float(plotter.camera.parallel_scale),
                "parallel_projection": bool(plotter.camera.parallel_projection),
            },
            "convention": "p' = R p + t",
        }
        output = args.stl.parent / filename
        output.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"saved {output}")

    plotter.add_key_event("Left", lambda: move(dx=-args.step)); plotter.add_key_event("Right", lambda: move(dx=args.step))
    plotter.add_key_event("Up", lambda: move(dy=args.step)); plotter.add_key_event("Down", lambda: move(dy=-args.step))
    plotter.add_key_event("a", lambda: move(dx=-args.step)); plotter.add_key_event("d", lambda: move(dx=args.step))
    plotter.add_key_event("w", lambda: move(dy=args.step)); plotter.add_key_event("s", lambda: move(dy=-args.step))
    for key, dz in (("q", args.step), ("e", -args.step)): plotter.add_key_event(key, lambda dz=dz: move(dz=dz))
    for key, axis, sign in (("i", "x", 1), ("k", "x", -1), ("j", "y", 1), ("l", "y", -1), ("u", "z", 1), ("o", "z", -1)):
        plotter.add_key_event(key, lambda axis=axis, sign=sign: rotate(axis, sign * args.angle))
    plotter.add_key_event("r", lambda: (pose.__setitem__((slice(None), slice(None)), np.eye(4)), redraw()))
    plotter.add_key_event("P", lambda: save_rt("single_rt.json", "single"))
    plotter.add_key_event("O", lambda: save_rt("all_rt.json", "all"))
    plotter.show()


if __name__ == "__main__":
    main()
