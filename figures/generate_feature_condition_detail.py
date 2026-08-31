#!/usr/bin/env python3
"""Generate the coordinate-wise Feature Flow conditioning detail figure."""

from pathlib import Path
import warnings

import matplotlib as mpl
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

mpl.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "assets" / "method_framework"
FIG_WIDTH_IN = 180.0 / 25.4
FIG_HEIGHT_IN = 54.0 / 25.4

COLORS = {
    "ink": "#24313C",
    "muted": "#687681",
    "blue": "#2E729F",
    "blue_dark": "#1F567A",
    "blue_fill": "#EAF3F8",
    "purple": "#7355A4",
    "purple_dark": "#574078",
    "purple_fill": "#F2EEF8",
    "gray": "#AEBBC2",
    "gray_fill": "#F4F7F8",
    "green": "#669C82",
    "green_fill": "#EFF6F1",
    "margin": "#D96055",
    "margin_fill": "#FBEDEA",
    "line": "#D2DEE5",
    "white": "#FFFFFF",
}

CONDITION_STYLE = (0, (5, 2, 1.2, 2))

mpl.rcParams.update(
    {
        "font.family": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 6.2,
        "text.color": COLORS["ink"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def rounded_box(
    ax,
    x,
    y,
    w,
    h,
    text="",
    *,
    fc=COLORS["white"],
    ec=COLORS["line"],
    lw=0.75,
    fontsize=6.0,
    weight="normal",
    radius=0.07,
    color=COLORS["ink"],
    zorder=4,
):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.025,rounding_size={radius}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        zorder=zorder,
    )
    ax.add_patch(patch)
    if text:
        ax.text(
            x + w / 2,
            y + h / 2,
            text,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight=weight,
            color=color,
            linespacing=1.02,
            zorder=zorder + 1,
        )
    return patch


def arrow(
    ax,
    start,
    end,
    *,
    color=COLORS["blue"],
    lw=1.0,
    style="-",
    mutation_scale=6.4,
    zorder=6,
):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        linewidth=lw,
        linestyle=style,
        color=color,
        shrinkA=1.0,
        shrinkB=1.0,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def poly_arrow(ax, points, *, color, lw=1.0, style="-", mutation_scale=6.4, zorder=6):
    xs, ys = zip(*points[:-1])
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
    arrow(
        ax,
        points[-2],
        points[-1],
        color=color,
        lw=lw,
        style=style,
        mutation_scale=mutation_scale,
        zorder=zorder + 0.1,
    )


def panel(ax, x, y, w, h, title, label, *, fill, edge):
    rounded_box(ax, x, y, w, h, fc=fill, ec=edge, lw=0.8, radius=0.11, zorder=0)
    ax.text(
        x + 0.22,
        y + h - 0.36,
        f"({label})",
        ha="left",
        va="center",
        fontsize=7.0,
        fontweight="bold",
        zorder=10,
    )
    ax.text(
        x + 0.80,
        y + h - 0.36,
        title,
        ha="left",
        va="center",
        fontsize=6.9,
        fontweight="semibold",
        zorder=10,
    )


def place_png(ax, path, x, y, w, h, *, zorder=4):
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
    slot_ratio = w / h
    if ratio >= slot_ratio:
        draw_w, draw_h = w, w / ratio
    else:
        draw_h, draw_w = h, h * ratio
    draw_x = x + (w - draw_w) / 2
    draw_y = y + (h - draw_h) / 2
    ax.imshow(
        image,
        extent=(draw_x, draw_x + draw_w, draw_y, draw_y + draw_h),
        interpolation="lanczos",
        zorder=zorder,
    )
    return True


def draw_case_context(ax, x, y, w, h):
    rounded_box(ax, x, y, w, h, fc=COLORS["white"], ec="#C5D3DA", lw=0.7)
    ax.text(
        x + 0.18,
        y + h - 0.24,
        "Case-aligned local anatomy",
        ha="left",
        va="center",
        fontsize=5.5,
        fontweight="semibold",
        zorder=8,
    )
    if not place_png(
        ax,
        ASSET_DIR / "scans.png",
        x + 0.10,
        y + 0.48,
        0.72 * w,
        0.67 * h,
        zorder=4,
    ):
        for index, color in enumerate((COLORS["gray"], COLORS["green"])):
            yy = y + 1.50 + index * 0.72
            ax.plot(
                [x + 0.25, x + 0.50 * w, x + 0.88 * w],
                [yy, yy + 0.12, yy],
                color=color,
                linewidth=3.0,
                solid_capstyle="round",
                zorder=4,
            )
    theta = np.linspace(0, 2 * np.pi, 80)
    margin_x = x + 0.49 * w + 0.18 * w * np.cos(theta)
    margin_y = y + 0.50 * h + 0.10 * h * np.sin(theta)
    ax.plot(margin_x, margin_y, color=COLORS["margin"], linewidth=0.95, zorder=8)
    qx, qy = x + 0.49 * w, y + 0.50 * h
    ax.add_patch(
        Circle(
            (qx, qy),
            0.105 * h,
            facecolor=COLORS["blue_fill"],
            edgecolor=COLORS["blue"],
            linewidth=0.85,
            zorder=9,
        )
    )
    ax.text(
        qx,
        qy,
        r"$q$",
        ha="center",
        va="center",
        fontsize=6.3,
        color=COLORS["blue_dark"],
        zorder=10,
    )


def _source_markers(ax, x, y, scale=1.0, *, zorder=8):
    specs = (
        (-0.28, 0.12, COLORS["gray"]),
        (-0.07, 0.22, COLORS["gray"]),
        (0.17, 0.09, COLORS["green"]),
        (0.29, 0.21, COLORS["green"]),
        (0.03, -0.20, COLORS["margin"]),
    )
    for dx, dy, color in specs:
        ax.add_patch(
            Circle(
                (x + scale * dx, y + scale * dy),
                0.055 * scale,
                facecolor=color,
                edgecolor=COLORS["white"],
                linewidth=0.22,
                zorder=zorder,
            )
        )


def draw_global_context(ax, x, y, w, h):
    rounded_box(ax, x, y, w, h, fc=COLORS["purple_fill"], ec="#A793C3", lw=0.75)
    ax.text(
        x + w / 2,
        y + 0.78 * h,
        r"Global semantic $C_F^g$",
        ha="center",
        va="center",
        fontsize=5.25,
        fontweight="semibold",
        color=COLORS["purple_dark"],
        zorder=8,
    )
    _source_markers(ax, x + 0.32 * w, y + 0.43 * h, 0.52 * w)
    ax.plot(
        [x + 0.49 * w, x + 0.65 * w],
        [y + 0.43 * h, y + 0.43 * h],
        color=COLORS["purple"],
        linewidth=0.68,
        zorder=7,
    )
    arrow(
        ax,
        (x + 0.65 * w, y + 0.43 * h),
        (x + 0.70 * w, y + 0.43 * h),
        color=COLORS["purple"],
        lw=0.68,
        mutation_scale=4.4,
    )
    rounded_box(
        ax,
        x + 0.72 * w,
        y + 0.28 * h,
        0.20 * w,
        0.30 * h,
        "FDI",
        fc=COLORS["white"],
        ec="#B8A6CC",
        fontsize=4.5,
        weight="semibold",
        radius=0.025,
        color=COLORS["purple_dark"],
        zorder=8,
    )
    ax.text(
        x + w / 2,
        y + 0.13 * h,
        "pooled case context",
        ha="center",
        va="center",
        fontsize=4.45,
        color=COLORS["muted"],
        zorder=8,
    )


def draw_voxel_context(ax, x, y, w, h):
    rounded_box(ax, x, y, w, h, fc=COLORS["purple_fill"], ec="#A793C3", lw=0.75)
    ax.text(
        x + w / 2,
        y + 0.78 * h,
        r"Voxel-aligned $C_{F,64}^v(q)$",
        ha="center",
        va="center",
        fontsize=5.1,
        fontweight="semibold",
        color=COLORS["purple_dark"],
        zorder=8,
    )
    gx, gy, gw, gh = x + 0.20 * w, y + 0.23 * h, 0.46 * w, 0.40 * h
    for row in range(3):
        for col in range(4):
            highlight = row == 1 and col == 2
            ax.add_patch(
                Rectangle(
                    (gx + col * gw / 4, gy + row * gh / 3),
                    gw / 4,
                    gh / 3,
                    facecolor="#C6B8DB" if highlight else COLORS["white"],
                    edgecolor="#AFA0C6",
                    linewidth=0.28,
                    zorder=6,
                )
            )
    qx, qy = gx + 2.5 * gw / 4, gy + 1.5 * gh / 3
    ax.add_patch(
        Circle((qx, qy), 0.052 * w, facecolor=COLORS["blue"], edgecolor="none", zorder=8))
    arrow(
        ax,
        (x + 0.69 * w, y + 0.41 * h),
        (x + 0.86 * w, y + 0.41 * h),
        color=COLORS["purple"],
        lw=0.68,
        mutation_scale=4.4,
    )
    ax.text(
        x + w / 2,
        y + 0.13 * h,
        "scatter, refine, lookup",
        ha="center",
        va="center",
        fontsize=4.45,
        color=COLORS["muted"],
        zorder=8,
    )


def draw_query_context(ax, x, y, w, h):
    rounded_box(ax, x, y, w, h, fc=COLORS["margin_fill"], ec="#E2AAA3", lw=0.75)
    ax.text(
        x + w / 2,
        y + 0.79 * h,
        r"Dental neighborhood $C_F^n(q)$",
        ha="center",
        va="center",
        fontsize=5.0,
        fontweight="semibold",
        color="#994A43",
        zorder=8,
    )
    qx, qy = x + 0.50 * w, y + 0.44 * h
    _source_markers(ax, qx, qy, 0.84 * w)
    for dx, dy in ((-0.28, 0.12), (-0.07, 0.22), (0.17, 0.09), (0.29, 0.21), (0.03, -0.20)):
        ax.plot(
            [qx, qx + 0.84 * w * dx],
            [qy, qy + 0.84 * w * dy],
            color="#C1847E",
            linewidth=0.36,
            zorder=6,
        )
    ax.add_patch(
        Circle(
            (qx, qy),
            0.075 * w,
            facecolor=COLORS["blue_fill"],
            edgecolor=COLORS["blue"],
            linewidth=0.7,
            zorder=9,
        )
    )
    ax.text(qx, qy, r"$q$", ha="center", va="center", fontsize=5.2, color=COLORS["blue_dark"], zorder=10)
    ax.text(
        x + w / 2,
        y + 0.12 * h,
        "relative position, normal, distance",
        ha="center",
        va="center",
        fontsize=4.25,
        color=COLORS["muted"],
        zorder=8,
    )


def draw_support_context(ax, x, y, w, h):
    rounded_box(ax, x, y, w, h, fc=COLORS["blue_fill"], ec="#9FBDD0", lw=0.75)
    ax.text(
        x + w / 2,
        y + 0.79 * h,
        r"Support adapter $A(q;\hat O)$",
        ha="center",
        va="center",
        fontsize=5.0,
        fontweight="semibold",
        color=COLORS["blue_dark"],
        zorder=8,
    )
    qx, qy = x + 0.50 * w, y + 0.43 * h
    offsets = ((-0.30, 0.0), (-0.18, 0.0), (0.18, 0.0), (0.30, 0.0), (0.0, -0.22), (0.0, 0.22))
    for dx, dy in offsets:
        ax.add_patch(
            Rectangle(
                (qx + dx * w - 0.045 * w, qy + dy * w - 0.045 * w),
                0.09 * w,
                0.09 * w,
                facecolor=COLORS["white"],
                edgecolor="#75A1BC",
                linewidth=0.42,
                zorder=7,
            )
        )
        ax.plot([qx, qx + dx * w], [qy, qy + dy * w], color="#8AB5CC", linewidth=0.36, zorder=6)
    ax.add_patch(
        Rectangle(
            (qx - 0.055 * w, qy - 0.055 * w),
            0.11 * w,
            0.11 * w,
            facecolor=COLORS["blue"],
            edgecolor=COLORS["blue_dark"],
            linewidth=0.48,
            zorder=9,
        )
    )
    ax.text(
        x + w / 2,
        y + 0.12 * h,
        "sparse axial context",
        ha="center",
        va="center",
        fontsize=4.45,
        color=COLORS["muted"],
        zorder=8,
    )


def draw_global_voxel_group(ax, x, y, w, h):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        fc=COLORS["purple_fill"],
        ec="#A793C3",
        lw=0.8,
        radius=0.07,
    )
    ax.plot(
        [x + 0.50 * w, x + 0.50 * w],
        [y + 0.17 * h, y + 0.82 * h],
        color="#C2B3D6",
        linewidth=0.5,
        zorder=6,
    )
    ax.text(
        x + 0.25 * w,
        y + 0.81 * h,
        r"Global $C_F^g$",
        ha="center",
        va="center",
        fontsize=5.0,
        fontweight="semibold",
        color=COLORS["purple_dark"],
        zorder=8,
    )
    _source_markers(ax, x + 0.18 * w, y + 0.46 * h, 0.32 * w)
    rounded_box(
        ax,
        x + 0.31 * w,
        y + 0.32 * h,
        0.13 * w,
        0.24 * h,
        "FDI",
        fc=COLORS["white"],
        ec="#B8A6CC",
        fontsize=3.9,
        weight="semibold",
        radius=0.02,
        color=COLORS["purple_dark"],
        zorder=8,
    )
    ax.text(
        x + 0.25 * w,
        y + 0.15 * h,
        "pooled semantics",
        ha="center",
        va="center",
        fontsize=4.45,
        color=COLORS["muted"],
        zorder=8,
    )

    ax.text(
        x + 0.75 * w,
        y + 0.81 * h,
        r"Voxel field $C_{F,64}^v$",
        ha="center",
        va="center",
        fontsize=5.0,
        fontweight="semibold",
        color=COLORS["purple_dark"],
        zorder=8,
    )
    gx, gy, gw, gh = x + 0.59 * w, y + 0.29 * h, 0.30 * w, 0.34 * h
    for row in range(3):
        for col in range(4):
            selected = row == 1 and col == 2
            ax.add_patch(
                Rectangle(
                    (gx + col * gw / 4, gy + row * gh / 3),
                    gw / 4,
                    gh / 3,
                    facecolor="#C6B8DB" if selected else COLORS["white"],
                    edgecolor="#AFA0C6",
                    linewidth=0.24,
                    zorder=6,
                )
            )
    ax.add_patch(
        Circle(
            (gx + 2.5 * gw / 4, gy + 1.5 * gh / 3),
            0.038 * w,
            facecolor=COLORS["blue"],
            edgecolor="none",
            zorder=8,
        )
    )
    ax.text(
        x + 0.75 * w,
        y + 0.15 * h,
        r"downsample: $C_{F,16}^v$; lookup at $q$",
        ha="center",
        va="center",
        fontsize=4.45,
        color=COLORS["muted"],
        zorder=8,
    )


def draw_local_support_group(ax, x, y, w, h):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        fc="#F7FAFC",
        ec="#AAC2D1",
        lw=0.8,
        radius=0.07,
    )
    ax.plot(
        [x + 0.50 * w, x + 0.50 * w],
        [y + 0.17 * h, y + 0.82 * h],
        color="#C7D8E2",
        linewidth=0.5,
        zorder=6,
    )
    ax.text(
        x + 0.25 * w,
        y + 0.81 * h,
        r"Dental $C_F^n(q)$",
        ha="center",
        va="center",
        fontsize=5.0,
        fontweight="semibold",
        color="#994A43",
        zorder=8,
    )
    qx, qy = x + 0.25 * w, y + 0.45 * h
    _source_markers(ax, qx, qy, 0.36 * w)
    for dx, dy in ((-0.28, 0.12), (-0.07, 0.22), (0.17, 0.09), (0.29, 0.21), (0.03, -0.20)):
        ax.plot(
            [qx, qx + 0.36 * w * dx],
            [qy, qy + 0.36 * w * dy],
            color="#C1847E",
            linewidth=0.32,
            zorder=6,
        )
    ax.add_patch(
        Circle(
            (qx, qy),
            0.045 * w,
            facecolor=COLORS["blue_fill"],
            edgecolor=COLORS["blue"],
            linewidth=0.55,
            zorder=9,
        )
    )
    ax.text(qx, qy, r"$q$", ha="center", va="center", fontsize=4.4, color=COLORS["blue_dark"], zorder=10)
    ax.text(
        x + 0.25 * w,
        y + 0.15 * h,
        "local dental samples",
        ha="center",
        va="center",
        fontsize=4.45,
        color=COLORS["muted"],
        zorder=8,
    )

    ax.text(
        x + 0.75 * w,
        y + 0.81 * h,
        r"Support $A(q;\hat O)$",
        ha="center",
        va="center",
        fontsize=5.0,
        fontweight="semibold",
        color=COLORS["blue_dark"],
        zorder=8,
    )
    sx, sy = x + 0.75 * w, y + 0.45 * h
    for dx, dy in ((-0.18, 0.0), (0.18, 0.0), (0.0, -0.17), (0.0, 0.17)):
        ax.add_patch(
            Rectangle(
                (sx + dx * w - 0.035 * w, sy + dy * w - 0.035 * w),
                0.07 * w,
                0.07 * w,
                facecolor=COLORS["white"],
                edgecolor="#75A1BC",
                linewidth=0.34,
                zorder=7,
            )
        )
        ax.plot([sx, sx + dx * w], [sy, sy + dy * w], color="#8AB5CC", linewidth=0.32, zorder=6)
    ax.add_patch(
        Rectangle(
            (sx - 0.042 * w, sy - 0.042 * w),
            0.084 * w,
            0.084 * w,
            facecolor=COLORS["blue"],
            edgecolor=COLORS["blue_dark"],
            linewidth=0.38,
            zorder=9,
        )
    )
    ax.text(
        x + 0.75 * w,
        y + 0.15 * h,
        "sparse axial context",
        ha="center",
        va="center",
        fontsize=4.45,
        color=COLORS["muted"],
        zorder=8,
    )


