#!/usr/bin/env python3
"""Render replaceable dental assets for the method framework figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import numpy as np
import open3d as o3d
from PIL import Image, ImageDraw, ImageFont

mpl.use("Agg")
import matplotlib.pyplot as plt


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "assets" / "method_framework"


def _mesh(path: Path, target_triangles: int) -> o3d.geometry.TriangleMesh:
    mesh = o3d.io.read_triangle_mesh(str(path), enable_post_processing=False)
    if mesh.is_empty() or not mesh.has_triangles():
        raise ValueError(f"No triangle mesh found in {path}")
    mesh.remove_duplicated_vertices()
    mesh.remove_degenerate_triangles()
    mesh.remove_unreferenced_vertices()
    if len(mesh.triangles) > target_triangles:
        simplified = mesh.simplify_quadric_decimation(target_triangles)
        if not simplified.is_empty() and simplified.has_triangles():
            mesh = simplified
    mesh.compute_vertex_normals()
    return mesh


def _local_axes(
    upper: o3d.geometry.TriangleMesh,
    lower: o3d.geometry.TriangleMesh,
    margin: np.ndarray,
    fdi: int,
) -> tuple[np.ndarray, np.ndarray]:
    origin = margin.mean(axis=0)
    _, _, vh = np.linalg.svd(margin - origin, full_matrices=False)
    z_axis = vh[-1]

    upper_vertices = np.asarray(upper.vertices, dtype=np.float64)
    lower_vertices = np.asarray(lower.vertices, dtype=np.float64)
    target = upper_vertices if fdi // 10 in (1, 2) else lower_vertices
    opposing = lower_vertices if fdi // 10 in (1, 2) else upper_vertices

    distances = np.linalg.norm(opposing - origin, axis=1)
    count = min(4096, len(opposing))
    nearest = opposing[np.argpartition(distances, count - 1)[:count]].mean(axis=0)
    if np.dot(z_axis, nearest - origin) < 0:
        z_axis = -z_axis

    radial = origin - np.median(target, axis=0)
    radial -= np.dot(radial, z_axis) * z_axis
    if np.linalg.norm(radial) < 1e-8:
        radial = vh[0] - np.dot(vh[0], z_axis) * z_axis
    y_axis = radial / np.linalg.norm(radial)
    x_axis = np.cross(y_axis, z_axis)
    x_axis /= np.linalg.norm(x_axis)
    y_axis = np.cross(z_axis, x_axis)
    y_axis /= np.linalg.norm(y_axis)
    return origin, np.column_stack((x_axis, y_axis, z_axis))


def _arrays(
    mesh: o3d.geometry.TriangleMesh,
    origin: np.ndarray,
    axes: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    vertices = (np.asarray(mesh.vertices, dtype=np.float64) - origin) @ axes
    triangles = np.asarray(mesh.triangles, dtype=np.int64)
    return vertices, triangles


def _configure_axes(ax, vertices: np.ndarray, elev: float, azim: float) -> None:
    bounds_min = vertices.min(axis=0)
    bounds_max = vertices.max(axis=0)
    center = (bounds_min + bounds_max) / 2.0
    radius = max(float(np.max(bounds_max - bounds_min)) * 0.55, 1.0)
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)
    if hasattr(ax, "set_box_aspect"):
        ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    if hasattr(ax, "set_proj_type"):
        ax.set_proj_type("ortho")
    ax.set_axis_off()
    ax.patch.set_alpha(0)


def _plot_surface(
    ax,
    vertices: np.ndarray,
    triangles: np.ndarray,
    color: str,
    alpha: float = 1.0,
    *,
    mesh_edges: bool = False,
    edge_color: str = "#315F77",
    edge_width: float = 0.12,
) -> None:
    ax.plot_trisurf(
        vertices[:, 0],
        vertices[:, 1],
        vertices[:, 2],
        triangles=triangles,
        color=color,
        edgecolor=edge_color if mesh_edges else "none",
        linewidth=edge_width if mesh_edges else 0,
        antialiased=True,
        shade=True,
        alpha=alpha,
    )


def _tight_square(path: Path, size: int, pad_fraction: float = 0.06) -> None:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError(f"Rendered image is empty: {path}")
    cropped = image.crop(bbox)
    side = int(max(cropped.size) * (1.0 + 2.0 * pad_fraction))
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    canvas.alpha_composite(
        cropped,
        ((side - cropped.width) // 2, (side - cropped.height) // 2),
    )
    canvas.resize((size, size), Image.Resampling.LANCZOS).save(path)


def _render_surface(
    path: Path,
    vertices: np.ndarray,
    triangles: np.ndarray,
    color: str,
    size: int,
    elev: float,
    azim: float,
    *,
    mesh_edges: bool = False,
) -> None:
    dpi = 200
    fig = plt.figure(figsize=(size / dpi, size / dpi), dpi=dpi)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1), projection="3d")
    _plot_surface(ax, vertices, triangles, color, mesh_edges=mesh_edges)
    visible = vertices[np.unique(triangles)]
    _configure_axes(ax, visible, elev, azim)
    fig.savefig(path, transparent=True, dpi=dpi, pad_inches=0)
    plt.close(fig)
    _tight_square(path, size)


def _render_margin_curve(path: Path, margin: np.ndarray, size: int) -> None:
    """Render the measured margin as a standalone 3D spatial curve."""
    dpi = 200
    fig = plt.figure(figsize=(size / dpi, size / dpi), dpi=dpi)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1), projection="3d")
    closed = np.vstack((margin, margin[:1]))
    xy_span = max(float(np.ptp(margin[:, 0])), float(np.ptp(margin[:, 1])), 1.0)
    projection_z = float(margin[:, 2].min() - 0.15 * xy_span)
    projected = closed.copy()
    projected[:, 2] = projection_z
    ax.plot(
        projected[:, 0],
        projected[:, 1],
        projected[:, 2],
        color="#9AA7AF",
        linewidth=0.9,
        linestyle=(0, (3, 2)),
        alpha=0.34,
        zorder=4,
    )
    ax.plot(
        closed[:, 0],
        closed[:, 1],
        closed[:, 2],
        color="#A84138",
        linewidth=6.4,
        solid_capstyle="round",
        zorder=18,
    )
    ax.plot(
        closed[:, 0],
        closed[:, 1],
        closed[:, 2],
        color="#E66B5D",
        linewidth=4.2,
        solid_capstyle="round",
        zorder=20,
    )
    stride = max(1, len(margin) // 6)
    samples = margin[::stride]
    for point in samples:
        ax.plot(
            [point[0], point[0]],
            [point[1], point[1]],
            [projection_z, point[2]],
            color="#AAB4BA",
            linewidth=0.75,
            alpha=0.36,
            zorder=5,
        )
    ax.scatter(
        samples[:, 0],
        samples[:, 1],
        samples[:, 2],
        s=12,
        color="#F4A096",
        edgecolors="#9E3E36",
        linewidths=0.45,
        depthshade=True,
        zorder=22,
    )
    _configure_axes(ax, np.vstack((closed, projected)), 22, -55)
    fig.savefig(path, transparent=True, dpi=dpi, pad_inches=0)
    plt.close(fig)
    _tight_square(path, size, pad_fraction=0.12)


def _render_scan_pair(
    path: Path,
    upper_vertices: np.ndarray,
    upper_faces: np.ndarray,
    lower_vertices: np.ndarray,
    lower_faces: np.ndarray,
    size: int,
) -> None:
    """Render registered upper and lower scans in static occlusion."""
    dpi = 200
    fig = plt.figure(figsize=(size / dpi, size / dpi), dpi=dpi)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1), projection="3d")
    # A shared presentation-only roll levels the lateral occlusal band. Both
    # arches receive the same rigid transform, preserving their registration.
    side_roll = np.deg2rad(6.0)
    cos_roll, sin_roll = np.cos(side_roll), np.sin(side_roll)
    rotation = np.array(
        [
            [cos_roll, 0.0, sin_roll],
            [0.0, 1.0, 0.0],
            [-sin_roll, 0.0, cos_roll],
        ]
    )
    upper_display = upper_vertices @ rotation.T
    lower_display = lower_vertices @ rotation.T

    # Soft, staggered translucency keeps the paired scans distinguishable
    # while allowing their opposing anatomy to remain visible.
    _plot_surface(ax, upper_display, upper_faces, "#B8C3C8", alpha=0.60)
    _plot_surface(ax, lower_display, lower_faces, "#76A48C", alpha=0.72)
    visible = np.vstack(
        (
            upper_display[np.unique(upper_faces)],
            lower_display[np.unique(lower_faces)],
        )
    )
    _configure_axes(ax, visible, elev=0, azim=-90)
    fig.savefig(path, transparent=True, dpi=dpi, pad_inches=0)
    plt.close(fig)
    _tight_square(path, size, pad_fraction=0.045)


def _placeholder_badge(path: Path, label: str) -> None:
    image = Image.open(path).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    font_size = max(28, image.width // 20)
    try:
        font_path = Path(mpl.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
        font = ImageFont.truetype(str(font_path), font_size)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), label, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = (image.width - width) // 2
    y = image.height - height - image.height // 18
    pad_x = max(14, image.width // 50)
    pad_y = max(9, image.height // 110)
    draw.rounded_rectangle(
        (x - pad_x, y - pad_y, x + width + pad_x, y + height + pad_y),
        radius=pad_y,
        fill=(255, 255, 255, 225),
        outline=(91, 105, 114, 185),
        width=max(1, image.width // 500),
    )
    draw.text((x, y), label, fill=(69, 82, 91, 235), font=font)
    image.save(path)


def render_assets(case_dir: Path, fdi: int, output_dir: Path, size: int) -> None:
    paths = {
        "upper": case_dir / "upperjaw.ply",
        "lower": case_dir / "lowerjaw.ply",
        "margin": case_dir / f"{fdi}-margin.xyz",
        "crown": case_dir / f"{fdi}-waxup.stl",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing case files: " + ", ".join(missing))

    output_dir.mkdir(parents=True, exist_ok=True)
    upper = _mesh(paths["upper"], 24_000)
    lower = _mesh(paths["lower"], 24_000)
    crown = _mesh(paths["crown"], 8_000)
    margin = np.loadtxt(paths["margin"], dtype=np.float64)[:, :3]
    origin, axes = _local_axes(upper, lower, margin, fdi)

    upper_vertices, upper_faces = _arrays(upper, origin, axes)
    lower_vertices, lower_faces = _arrays(lower, origin, axes)
    crown_vertices, crown_faces = _arrays(crown, origin, axes)
    margin_local = (margin - origin) @ axes
    _render_scan_pair(
        output_dir / "scans.png",
        upper_vertices,
        upper_faces,
        lower_vertices,
        lower_faces,
        size,
    )
    _render_margin_curve(
        output_dir / "margin.png",
        margin_local,
        size,
    )
    _render_surface(
        output_dir / "reference_cad.png",
        crown_vertices,
        crown_faces,
        "#D7AA77",
        size,
        38,
        -54,
    )
    for filename, color, elev, azim, label in (
        (
            "reconstructed_mesh.png",
            "#A2BBC7",
            43,
            -43,
            "VAE PLACEHOLDER",
        ),
        ("crown_mesh.png", "#72A6C0", 34, -64, "GEN PLACEHOLDER"),
    ):
        path = output_dir / filename
        _render_surface(
            path,
            crown_vertices,
            crown_faces,
            color,
            size,
            elev,
            azim,
            mesh_edges=filename == "crown_mesh.png",
        )
        _placeholder_badge(path, label)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--fdi", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--size", type=int, default=1200)
    args = parser.parse_args()
    if args.size < 512:
        raise ValueError("--size must be at least 512 pixels")
    render_assets(args.case_dir.expanduser(), args.fdi, args.output_dir, args.size)


if __name__ == "__main__":
    main()
