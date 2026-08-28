#!/usr/bin/env python3
"""Generate the oriented signed-FDG local-detail figure for the Method section."""

from pathlib import Path
import warnings

import matplotlib as mpl
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle


mpl.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "assets" / "method_framework"
FIG_WIDTH_IN = 180.0 / 25.4
FIG_HEIGHT_IN = 54.0 / 25.4

COLORS = {
    "ink": "#24313C",
    "muted": "#66747D",
    "line": "#D5DEE4",
    "grid": "#BDCBD3",
    "inactive": "#E9EFF2",
    "amber": "#C9843C",
    "amber_dark": "#9B6126",
    "amber_fill": "#F6E8D6",
    "blue": "#2E729F",
    "blue_dark": "#1F567A",
    "blue_fill": "#EAF3F8",
    "purple": "#7355A4",
    "purple_dark": "#574078",
    "purple_fill": "#F2EEF8",
    "surface": "#D8B47B",
    "surface_edge": "#9A7043",
    "white": "#FFFFFF",
}

mpl.rcParams.update(
    {
        "font.family": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 6.0,
        "text.color": COLORS["ink"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def place_png(ax, path, x, y, width, height, *, zorder=2):
    """Place a transparent bitmap asset without changing its aspect ratio."""
    path = Path(path)
    if not path.is_file():
        return False
    try:
        image = plt.imread(path)
    except (OSError, ValueError) as exc:
        warnings.warn(f"Unable to load figure asset {path}: {exc}")
        return False
    if image.ndim == 3 and image.shape[-1] == 4:
        visible = image[..., 3] > 0.01
        if visible.any():
            rows, cols = np.where(visible)
            image = image[rows.min() : rows.max() + 1, cols.min() : cols.max() + 1]
    ratio = image.shape[1] / image.shape[0]
    slot_ratio = width / height
    if ratio >= slot_ratio:
        draw_width, draw_height = width, width / ratio
    else:
        draw_height, draw_width = height, height * ratio
    draw_x = x + (width - draw_width) / 2.0
    draw_y = y + (height - draw_height) / 2.0
    ax.imshow(
        image,
        extent=(draw_x, draw_x + draw_width, draw_y, draw_y + draw_height),
        interpolation="lanczos",
        zorder=zorder,
    )
    return True


def arrow(ax, start, end, *, color, lw=0.9, style="-", scale=6.0, zorder=8):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=scale,
        linewidth=lw,
        linestyle=style,
        color=color,
        shrinkA=1.0,
        shrinkB=1.0,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def leader(ax, points, *, color, lw=0.55, style=(0, (2.0, 1.7)), zorder=7):
    xs, ys = zip(*points)
    ax.plot(
        xs,
        ys,
        color=color,
        linewidth=lw,
        linestyle=style,
        solid_capstyle="round",
        dash_capstyle="round",
        zorder=zorder,
    )


def panel_heading(ax, x, label, title):
    ax.text(x, 6.77, f"({label})", ha="left", va="center", fontsize=6.8, fontweight="bold")
    ax.text(x + 0.55, 6.77, title, ha="left", va="center", fontsize=6.3, fontweight="semibold")


def iso(origin, x, y, z, scale=0.84):
    """Map a local voxel coordinate into a compact isometric drawing."""
    return (
        origin[0] + scale * (x - 0.72 * y),
        origin[1] + scale * (0.34 * x + 0.34 * y + z),
    )


def cube_vertices(origin, cell, *, scale=0.84):
    x, y, z = cell
    return [
        iso(origin, x + dx, y + dy, z + dz, scale)
        for dz in (0, 1)
        for dy in (0, 1)
        for dx in (0, 1)
    ]


def draw_cube(ax, origin, cell, *, active=False, emphasis=False, zorder=3):
    vertices = cube_vertices(origin, cell)
    # Vertex indices use x as the fast axis, then y, then z.
    faces = ((0, 1, 3, 2), (0, 1, 5, 4), (1, 3, 7, 5))
    edge_pairs = (
        (0, 1),
        (0, 2),
        (0, 4),
        (1, 3),
        (1, 5),
        (2, 3),
        (2, 6),
        (3, 7),
        (4, 5),
        (4, 6),
        (5, 7),
        (6, 7),
    )
    if active:
        fill = COLORS["amber_fill"]
        edge = COLORS["amber_dark"] if emphasis else COLORS["amber"]
        alpha = 0.20 if emphasis else 0.10
        line_width = 0.78 if emphasis else 0.45
    else:
        fill = COLORS["inactive"]
        edge = COLORS["grid"]
        alpha = 0.11
        line_width = 0.30
    for face in faces:
        ax.add_patch(
            Polygon(
                [vertices[index] for index in face],
                closed=True,
                facecolor=fill,
                edgecolor="none",
                alpha=alpha,
                zorder=zorder,
            )
        )
    for start, end in edge_pairs:
        ax.plot(
            [vertices[start][0], vertices[end][0]],
            [vertices[start][1], vertices[end][1]],
            color=edge,
            linewidth=line_width,
            alpha=0.92 if active else 0.6,
            zorder=zorder + 0.2,
        )
    return vertices


def draw_surface_patch(ax):
    """Draw a stylized local crown surface passing through active cells."""
    vertices = np.array(
        [
        (8.35, 3.15),
        (9.45, 3.75),
        (10.26, 3.42),
        (11.28, 4.08),
        (12.26, 3.70),
        (13.55, 4.52),
        (13.30, 5.05),
        (12.00, 4.41),
        (11.18, 4.78),
        (10.10, 4.16),
        (9.16, 4.52),
        (8.25, 3.86),
        ]
    )
    patch = Polygon(
        vertices,
        closed=True,
        facecolor=COLORS["surface"],
        edgecolor=COLORS["surface_edge"],
        linewidth=0.75,
        alpha=0.70,
        zorder=5.5,
    )
    ax.add_patch(patch)
    for offset in (0.0, 0.22, -0.22):
        ax.plot(
            [8.55, 9.65, 10.80, 12.05, 13.25],
            [3.58 + offset, 4.14 + offset * 0.4, 3.83 + offset, 4.43 + offset * 0.25, 4.74 + offset * 0.45],
            color=COLORS["surface_edge"],
            linewidth=0.33,
            alpha=0.55,
            zorder=6,
        )


def draw_crown_support(ax):
    panel_heading(ax, 0.42, "a", "Sparse surface support")
    asset_loaded = place_png(
        ax,
        ASSET_DIR / "reference_cad.png",
        0.70,
        1.03,
        5.65,
        5.25,
        zorder=2,
    )
    if not asset_loaded:
        crown = np.array(
            [[1.05, 2.0], [1.25, 4.7], [2.65, 5.65], [4.45, 5.35], [5.65, 4.2], [5.90, 2.25], [4.6, 1.2], [2.15, 1.15]]
        )
        ax.add_patch(
            Polygon(crown, closed=True, facecolor=COLORS["surface"], edgecolor=COLORS["surface_edge"], alpha=0.82, zorder=2)
        )
    selection = (3.35, 4.06)
    ax.add_patch(
        Circle(
            selection,
            0.66,
            facecolor="none",
            edgecolor=COLORS["amber"],
            linewidth=1.12,
            zorder=5,
        )
    )
    for dx, dy in ((-0.32, 0.20), (0.0, 0.28), (0.31, 0.11), (-0.26, -0.16), (0.12, -0.23), (0.42, -0.11)):
        x, y = selection[0] + dx, selection[1] + dy
        ax.add_patch(
            Polygon(
                [(x - 0.14, y), (x, y + 0.08), (x + 0.14, y), (x, y - 0.08)],
                closed=True,
                facecolor=COLORS["amber_fill"],
                edgecolor=COLORS["amber"],
                linewidth=0.40,
                alpha=0.78,
                zorder=6,
            )
        )
    ax.text(3.35, 1.00, "active cells near the reference surface", ha="center", va="center", fontsize=4.8, color=COLORS["muted"])
    leader(ax, [(4.02, 4.30), (6.75, 4.30), (8.15, 4.48)], color=COLORS["amber"], lw=0.82, style=(0, (2.2, 1.8)), zorder=6)


def draw_local_fdg(ax):
    panel_heading(ax, 7.92, "b", "Local oriented signed FDG")
    origin = (10.28, 1.74)
    # Light local background establishes a grid without suggesting dense storage.
    for cell in ((0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (1, 2, 0), (2, 2, 0)):
        draw_cube(ax, origin, cell, active=False, zorder=2.5)
    active_cells = ((1, 1, 0), (2, 1, 0), (2, 0, 1), (1, 2, 0), (3, 1, 0))
    for cell in active_cells:
        draw_cube(ax, origin, cell, active=True, emphasis=cell == (2, 1, 0), zorder=3.2)
    draw_surface_patch(ax)

    x_j = iso(origin, 2.5, 1.5, 0.5)
    p_j = (11.30, 4.08)
    v_j = (11.57, 3.78)
    b_j = ((10.82, 3.30), (11.76, 3.55), (11.04, 4.06))
    ax.add_patch(Circle(x_j, 0.065, facecolor=COLORS["blue"], edgecolor=COLORS["white"], linewidth=0.30, zorder=9))
    ax.add_patch(Circle(p_j, 0.062, facecolor=COLORS["blue_dark"], edgecolor=COLORS["white"], linewidth=0.30, zorder=10))
    ax.add_patch(
        Polygon(
            [(v_j[0], v_j[1] + 0.095), (v_j[0] + 0.095, v_j[1]), (v_j[0], v_j[1] - 0.095), (v_j[0] - 0.095, v_j[1])],
            closed=True,
            facecolor=COLORS["amber"],
            edgecolor=COLORS["amber_dark"],
            linewidth=0.45,
            zorder=10,
        )
    )
    for point in b_j:
        ax.add_patch(Circle(point, 0.047, facecolor=COLORS["white"], edgecolor=COLORS["amber_dark"], linewidth=0.55, zorder=10))
    ax.plot([x_j[0], p_j[0]], [x_j[1], p_j[1]], color=COLORS["blue"], linewidth=0.78, linestyle=(0, (2.0, 1.5)), zorder=9)
    arrow(ax, p_j, (11.88, 4.73), color=COLORS["purple"], lw=0.95, scale=6.0, zorder=10)

    ax.text(x_j[0] - 0.38, x_j[1] - 0.24, r"$x_j$", ha="center", va="center", fontsize=5.0, color=COLORS["blue_dark"], zorder=11)
    ax.text(p_j[0] - 0.48, p_j[1] + 0.20, r"$p_j$", ha="center", va="center", fontsize=5.0, color=COLORS["blue_dark"], zorder=11)
    ax.text(10.60, 3.84, r"$d_j$", ha="center", va="center", fontsize=5.0, color=COLORS["blue_dark"], zorder=11)
    ax.text(12.01, 4.83, r"$n_j$", ha="center", va="center", fontsize=5.0, color=COLORS["purple_dark"], zorder=11)
    ax.text(11.88, 3.70, r"$v_j$", ha="center", va="center", fontsize=5.0, color=COLORS["amber_dark"], zorder=11)
    ax.text(12.40, 3.42, r"$b_j$", ha="center", va="center", fontsize=5.0, color=COLORS["amber_dark"], zorder=11)
    leader(ax, [(12.22, 3.46), (11.96, 3.50), (11.76, 3.55)], color=COLORS["amber_dark"], lw=0.45, style="-", zorder=9)
    ax.text(8.18, 1.07, "inactive cells", ha="left", va="center", fontsize=4.5, color=COLORS["muted"])
    ax.add_patch(Rectangle((7.92, 0.91), 0.17, 0.17, facecolor=COLORS["inactive"], edgecolor=COLORS["grid"], linewidth=0.35, alpha=0.75, zorder=8))
    ax.text(12.12, 1.07, "active surface cells", ha="left", va="center", fontsize=4.5, color=COLORS["amber_dark"])
    ax.add_patch(Rectangle((11.88, 0.91), 0.17, 0.17, facecolor=COLORS["amber_fill"], edgecolor=COLORS["amber"], linewidth=0.40, alpha=0.85, zorder=8))


def draw_geometry_code(ax):
    panel_heading(ax, 18.20, "c", "Per-cell geometry code")
    ax.text(20.77, 5.65, r"shared active coordinate $c_j$", ha="center", va="center", fontsize=4.9, color=COLORS["muted"])
    x, y, width, height = 18.40, 3.12, 3.25, 1.22
    item_width = width / 4.0
    fields = (
        (r"$v_j$", COLORS["amber_fill"], COLORS["amber_dark"]),
        (r"$b_j$", COLORS["amber_fill"], COLORS["amber_dark"]),
        (r"$d_j$", COLORS["blue_fill"], COLORS["blue_dark"]),
        (r"$n_j$", COLORS["purple_fill"], COLORS["purple_dark"]),
    )
    for index, (label, fill, edge) in enumerate(fields):
        cell_x = x + index * item_width
        ax.add_patch(
            Rectangle(
                (cell_x, y),
                item_width,
                height,
                facecolor=fill,
                edgecolor=edge,
                linewidth=0.58,
                zorder=5,
            )
        )
        ax.text(cell_x + item_width / 2, y - 0.27, label, ha="center", va="center", fontsize=5.35, color=edge, zorder=8)
    # Small field-specific icons keep the code legible without numerical channel counts.
    ax.add_patch(
        Polygon([(18.81, 3.87), (18.91, 3.77), (18.81, 3.67), (18.71, 3.77)], closed=True, facecolor=COLORS["amber"], edgecolor=COLORS["amber_dark"], linewidth=0.42, zorder=8)
    )
    for offset in (-0.13, 0.0, 0.13):
        ax.add_patch(Circle((19.63 + offset, 3.77), 0.042, facecolor=COLORS["white"], edgecolor=COLORS["amber_dark"], linewidth=0.42, zorder=8))
    ax.plot([20.20, 20.55], [3.58, 3.99], color=COLORS["blue"], linewidth=0.68, linestyle=(0, (2.0, 1.4)), zorder=8)
    arrow(ax, (21.16, 3.58), (21.16, 4.03), color=COLORS["purple"], lw=0.78, scale=4.9, zorder=8)
    ax.text(20.03, 2.47, r"$g_j=[v_j-0.5,\ b_j-0.5,\ d_j,\ n_j]$", ha="center", va="center", fontsize=4.95, fontweight="semibold", color=COLORS["ink"])
    arrow(ax, (21.72, 3.72), (22.10, 3.72), color=COLORS["amber"], lw=0.92, scale=5.6, zorder=8)
    ax.add_patch(
        Rectangle((22.15, 3.05), 1.20, 1.34, facecolor="#F9FBFC", edgecolor=COLORS["blue"], linewidth=0.74, zorder=5)
    )
    for row in range(3):
        for col in range(3):
            ax.add_patch(
                Rectangle(
                    (22.36 + col * 0.21, 3.34 + row * 0.21),
                    0.14,
                    0.14,
                    facecolor=COLORS["blue"] if (row, col) in ((0, 1), (1, 1), (1, 2), (2, 0)) else COLORS["white"],
                    edgecolor="#91B7CF",
                    linewidth=0.24,
                    zorder=7,
                )
            )
    ax.text(22.75, 4.73, "Sparse geometry VAE", ha="center", va="center", fontsize=4.9, fontweight="semibold", color=COLORS["blue_dark"])
    ax.text(20.77, 1.08, "FDG geometry + oriented surface cues", ha="center", va="center", fontsize=4.75, color=COLORS["muted"])


def build_figure():
    fig, ax = plt.subplots(figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))
    ax.set_xlim(0.0, 24.0)
    ax.set_ylim(0.0, 7.2)
    ax.set_aspect("equal")
    ax.axis("off")
    # Deliberately light structure: the visual hierarchy is the left-to-right zoom.
    ax.plot([7.45, 7.45], [0.55, 6.42], color=COLORS["line"], linewidth=0.72, zorder=0)
    ax.plot([17.72, 17.72], [0.55, 6.42], color=COLORS["line"], linewidth=0.72, zorder=0)
    draw_crown_support(ax)
    draw_local_fdg(ax)
    draw_geometry_code(ax)
    arrow(ax, (17.45, 3.80), (18.08, 3.80), color=COLORS["amber"], lw=1.0, scale=6.0, zorder=9)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    exports = {"png": {"dpi": 600}, "pdf": {}, "svg": {}}
    for extension, kwargs in exports.items():
        fig.savefig(
            ROOT / f"oriented_signed_fdg_detail.{extension}",
            facecolor=COLORS["white"],
            edgecolor="none",
            metadata={"Title": "Oriented signed flexible dual-grid representation"},
            **kwargs,
        )
    plt.close(fig)


if __name__ == "__main__":
    build_figure()