def draw_feature_dit(ax, x, y, w, h):
    rounded_box(ax, x, y, w, h, fc=COLORS["blue_fill"], ec=COLORS["blue"], lw=0.95, radius=0.08)
    ax.text(
        x + w / 2,
        y + 0.80 * h,
        "Sparse Feature DiT",
        ha="center",
        va="center",
        fontsize=6.0,
        fontweight="semibold",
        zorder=8,
    )
    rng = np.random.default_rng(24)
    ax.scatter(
        x + 0.12 * w + rng.random(18) * 0.23 * w,
        y + 0.23 * h + rng.random(18) * 0.30 * h,
        s=3.0 + rng.random(18) * 2.5,
        color=COLORS["blue"],
        alpha=0.78,
        linewidths=0,
        zorder=7,
    )
    for index in range(3):
        rounded_box(
            ax,
            x + (0.43 + 0.027 * index) * w,
            y + (0.23 + 0.027 * index) * h,
            0.22 * w,
            0.25 * h,
            fc=COLORS["white"],
            ec=COLORS["blue"],
            lw=0.42,
            radius=0.025,
            zorder=6 + index,
        )
    arrow(
        ax,
        (x + 0.31 * w, y + 0.35 * h),
        (x + 0.40 * w, y + 0.35 * h),
        color=COLORS["blue"],
        lw=0.65,
        mutation_scale=4.6,
    )
    arrow(
        ax,
        (x + 0.70 * w, y + 0.35 * h),
        (x + 0.79 * w, y + 0.35 * h),
        color=COLORS["blue"],
        lw=0.65,
        mutation_scale=4.6,
    )
    ax.text(
        x + w / 2,
        y + 0.12 * h,
        r"Feature update at $q$",
        ha="center",
        va="center",
        fontsize=4.8,
        color=COLORS["blue_dark"],
        zorder=8,
    )


