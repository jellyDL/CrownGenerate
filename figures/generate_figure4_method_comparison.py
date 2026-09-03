#!/usr/bin/env python3
"""Render Figure 4 from a manifest of same-case crown meshes.

The renderer deliberately keeps the reference-defined camera and bounds fixed
across methods. It can also create a clearly watermarked layout template when
genuine baseline and proposed-model outputs are not yet available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d


ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE_BASE = ROOT / "figure4_method_comparison_template"
METHODS: Sequence[Tuple[str, str]] = (
    ("reference_cad", "Reference CAD"),
    ("fdi_nearest_neighbor", "FDI-NN"),
    ("madcrowner", "MADCrowner"),
    ("vbcd", "VBCD"),
    ("dcrownformer_plus", "DCrownFormer+"),
    ("ours", "Proposed"),
)

COLORS = {
    "ink": "#24313C",
    "muted": "#687681",
    "line": "#D5DEE4",
    "panel": "#FBFCFD",
    "slot": "#F4F7F9",
    "accent": "#0F4D92",
    "reference": "#9A7043",
    "warning": "#A96824",
    "mesh": "#CBB28F",
    "mesh_edge": "#8F775A",
    "white": "#FFFFFF",
}

mpl.rcParams.update(
    {
        "font.family": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 6.5,
        "text.color": COLORS["ink"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "figure.facecolor": COLORS["white"],
        "savefig.facecolor": COLORS["white"],
    }
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_mesh(path: Path, max_triangles: int) -> Tuple[np.ndarray, np.ndarray]:
    mesh = o3d.io.read_triangle_mesh(str(path), enable_post_processing=False)
    if mesh.is_empty() or not mesh.has_triangles():
        raise ValueError("No triangle mesh found in {}".format(path))
    if max_triangles > 0 and len(mesh.triangles) > max_triangles:
        simplified = mesh.simplify_quadric_decimation(max_triangles)
        if not simplified.is_empty() and simplified.has_triangles():
            mesh = simplified
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    faces = np.asarray(mesh.triangles, dtype=np.int64)
    if len(vertices) == 0 or len(faces) == 0:
        raise ValueError("Empty mesh after display preparation: {}".format(path))
    return vertices, faces


def _resolve_path(manifest_path: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (manifest_path.parent / path).resolve()


def _reference_bounds(vertices: np.ndarray) -> np.ndarray:
    lower = vertices.min(axis=0)
    upper = vertices.max(axis=0)
    span = np.maximum(upper - lower, 1.0)
    return np.column_stack((lower - 0.06 * span, upper + 0.06 * span))


def _parse_bounds(value: object, fallback: np.ndarray, label: str) -> np.ndarray:
    if value is None or value == "reference":
        return fallback.copy()
    bounds = np.asarray(value, dtype=np.float64)
    if bounds.shape != (3, 2):
        raise ValueError("{} bounds must have shape [3, 2]".format(label))
    if np.any(bounds[:, 1] <= bounds[:, 0]):
        raise ValueError("{} bounds must increase along every axis".format(label))
    return bounds


def _configure_axes(ax, bounds: np.ndarray, elev: float, azim: float) -> None:
    ax.set_xlim(bounds[0, 0], bounds[0, 1])
    ax.set_ylim(bounds[1, 0], bounds[1, 1])
    ax.set_zlim(bounds[2, 0], bounds[2, 1])
    if hasattr(ax, "set_box_aspect"):
        ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    if hasattr(ax, "set_proj_type"):
        ax.set_proj_type("ortho")
    ax.set_axis_off()
    ax.patch.set_alpha(0.0)


def _draw_mesh(ax, vertices: np.ndarray, faces: np.ndarray) -> None:
    ax.plot_trisurf(
        vertices[:, 0],
        vertices[:, 1],
        vertices[:, 2],
        triangles=faces,
        color=COLORS["mesh"],
        edgecolor="none",
        linewidth=0.0,
        antialiased=True,
        shade=True,
    )


def _placeholder(ax, detail: bool) -> None:
    ax.set_facecolor(COLORS["slot"])
    ax.text2D(
        0.5,
        0.57,
        "OUTPUT\nREQUIRED",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=7.0,
        fontweight="semibold",
        color=COLORS["warning"],
        linespacing=1.05,
    )
    ax.text2D(
        0.5,
        0.30,
        "reference-defined ROI" if detail else "same-case mesh",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=4.9,
        color=COLORS["muted"],
    )
    if detail:
        rectangle = mpl.patches.Rectangle(
            (0.23, 0.20),
            0.54,
            0.54,
            transform=ax.transAxes,
            fill=False,
            edgecolor=COLORS["muted"],
            linewidth=0.7,
            linestyle=(0, (2.0, 1.8)),
        )
        ax.add_artist(rectangle)


def _case_meshes(
    case: Mapping[str, object], manifest_path: Path, max_triangles: int, allow_missing: bool
) -> Tuple[Dict[str, Optional[Tuple[np.ndarray, np.ndarray]]], Dict[str, Optional[str]], np.ndarray]:
    paths: Dict[str, Optional[Path]] = {}
    hashes: Dict[str, Optional[str]] = {}
    for key, _ in METHODS:
        raw_path = case.get(key)
        if raw_path is None:
            if allow_missing:
                paths[key] = None
                hashes[key] = None
                continue
            raise KeyError("Missing '{}' mesh path in manifest".format(key))
        path = _resolve_path(manifest_path, str(raw_path))
        if not path.is_file():
            if allow_missing:
                paths[key] = None
                hashes[key] = None
                continue
            raise FileNotFoundError("Mesh file not found: {}".format(path))
        paths[key] = path
        hashes[key] = _sha256(path)

    observed = [digest for digest in hashes.values() if digest is not None]
    if len(observed) != len(set(observed)):
        raise ValueError("Manifest contains duplicate mesh payloads; no reference copy may substitute for a prediction")

    reference_path = paths["reference_cad"]
    if reference_path is None:
        raise ValueError("A reference CAD mesh is required to define shared bounds")
    reference_vertices, reference_faces = _load_mesh(reference_path, max_triangles)
    meshes: Dict[str, Optional[Tuple[np.ndarray, np.ndarray]]] = {
        "reference_cad": (reference_vertices, reference_faces)
    }
    for key, _ in METHODS[1:]:
        path = paths[key]
        meshes[key] = None if path is None else _load_mesh(path, max_triangles)
    return meshes, hashes, _reference_bounds(reference_vertices)


def _method_title(ax, text: str, key: str) -> None:
    color = COLORS["accent"] if key == "ours" else COLORS["reference"] if key == "reference_cad" else COLORS["ink"]
    ax.set_title(text, fontsize=6.4, fontweight="semibold", color=color, pad=5.0)


def _render_template(output_base: Path, dpi: int, formats: Sequence[str]) -> List[Path]:
    rows = (
        ("(a)", "Overall crown view", False),
        ("(b)", "Cusp-fossa detail", True),
        ("(c)", "Cervical-margin detail", True),
    )
    fig = plt.figure(figsize=(180.0 / 25.4, 108.0 / 25.4), dpi=dpi)
    grid = fig.add_gridspec(
        nrows=len(rows), ncols=len(METHODS), left=0.10, right=0.99, top=0.88, bottom=0.06, wspace=0.03, hspace=0.11
    )
    fig.text(0.10, 0.95, "Same-case qualitative comparison", ha="left", va="center", fontsize=9.0, fontweight="semibold")
    fig.text(
        0.10,
        0.915,
        "Layout template only - replace every slot with a genuine, frozen-run mesh output.",
        ha="left",
        va="center",
        fontsize=5.8,
        color=COLORS["warning"],
    )
    for row_index, (letter, label, detail) in enumerate(rows):
        for column_index, (key, method) in enumerate(METHODS):
            ax = fig.add_subplot(grid[row_index, column_index], projection="3d")
            _configure_axes(ax, np.array([[-1.0, 1.0], [-1.0, 1.0], [-1.0, 1.0]]), 30.0, -55.0)
            _placeholder(ax, detail)
            if row_index == 0:
                _method_title(ax, method, key)
            if column_index == 0:
                ax.text2D(-0.26, 0.5, "{} {}".format(letter, label), transform=ax.transAxes, rotation=90, ha="center", va="center", fontsize=5.8, fontweight="semibold")
    fig.text(
        0.56,
        0.50,
        "TEMPLATE",
        ha="center",
        va="center",
        fontsize=31,
        fontweight="bold",
        color=COLORS["warning"],
        alpha=0.10,
        rotation=22,
        zorder=0,
    )
    paths = _save_figure(fig, output_base, dpi, formats)
    plt.close(fig)
    provenance = {
        "template": True,
        "message": "This layout contains no experimental result meshes.",
        "methods": [key for key, _ in METHODS],
    }
    output_base.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return paths


def _illustrative_crown(key: str) -> Tuple[np.ndarray, np.ndarray]:
    """Create a generic crown-shaped mesh for a clearly labelled layout preview."""
    variants = {
        "reference_cad": {"rings": 42, "angles": 96, "cusp": 1.00, "groove": 1.00, "scale": 1.00, "quantize": 0.0},
        "fdi_nearest_neighbor": {"rings": 40, "angles": 90, "cusp": 0.96, "groove": 0.93, "scale": 1.025, "quantize": 0.0},
        "madcrowner": {"rings": 42, "angles": 94, "cusp": 0.99, "groove": 0.97, "scale": 0.985, "quantize": 0.0},
        "vbcd": {"rings": 38, "angles": 88, "cusp": 0.98, "groove": 0.96, "scale": 1.00, "quantize": 0.025},
        "dcrownformer_plus": {"rings": 41, "angles": 94, "cusp": 0.99, "groove": 0.98, "scale": 1.01, "quantize": 0.0},
        "ours": {"rings": 44, "angles": 96, "cusp": 1.01, "groove": 1.00, "scale": 1.00, "quantize": 0.0},
    }
    if key not in variants:
        raise KeyError("Unknown illustrative crown variant: {}".format(key))
    config = variants[key]
    rings = int(config["rings"])
    angles = int(config["angles"])
    vertices: List[List[float]] = []

    def surface_height(x: float, y: float, radius: float) -> float:
        cusp_centers = ((1.62, 1.18, 1.45), (-1.66, 1.28, 1.52), (1.48, -1.26, 1.35), (-1.54, -1.32, 1.42))
        height = 0.48 - 1.32 * radius ** 1.72
        for cx, cy, amplitude in cusp_centers:
            height += float(config["cusp"]) * amplitude * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / 1.85)
        height -= 0.84 * np.exp(-(x ** 2 / 0.76 + y ** 2 / 0.88))
        diagonal_a = (0.72 * x + 0.70 * y) / 0.24
        diagonal_b = (0.72 * x - 0.70 * y) / 0.28
        height -= float(config["groove"]) * 0.32 * np.exp(-(diagonal_a ** 2)) * np.exp(-radius ** 2 / 0.58)
        height -= float(config["groove"]) * 0.27 * np.exp(-(diagonal_b ** 2)) * np.exp(-radius ** 2 / 0.64)
        height += 0.22 * np.exp(-((radius - 0.82) / 0.13) ** 2)
        step = float(config["quantize"])
        return float(np.round(height / step) * step) if step else float(height)

    center_height = surface_height(0.0, 0.0, 0.0)
    vertices.append([0.0, 0.0, center_height])
    for ring_index in range(1, rings + 1):
        radial = ring_index / float(rings)
        for angle_index in range(angles):
            theta = 2.0 * np.pi * angle_index / float(angles)
            irregular = 1.0 + 0.045 * np.cos(4.0 * theta - 0.35) + 0.018 * np.sin(7.0 * theta)
            x = float(config["scale"]) * 4.08 * radial * irregular * np.cos(theta)
            y = float(config["scale"]) * 3.68 * radial * irregular * np.sin(theta)
            vertices.append([x, y, surface_height(x, y, radial)])

    faces: List[List[int]] = []
    first_ring = 1
    for angle_index in range(angles):
        faces.append([0, first_ring + angle_index, first_ring + (angle_index + 1) % angles])
    for ring_index in range(1, rings):
        current = 1 + (ring_index - 1) * angles
        following = current + angles
        for angle_index in range(angles):
            next_angle = (angle_index + 1) % angles
            faces.append([current + angle_index, following + angle_index, following + next_angle])
            faces.append([current + angle_index, following + next_angle, current + next_angle])

    outer = 1 + (rings - 1) * angles
    bottom_start = len(vertices)
    for angle_index in range(angles):
        x, y, _ = vertices[outer + angle_index]
        theta = 2.0 * np.pi * angle_index / float(angles)
        vertices.append([0.965 * x, 0.965 * y, -2.72 + 0.08 * np.cos(4.0 * theta)])
    bottom_center = len(vertices)
    vertices.append([0.0, 0.0, -2.75])
    for angle_index in range(angles):
        next_angle = (angle_index + 1) % angles
        faces.append([outer + angle_index, bottom_start + angle_index, bottom_start + next_angle])
        faces.append([outer + angle_index, bottom_start + next_angle, outer + next_angle])
        faces.append([bottom_center, bottom_start + next_angle, bottom_start + angle_index])
    return np.asarray(vertices, dtype=np.float64), np.asarray(faces, dtype=np.int64)


def _render_illustrative_preview(output_base: Path, dpi: int, formats: Sequence[str]) -> List[Path]:
    """Render a nonexperimental filled preview of the Figure 4 layout."""
    rows = (
        ("Overall crown view", np.array([[-4.8, 4.8], [-4.4, 4.4], [-3.0, 2.6]]), 64.0, -56.0),
        ("Cusp-fossa detail", np.array([[-2.7, 2.7], [-2.5, 2.5], [-0.8, 2.6]]), 72.0, -56.0),
        ("Cervical-margin detail", np.array([[-4.8, 4.8], [-4.4, 4.4], [-3.0, -0.35]]), 18.0, -65.0),
    )
    meshes = {key: _illustrative_crown(key) for key, _ in METHODS}
    fig = plt.figure(figsize=(180.0 / 25.4, 108.0 / 25.4), dpi=dpi)
    grid = fig.add_gridspec(
        nrows=len(rows), ncols=len(METHODS), left=0.10, right=0.99, top=0.88, bottom=0.06, wspace=0.03, hspace=0.11
    )
    fig.text(0.10, 0.95, "Illustrative qualitative-comparison preview", ha="left", va="center", fontsize=9.0, fontweight="semibold")
    fig.text(
        0.10,
        0.915,
        "Procedural stand-ins for layout review only; they are not outputs of the listed methods and must not be used as results.",
        ha="left",
        va="center",
        fontsize=5.55,
        color=COLORS["warning"],
    )
    for row_index, (label, bounds, elev, azim) in enumerate(rows):
        for column_index, (key, method) in enumerate(METHODS):
            ax = fig.add_subplot(grid[row_index, column_index], projection="3d")
            _configure_axes(ax, bounds, elev, azim)
            mesh = meshes[key]
            _draw_mesh(ax, mesh[0], mesh[1])
            if row_index == 0:
                _method_title(ax, method, key)
            if column_index == 0:
                ax.text2D(
                    -0.26,
                    0.5,
                    "({}) {}".format(chr(ord("a") + row_index), label),
                    transform=ax.transAxes,
                    rotation=90,
                    ha="center",
                    va="center",
                    fontsize=5.8,
                    fontweight="semibold",
                )
    fig.text(
        0.55,
        0.50,
        "ILLUSTRATIVE - NOT RESULTS",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color=COLORS["warning"],
        alpha=0.11,
        rotation=21,
        zorder=0,
    )
    paths = _save_figure(fig, output_base, dpi, formats)
    plt.close(fig)
    provenance = {
        "illustrative_preview": True,
        "message": "Procedural crown-shaped meshes are layout stand-ins, not experimental outputs.",
        "methods": [key for key, _ in METHODS],
    }
    output_base.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return paths


def _save_figure(fig, output_base: Path, dpi: int, formats: Sequence[str]) -> List[Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for fmt in formats:
        path = output_base.with_suffix("." + fmt)
        fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.02)
        paths.append(path)
    return paths


def _render_manifest(manifest_path: Path, output_base: Path, dpi: int, formats: Sequence[str], max_triangles: int) -> List[Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = manifest.get("cases")
    rows = manifest.get("rows")
    if not isinstance(cases, Mapping) or not isinstance(rows, list) or not rows:
        raise ValueError("Manifest requires non-empty 'cases' and 'rows' entries")
    if len(rows) > 6:
        raise ValueError("Figure 4 supports at most six rows; split additional cases into a supplementary figure")

    prepared: Dict[str, Tuple[Dict[str, Optional[Tuple[np.ndarray, np.ndarray]]], Dict[str, Optional[str]], np.ndarray]] = {}
    for case_id, case in cases.items():
        if not isinstance(case, Mapping):
            raise ValueError("Case '{}' must be an object".format(case_id))
        prepared[str(case_id)] = _case_meshes(case, manifest_path, max_triangles, allow_missing=False)

    height_mm = 22.0 + 27.0 * len(rows)
    fig = plt.figure(figsize=(180.0 / 25.4, height_mm / 25.4), dpi=dpi)
    grid = fig.add_gridspec(
        nrows=len(rows), ncols=len(METHODS), left=0.10, right=0.99, top=0.90, bottom=0.05, wspace=0.03, hspace=0.10
    )
    fig.text(0.10, 0.956, "Same-case qualitative comparison", ha="left", va="center", fontsize=9.0, fontweight="semibold")
    fig.text(
        0.10,
        0.923,
        "All meshes use the reference-defined coordinate frame, camera, material, and bounds.",
        ha="left",
        va="center",
        fontsize=5.6,
        color=COLORS["muted"],
    )

    provenance: Dict[str, object] = {
        "template": False,
        "manifest": str(manifest_path),
        "max_triangles": max_triangles,
        "cases": {},
    }
    for row_index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError("Each row must be an object")
        case_id = str(row.get("case", ""))
        if case_id not in prepared:
            raise KeyError("Row {} references unknown case '{}'".format(row_index + 1, case_id))
        meshes, hashes, reference_bounds = prepared[case_id]
        label = str(row.get("label", "Case {}".format(case_id)))
        view = row.get("view", {})
        if not isinstance(view, Mapping):
            raise ValueError("Row '{}' view must be an object".format(label))
        elev = float(view.get("elev", 30.0))
        azim = float(view.get("azim", -55.0))
        bounds = _parse_bounds(row.get("bounds"), reference_bounds, label)
        is_detail = row.get("bounds") not in (None, "reference")
        provenance["cases"][case_id] = hashes

        for column_index, (key, method) in enumerate(METHODS):
            ax = fig.add_subplot(grid[row_index, column_index], projection="3d")
            _configure_axes(ax, bounds, elev, azim)
            mesh = meshes[key]
            if mesh is None:
                raise ValueError("Missing '{}' output for case '{}'".format(key, case_id))
            _draw_mesh(ax, mesh[0], mesh[1])
            if row_index == 0:
                _method_title(ax, method, key)
            if column_index == 0:
                ax.text2D(
                    -0.25,
                    0.5,
                    "({}) {}".format(chr(ord("a") + row_index), label),
                    transform=ax.transAxes,
                    rotation=90,
                    ha="center",
                    va="center",
                    fontsize=5.7,
                    fontweight="semibold",
                )
            if is_detail:
                ax.text2D(0.03, 0.04, "fixed ROI", transform=ax.transAxes, ha="left", va="bottom", fontsize=4.4, color=COLORS["muted"])

    paths = _save_figure(fig, output_base, dpi, formats)
    plt.close(fig)
    output_base.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--template", action="store_true", help="Render the clearly watermarked planning template.")
    source.add_argument("--illustrative-preview", action="store_true", help="Render clearly labelled procedural stand-ins for layout review only.")
    source.add_argument("--manifest", type=Path, help="JSON manifest for genuine same-case meshes.")
    parser.add_argument("--output-base", type=Path, default=None, help="Output path without a suffix.")
    parser.add_argument("--formats", nargs="+", default=["png", "pdf", "svg"], choices=["png", "pdf", "svg"])
    parser.add_argument("--dpi", type=int, default=600)
    parser.add_argument(
        "--max-triangles",
        type=int,
        default=0,
        help="Optional display-only triangle cap; 0 preserves the input meshes.",
    )
    args = parser.parse_args()
    if args.dpi < 300:
        raise ValueError("Use at least 300 dpi for manuscript figures")
    if args.max_triangles < 0:
        raise ValueError("--max-triangles must be non-negative")

    if args.template:
        output_base = args.output_base or DEFAULT_TEMPLATE_BASE
        paths = _render_template(output_base, args.dpi, args.formats)
    elif args.illustrative_preview:
        output_base = args.output_base or ROOT / "figure4_method_comparison_illustrative_preview"
        paths = _render_illustrative_preview(output_base, args.dpi, args.formats)
    else:
        manifest_path = args.manifest.expanduser().resolve()
        if not manifest_path.is_file():
            raise FileNotFoundError("Manifest not found: {}".format(manifest_path))
        output_base = args.output_base or ROOT / "figure4_method_comparison"
        paths = _render_manifest(manifest_path, output_base, args.dpi, args.formats, args.max_triangles)
    print("Generated:")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