def build_figure():
    fig, ax = plt.subplots(figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 7.2)
    ax.set_aspect("equal")
    ax.axis("off")

    panel(
        ax,
        0.28,
        0.35,
        6.55,
        6.45,
        "Case-aligned query coordinate",
        "a",
        fill="#F8FAFB",
        edge="#B8C8D2",
    )
    panel(
        ax,
        7.08,
        0.35,
        16.64,
        6.45,
        "Coordinate-wise multi-scale conditioning for Feature Flow",
        "b",
        fill="#FBFAFD",
        edge="#D8CEE5",
    )

    draw_case_context(ax, 0.72, 1.35, 3.72, 4.32)
    rounded_box(
        ax,
        4.74,
        2.06,
        1.35,
        2.36,
        fc=COLORS["blue_fill"],
        ec="#9DBCCE",
        radius=0.06,
        zorder=7,
    )
    ax.text(
        5.42,
        4.04,
        r"$q\in\hat O$",
        ha="center",
        va="center",
        fontsize=5.6,
        fontweight="semibold",
        color=COLORS["blue_dark"],
        zorder=9,
    )
    q_grid_x, q_grid_y = 4.94, 2.48
    for row in range(3):
        for col in range(3):
            ax.add_patch(
                Rectangle(
                    (q_grid_x + col * 0.27, q_grid_y + row * 0.27),
                    0.25,
                    0.25,
                    facecolor=COLORS["blue"] if (row, col) == (1, 1) else COLORS["white"],
                    edgecolor="#8FADBF",
                    linewidth=0.25,
                    zorder=8,
                )
            )
    arrow(ax, (4.42, 3.30), (4.72, 3.30), color=COLORS["blue"], lw=0.9, mutation_scale=5.8)
    ax.text(
        3.52,
        1.00,
        "Upper jaw  |  Lower jaw  |  Margin  |  FDI",
        ha="center",
        va="center",
        fontsize=5.0,
        color=COLORS["muted"],
        zorder=8,
    )

    draw_global_voxel_group(ax, 7.62, 4.22, 5.12, 1.58)
    draw_local_support_group(ax, 7.62, 2.10, 5.12, 1.58)

    rounded_box(
        ax,
        13.14,
        4.55,
        2.06,
        0.92,
        "Cross-attention\ntokens",
        fc=COLORS["purple_fill"],
        ec="#A793C3",
        fontsize=4.9,
        weight="semibold",
        radius=0.06,
        color=COLORS["purple_dark"],
        zorder=7,
    )
    rounded_box(
        ax,
        13.14,
        2.42,
        2.06,
        0.92,
        "Feature token\nat $q$",
        fc=COLORS["blue_fill"],
        ec="#9DBCCE",
        fontsize=4.9,
        weight="semibold",
        radius=0.06,
        color=COLORS["blue_dark"],
        zorder=7,
    )
    draw_feature_dit(ax, 15.86, 2.18, 3.12, 2.78)
    rounded_box(
        ax,
        19.63,
        2.92,
        3.00,
        1.30,
        r"$\hat F_q$",
        fc=COLORS["white"],
        ec="#8FB2C8",
        fontsize=7.2,
        weight="semibold",
        radius=0.06,
        color=COLORS["blue_dark"],
        zorder=7,
    )
    for offset, color in enumerate(("#5E91B7", "#66A392", "#D39A52", "#8467AD")):
        ax.add_patch(
            Rectangle(
                (21.50 + offset * 0.15, 3.20),
                0.08,
                0.38,
                facecolor=color,
                edgecolor="none",
                zorder=8,
            )
        )

    # Global/voxel features supply both cross-attention tokens and a residual
    # conditioning path; dental and support cues update the sparse feature token.
    arrow(
        ax,
        (12.76, 5.01),
        (13.12, 5.01),
        color=COLORS["purple"],
        lw=0.92,
        style=CONDITION_STYLE,
        mutation_scale=5.8,
    )
    poly_arrow(
        ax,
        [(12.76, 4.76), (12.96, 4.76), (12.96, 3.86), (14.17, 3.86), (14.17, 3.36)],
        color=COLORS["purple"],
        lw=0.72,
        style=CONDITION_STYLE,
        mutation_scale=5.0,
        zorder=5.8,
    )
    ax.text(
        13.54,
        4.03,
        "residual",
        ha="center",
        va="center",
        fontsize=4.25,
        color=COLORS["purple_dark"],
        zorder=8,
    )
    arrow(
        ax,
        (12.76, 3.05),
        (13.12, 2.98),
        color=COLORS["purple"],
        lw=0.88,
        style=CONDITION_STYLE,
        mutation_scale=5.6,
    )
    arrow(
        ax,
        (12.76, 2.55),
        (13.12, 2.76),
        color=COLORS["blue"],
        lw=0.95,
        mutation_scale=5.8,
    )
    poly_arrow(
        ax,
        [(15.22, 5.01), (15.54, 5.01), (15.54, 4.42), (15.84, 4.42)],
        color=COLORS["purple"],
        lw=0.88,
        style=CONDITION_STYLE,
        mutation_scale=5.6,
    )
    arrow(
        ax,
        (15.22, 2.88),
        (15.84, 3.34),
        color=COLORS["blue"],
        lw=1.0,
        mutation_scale=6.1,
    )
    arrow(
        ax,
        (19.00, 3.58),
        (19.61, 3.58),
        color=COLORS["blue"],
        lw=1.1,
        mutation_scale=6.6,
    )

    rounded_box(
        ax,
        7.82,
        1.10,
        3.20,
        0.50,
        r"Structure: $C_S^g,\ C_{S,16}^v$",
        fc=COLORS["white"],
        ec="#B8A6CC",
        fontsize=4.9,
        weight="semibold",
        radius=0.035,
        color=COLORS["purple_dark"],
        zorder=8,
    )
    rounded_box(
        ax,
        11.26,
        1.10,
        4.85,
        0.50,
        r"Feature: $C_F^g,\ C_{F,16}^v,\ C_{F,64}^v(q),\ C_F^n(q),\ A(q;\hat O)$",
        fc=COLORS["white"],
        ec="#A6C4D5",
        fontsize=4.0,
        weight="semibold",
        radius=0.035,
        color=COLORS["blue_dark"],
        zorder=8,
    )

    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    for extension, kwargs in {"png": {"dpi": 600}, "pdf": {}, "svg": {}}.items():
        fig.savefig(
            ROOT / f"feature_condition_detail.{extension}",
            facecolor=COLORS["white"],
            edgecolor="none",
            metadata={"Title": "Coordinate-wise multi-scale conditioning for Feature Flow"},
            **kwargs,
        )
    plt.close(fig)


if __name__ == "__main__":
    build_figure()
