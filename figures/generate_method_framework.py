#!/usr/bin/env python3
"""Generate the publication framework figure for crown-shape generation."""

from pathlib import Path
import warnings

import matplotlib as mpl
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

mpl.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "assets" / "method_framework"
ASSET_PATHS = {
    "scans": ASSET_DIR / "scans.png",
    "margin": ASSET_DIR / "margin.png",
    "reference_cad": ASSET_DIR / "reference_cad.png",
    "reconstructed_mesh": ASSET_DIR / "reconstructed_mesh.png",
    "crown_mesh": ASSET_DIR / "crown_mesh.png",
}
FIG_WIDTH_IN = 180.0 / 25.4
FIG_HEIGHT_IN = 79.0 / 25.4

COLORS = {
    "ink": "#24313C",
    "muted": "#687681",
    "line": "#D7DFE5",
    "blue": "#2E729F",
    "blue_dark": "#1F567A",
    "blue_fill": "#EAF3F8",
    "blue_band": "#F7FAFC",
    "purple": "#7355A4",
    "purple_dark": "#574078",
    "purple_fill": "#F2EEF8",
    "purple_band": "#FBFAFD",
    "orange": "#C96E29",
    "orange_dark": "#945021",
    "orange_fill": "#FAF0E7",
    "orange_band": "#FDFBF9",
    "gray": "#7A8790",
    "gray_fill": "#F0F3F5",
    "teal": "#4E8F82",
    "green": "#4D8B6A",
    "white": "#FFFFFF",
}

TRAIN_STYLE = (0, (4, 2.5))
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
    fontsize=6.2,
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
            linespacing=1.04,
            zorder=zorder + 1,
        )
    return patch


def place_png(ax, path, x, y, w, h, *, zorder=7):
    """Place a tightly cropped PNG while preserving its aspect ratio."""
    path = Path(path)
    if not path.is_file():
        return False
    try:
        image = plt.imread(path)
    except (OSError, ValueError) as exc:
        warnings.warn(f"Unable to load figure asset {path}: {exc}")
        return False
    if image.ndim not in (2, 3) or image.shape[0] == 0 or image.shape[1] == 0:
        warnings.warn(f"Invalid figure asset shape for {path}: {image.shape}")
        return False
    if image.ndim == 3 and image.shape[2] == 4:
        visible = image[:, :, 3] > 0.01
        if visible.any():
            rows, cols = np.where(visible)
            image = image[rows.min() : rows.max() + 1, cols.min() : cols.max() + 1]
    image_ratio = image.shape[1] / image.shape[0]
    slot_ratio = w / h
    if image_ratio >= slot_ratio:
        draw_w = w
        draw_h = w / image_ratio
    else:
        draw_h = h
        draw_w = h * image_ratio
    draw_x = x + (w - draw_w) / 2
    draw_y = y + (h - draw_h) / 2
    ax.imshow(
        image,
        extent=(draw_x, draw_x + draw_w, draw_y, draw_y + draw_h),
        interpolation="lanczos",
        zorder=zorder,
    )
    return True


def arrow(
    ax,
    start,
    end,
    *,
    color=COLORS["blue"],
    lw=1.15,
    style="-",
    mutation_scale=7,
    zorder=6,
    connectionstyle="arc3,rad=0",
):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        linewidth=lw,
        linestyle=style,
        color=color,
        shrinkA=1,
        shrinkB=1,
        connectionstyle=connectionstyle,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def poly_arrow(ax, points, *, color, lw=1.0, style="-", mutation_scale=7, zorder=5):
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


def lane_title(ax, y, title, color):
    ax.plot(
        [0.62, 1.03],
        [y + 0.12, y + 0.12],
        color=color,
        lw=1.8,
        solid_capstyle="butt",
    )
    ax.text(
        0.62,
        y - 0.22,
        title,
        ha="left",
        va="center",
        fontsize=7.0,
        fontweight="semibold",
        linespacing=1.02,
    )


def molar_outline(x, y, w, h):
    points = np.array(
        [
            [0.08, 0.12],
            [0.03, 0.34],
            [0.10, 0.65],
            [0.23, 0.91],
            [0.36, 0.75],
            [0.48, 0.98],
            [0.60, 0.76],
            [0.74, 0.91],
            [0.89, 0.65],
            [0.97, 0.35],
            [0.91, 0.12],
            [0.70, 0.05],
            [0.34, 0.05],
        ]
    )
    points[:, 0] = x + points[:, 0] * w
    points[:, 1] = y + points[:, 1] * h
    return points


def draw_molar(ax, x, y, w, h, *, fc, ec, mesh=True, alpha=1.0, zorder=6):
    patch = Polygon(
        molar_outline(x, y, w, h),
        closed=True,
        facecolor=fc,
        edgecolor=ec,
        linewidth=0.75,
        alpha=alpha,
        zorder=zorder,
    )
    ax.add_patch(patch)
    if not mesh:
        return
    for frac, tilt in ((0.28, 0.05), (0.47, -0.02), (0.66, 0.04)):
        ax.plot(
            [x + 0.14 * w, x + 0.88 * w],
            [y + frac * h, y + (frac + tilt) * h],
            color=ec,
            linewidth=0.35,
            alpha=0.74 * alpha,
            zorder=zorder + 1,
        )
    for frac in (0.25, 0.43, 0.62, 0.80):
        ax.plot(
            [x + frac * w, x + (frac - 0.06) * w],
            [y + 0.10 * h, y + 0.77 * h],
            color=ec,
            linewidth=0.32,
            alpha=0.72 * alpha,
            zorder=zorder + 1,
        )
    ax.plot(
        [x + 0.30 * w, x + 0.48 * w, x + 0.67 * w],
        [y + 0.64 * h, y + 0.50 * h, y + 0.66 * h],
        color=ec,
        linewidth=0.48,
        alpha=0.9 * alpha,
        zorder=zorder + 2,
    )


def draw_reference_cad(ax, x, y, w, h, asset=ASSET_PATHS["reference_cad"]):
    rounded_box(ax, x, y, w, h, fc=COLORS["white"], ec="#DDBA9B", lw=0.7)
    ax.text(
        x + w / 2,
        y + 0.82 * h,
        "CAD",
        ha="center",
        va="center",
        fontsize=6.4,
        fontweight="semibold",
        zorder=8,
    )
    if not place_png(
        ax,
        asset,
        x + 0.12 * w,
        y + 0.11 * h,
        0.76 * w,
        0.59 * h,
        zorder=7,
    ):
        draw_molar(
            ax,
            x + 0.20 * w,
            y + 0.14 * h,
            0.60 * w,
            0.54 * h,
            fc="#E3B37F",
            ec="#805C3F",
        )


def draw_fdg(ax, x, y, w, h, label="Oriented\nsigned FDG"):
    rounded_box(ax, x, y, w, h, fc=COLORS["white"], ec="#DDBA9B", lw=0.7)
    ax.text(
        x + w / 2,
        y + 0.84 * h,
        label,
        ha="center",
        va="center",
        fontsize=5.2,
        fontweight="semibold",
        zorder=8,
    )
    fx, fy = x + 0.22 * w, y + 0.18 * h
    fw, fh, dx, dy = 0.46 * w, 0.42 * h, 0.13 * w, 0.10 * h
    front = np.array(
        [[fx, fy], [fx + fw, fy], [fx + fw, fy + fh], [fx, fy + fh]]
    )
    top = np.array(
        [front[3], front[2], front[2] + [dx, dy], front[3] + [dx, dy]]
    )
    side = np.array(
        [front[1], front[2], front[2] + [dx, dy], front[1] + [dx, dy]]
    )
    ax.add_patch(
        Polygon(
            front,
            closed=True,
            fc="#FBFCFD",
            ec="#8FA2B0",
            lw=0.55,
            zorder=5,
        )
    )
    ax.add_patch(
        Polygon(
            top,
            closed=True,
            fc="#F1F5F7",
            ec="#8FA2B0",
            lw=0.55,
            zorder=4,
        )
    )
    ax.add_patch(
        Polygon(
            side,
            closed=True,
            fc="#E8EFF3",
            ec="#8FA2B0",
            lw=0.55,
            zorder=4,
        )
    )
    for k in range(1, 4):
        ax.plot(
            [fx + k * fw / 4] * 2,
            [fy, fy + fh],
            color="#B8C3CB",
            lw=0.3,
            zorder=6,
        )
        ax.plot(
            [fx, fx + fw],
            [fy + k * fh / 4] * 2,
            color="#B8C3CB",
            lw=0.3,
            zorder=6,
        )
    for a, b in ((0, 2), (1, 1), (2, 0), (2, 2), (3, 1)):
        ax.add_patch(
            Rectangle(
                (fx + a * fw / 4 + 0.012, fy + b * fh / 4 + 0.012),
                fw / 4 - 0.024,
                fh / 4 - 0.024,
                facecolor="#E5A26A",
                edgecolor="#AD6A36",
                linewidth=0.2,
                zorder=7,
            )
        )
    arrow(
        ax,
        (x + 0.54 * w, y + 0.48 * h),
        (x + 0.65 * w, y + 0.62 * h),
        color=COLORS["purple"],
        lw=0.55,
        mutation_scale=4.5,
    )


def draw_vae(
    ax,
    x,
    y,
    w,
    h,
    label,
    *,
    frozen=False,
    decode=False,
    training=False,
    fontsize=6.4,
    linespacing=1.02,
):
    if training:
        fc, ec = COLORS["orange_fill"], COLORS["orange"]
    elif frozen:
        fc, ec = COLORS["gray_fill"], COLORS["gray"]
    elif decode:
        fc, ec = COLORS["blue_fill"], COLORS["blue"]
    else:
        fc, ec = COLORS["orange_fill"], COLORS["orange"]
    if decode:
        pts = np.array(
            [[x, y + 0.18 * h], [x, y + 0.82 * h], [x + w, y + h], [x + w, y]]
        )
    else:
        pts = np.array(
            [[x, y], [x, y + h], [x + w, y + 0.82 * h], [x + w, y + 0.18 * h]]
        )
    ax.add_patch(
        Polygon(
            pts,
            closed=True,
            facecolor=fc,
            edgecolor=ec,
            linewidth=0.8,
            zorder=5,
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        label,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="semibold",
        linespacing=linespacing,
        zorder=7,
    )


def draw_latent(ax, x, y, w, h):
    rounded_box(ax, x, y, w, h, fc=COLORS["white"], ec="#AEC3D1", lw=0.75)
    ax.text(
        x + w / 2,
        y + 0.84 * h,
        r"$Z=(O,F)$",
        ha="center",
        va="center",
        fontsize=5.8,
        fontweight="semibold",
        zorder=8,
    )
    rng = np.random.default_rng(8)
    xx = x + 0.12 * w + rng.random(18) * 0.34 * w
    yy = y + 0.18 * h + rng.random(18) * 0.47 * h
    ax.scatter(
        xx,
        yy,
        s=4.6,
        color="#6599BD",
        alpha=0.9,
        linewidths=0,
        zorder=7,
    )
    for idx, color in enumerate(
        ("#5E91B7", "#66A392", "#D39A52", "#8467AD")
    ):
        ax.add_patch(
            Rectangle(
                (x + (0.61 + idx * 0.07) * w, y + 0.19 * h),
                0.038 * w,
                0.46 * h,
                facecolor=color,
                edgecolor="none",
                zorder=7,
            )
        )


def draw_flow(ax, x, y, w, h, title, subtitle, *, feature=False):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        fc=COLORS["blue_fill"],
        ec=COLORS["blue"],
        lw=0.95,
        radius=0.08,
    )
    ax.text(
        x + w / 2,
        y + 0.82 * h,
        title,
        ha="center",
        va="center",
        fontsize=6.3,
        fontweight="semibold",
        zorder=8,
    )
    if subtitle:
        ax.text(
            x + w / 2,
            y + 0.62 * h,
            subtitle,
            ha="center",
            va="center",
            fontsize=5.8,
            color=COLORS["blue_dark"],
            zorder=8,
        )
    rng = np.random.default_rng(17 if feature else 19)
    ax.scatter(
        x + 0.10 * w + rng.random(15) * 0.16 * w,
        y + 0.20 * h + rng.random(15) * 0.24 * h,
        s=3.8 + rng.random(15) * 2.0,
        color=COLORS["blue"],
        alpha=0.65,
        linewidths=0,
        zorder=7,
    )
    arrow(
        ax,
        (x + 0.30 * w, y + 0.31 * h),
        (x + 0.39 * w, y + 0.31 * h),
        color=COLORS["blue"],
        lw=0.65,
        mutation_scale=4.8,
    )
    for idx in range(3):
        rounded_box(
            ax,
            x + (0.42 + 0.025 * idx) * w,
            y + (0.18 + 0.025 * idx) * h,
            0.25 * w,
            0.28 * h,
            fc=COLORS["white"],
            ec=COLORS["blue"],
            lw=0.42,
            radius=0.025,
            zorder=6 + idx,
        )
    arrow(
        ax,
        (x + 0.72 * w, y + 0.31 * h),
        (x + 0.80 * w, y + 0.31 * h),
        color=COLORS["blue"],
        lw=0.65,
        mutation_scale=4.8,
    )
    if feature:
        for idx, color in enumerate(("#5E91B7", "#66A392", "#D39A52")):
            ax.add_patch(
                Rectangle(
                    (x + (0.83 + idx * 0.035) * w, y + 0.20 * h),
                    0.022 * w,
                    0.24 * h,
                    facecolor=color,
                    edgecolor="none",
                    zorder=8,
                )
            )
    else:
        for cx, cy in (
            (0.84, 0.23),
            (0.88, 0.34),
            (0.92, 0.24),
            (0.94, 0.39),
        ):
            ax.add_patch(
                Rectangle(
                    (x + cx * w, y + cy * h),
                    0.022 * w,
                    0.035 * h,
                    facecolor=COLORS["blue"],
                    edgecolor="none",
                    zorder=8,
                )
            )


def draw_support(ax, x, y, w, h):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        fc=COLORS["white"],
        ec="#AAC1D0",
        lw=0.7,
        radius=0.055,
    )
    rng = np.random.default_rng(31)
    ax.scatter(
        x + 0.18 * w + rng.random(21) * 0.64 * w,
        y + 0.30 * h + rng.random(21) * 0.46 * h,
        s=4.3,
        color="#5E91B7",
        alpha=0.9,
        linewidths=0,
        zorder=7,
    )
    ax.text(
        x + w / 2,
        y + 0.13 * h,
        r"$\hat O$",
        ha="center",
        va="center",
        fontsize=6.4,
        zorder=8,
    )


def draw_reconstruction(ax, x, y, w, h):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        fc=COLORS["white"],
        ec="#91B2C8",
        lw=0.85,
        radius=0.07,
    )
    ax.text(
        x + w / 2,
        y + 0.84 * h,
        "Oriented-field\nreconstruction",
        ha="center",
        va="center",
        fontsize=6.1,
        fontweight="semibold",
        zorder=8,
    )
    centers = [x + 0.19 * w, x + 0.51 * w, x + 0.82 * w]
    t = np.linspace(-1, 1, 80)
    ax.plot(
        centers[0] + 0.10 * w * t,
        y + 0.50 * h + 0.055 * h * np.sin(2.7 * t),
        color=COLORS["blue"],
        lw=0.65,
        zorder=7,
    )
    for frac in (-0.55, 0.0, 0.55):
        sx = centers[0] + frac * 0.10 * w
        sy = y + 0.50 * h + 0.055 * h * np.sin(2.7 * frac)
        arrow(
            ax,
            (sx, sy),
            (sx, sy + 0.11 * h),
            color=COLORS["purple"],
            lw=0.48,
            mutation_scale=4.2,
        )
    for offset in (-0.055, 0.0, 0.055):
        ax.plot(
            centers[1] + 0.09 * w * t,
            y + 0.50 * h + offset * h + 0.04 * h * np.sin(2.2 * t),
            color="#729EBC",
            lw=0.48,
            alpha=0.9,
            zorder=7,
        )
    mesh_x, mesh_y = centers[2], y + 0.50 * h
    angles = np.linspace(0, 2 * np.pi, 9, endpoint=False)
    px = mesh_x + 0.105 * w * np.cos(angles)
    py = mesh_y + 0.105 * h * np.sin(angles)
    for idx in range(len(px)):
        ax.plot(
            [px[idx], px[(idx + 1) % len(px)]],
            [py[idx], py[(idx + 1) % len(py)]],
            color=COLORS["blue_dark"],
            lw=0.48,
            zorder=7,
        )
        ax.plot(
            [mesh_x, px[idx]],
            [mesh_y, py[idx]],
            color=COLORS["blue_dark"],
            lw=0.34,
            zorder=7,
        )
    arrow(
        ax,
        (x + 0.30 * w, y + 0.50 * h),
        (x + 0.39 * w, y + 0.50 * h),
        lw=0.62,
        mutation_scale=4.8,
    )
    arrow(
        ax,
        (x + 0.62 * w, y + 0.50 * h),
        (x + 0.70 * w, y + 0.50 * h),
        lw=0.62,
        mutation_scale=4.8,
    )
    for xpos, label in zip(centers, ("field", "zero-set", "mesh")):
        ax.text(
            xpos,
            y + 0.17 * h,
            label,
            ha="center",
            va="center",
            fontsize=5.8,
            color=COLORS["muted"],
            zorder=8,
        )


def draw_output(ax, x, y, w, h, *, title="Crown\nmesh", qc=True, asset=None):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        fc="#F1F7FA",
        ec="#79A5C0",
        lw=0.95,
        radius=0.08,
    )
    ax.text(
        x + w / 2,
        y + 0.84 * h,
        title,
        ha="center",
        va="center",
        fontsize=6.1,
        fontweight="semibold",
        zorder=8,
    )
    if asset is None or not place_png(
        ax,
        asset,
        x + 0.08 * w,
        y + 0.10 * h,
        0.84 * w,
        0.66 * h,
        zorder=7,
    ):
        draw_molar(
            ax,
            x + 0.05 * w,
            y + 0.15 * h,
            0.64 * w,
            0.60 * h,
            fc="#BCD7E7",
            ec=COLORS["blue_dark"],
            mesh=True,
            zorder=7,
        )
    if qc:
        badge = Circle(
            (x + 0.82 * w, y + 0.23 * h),
            0.090 * h,
            facecolor=COLORS["white"],
            edgecolor=COLORS["green"],
            linewidth=0.8,
            zorder=9,
        )
        ax.add_patch(badge)
        ax.text(
            x + 0.82 * w,
            y + 0.23 * h,
            "QC",
            ha="center",
            va="center",
            fontsize=5.2,
            fontweight="bold",
            color=COLORS["green"],
            zorder=10,
        )


def draw_case_inputs(ax, x, y, w, h):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        fc=COLORS["white"],
        ec="#AA99C1",
        lw=0.8,
        radius=0.07,
    )
    ax.text(
        x + w / 2,
        y + 0.85 * h,
        "Inputs",
        ha="center",
        va="center",
        fontsize=6.4,
        fontweight="semibold",
        zorder=8,
    )
    if not place_png(
        ax,
        ASSET_PATHS["scans"],
        x + 0.02 * w,
        y + 0.20 * h,
        0.42 * w,
        0.52 * h,
        zorder=7,
    ):
        theta = np.linspace(0.16 * np.pi, 0.84 * np.pi, 16)
        for offset, color in ((0.08, COLORS["teal"]), (-0.05, "#8BA9A1")):
            xx = x + 0.25 * w + 0.14 * w * np.cos(theta)
            yy = y + 0.43 * h + offset + 0.17 * h * np.sin(theta)
            ax.scatter(
                xx,
                yy,
                s=4.8,
                c=color,
                edgecolors=COLORS["white"],
                linewidths=0.22,
                zorder=7,
            )
    if not place_png(
        ax,
        ASSET_PATHS["margin"],
        x + 0.47 * w,
        y + 0.25 * h,
        0.28 * w,
        0.45 * h,
        zorder=7,
    ):
        t = np.linspace(0, 2 * np.pi, 100)
        rr = 1 + 0.10 * np.cos(5 * t)
        mx = x + 0.61 * w + 0.085 * w * rr * np.cos(t)
        my = y + 0.48 * h + 0.18 * h * rr * np.sin(t)
        ax.plot(mx, my, color=COLORS["purple"], lw=1.0, zorder=7)
    rounded_box(
        ax,
        x + 0.77 * w,
        y + 0.33 * h,
        0.18 * w,
        0.29 * h,
        "FDI",
        fc="#FBF8EE",
        ec="#C8B98C",
        fontsize=5.2,
        weight="semibold",
        radius=0.035,
        zorder=6,
    )
    ax.text(
        x + 0.215 * w,
        y + 0.105 * h,
        "Scans",
        ha="center",
        va="center",
        fontsize=5.2,
        color=COLORS["muted"],
        zorder=8,
    )
    ax.text(
        x + 0.62 * w,
        y + 0.105 * h,
        "Margin",
        ha="center",
        va="center",
        fontsize=5.2,
        color=COLORS["muted"],
        zorder=8,
    )


def draw_condition_encoder(ax, x, y, w, h, title, channels):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        fc=COLORS["purple_fill"],
        ec="#9E88BA",
        lw=0.85,
        radius=0.07,
    )
    ax.text(
        x + w / 2,
        y + 0.75 * h,
        title,
        ha="center",
        va="center",
        fontsize=6.4,
        fontweight="semibold",
        zorder=8,
    )
    chip_w = 0.24 * w
    total = len(channels) * chip_w + (len(channels) - 1) * 0.04 * w
    start = x + (w - total) / 2
    for idx, channel in enumerate(channels):
        rounded_box(
            ax,
            start + idx * (chip_w + 0.04 * w),
            y + 0.18 * h,
            chip_w,
            0.28 * h,
            channel,
            fc=COLORS["white"],
            ec="#B8A6CC",
            fontsize=6.2,
            weight="semibold",
            radius=0.035,
            color=COLORS["purple_dark"],
            zorder=7,
        )


def loss_node(ax, x, y, text, width=0.64):
    rounded_box(
        ax,
        x - width / 2,
        y,
        width,
        0.42,
        text,
        fc=COLORS["orange_fill"],
        ec=COLORS["orange"],
        lw=0.8,
        fontsize=6.4,
        weight="semibold",
        radius=0.04,
        color=COLORS["orange_dark"],
        zorder=8,
    )


def section_tab(ax, x, y, w, text, *, color, fill):
    """Draw a compact section label without creating a title column."""
    rounded_box(
        ax,
        x,
        y,
        w,
        0.42,
        fc=fill,
        ec=color,
        lw=0.7,
        radius=0.045,
        zorder=8,
    )
    ax.add_patch(
        Rectangle(
            (x, y),
            0.08,
            0.42,
            facecolor=color,
            edgecolor="none",
            zorder=9,
        )
    )
    ax.text(
        x + 0.19,
        y + 0.21,
        text,
        ha="left",
        va="center",
        fontsize=6.7,
        fontweight="semibold",
        color=COLORS["ink"],
        zorder=10,
    )


def panel_background(
    ax,
    x,
    y,
    w,
    h,
    title,
    *,
    fill,
    edge,
    label=None,
    title_size=7.0,
    title_x=0.20,
    title_y_offset=0.36,
):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        facecolor=fill,
        edgecolor=edge,
        linewidth=0.72,
        zorder=0,
    )
    ax.add_patch(patch)
    title_y = y + h - title_y_offset
    if label:
        ax.text(
            x + title_x,
            title_y,
            f"({label})",
            ha="left",
            va="center",
            fontsize=title_size + 0.1,
            fontweight="bold",
            color=COLORS["ink"],
            zorder=10,
        )
    title_left = x + title_x + 0.52 if label else x + title_x
    ax.text(
        title_left,
        title_y,
        title,
        ha="left",
        va="center",
        fontsize=title_size,
        fontweight="semibold",
        color=COLORS["ink"],
        zorder=10,
    )
    return patch


def draw_noise(ax, x, y, w, h, label="Noise"):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        fc=COLORS["white"],
        ec="#A8C0D0",
        lw=0.75,
        radius=0.055,
    )
    rng = np.random.default_rng(43)
    ax.scatter(
        x + 0.18 * w + rng.random(28) * 0.64 * w,
        y + 0.28 * h + rng.random(28) * 0.50 * h,
        s=3.5 + rng.random(28) * 2.3,
        c=rng.choice(("#5E91B7", "#8B6CB0", "#67A293"), 28),
        alpha=0.82,
        linewidths=0,
        zorder=7,
    )
    ax.text(
        x + w / 2,
        y + 0.12 * h,
        label,
        ha="center",
        va="center",
        fontsize=5.0 if "\n" in label else 5.7,
        color=COLORS["muted"],
        linespacing=0.92,
        zorder=8,
    )


def draw_qc_gate(ax, x, y, w, h):
    rounded_box(
        ax,
        x,
        y,
        w,
        h,
        "QC\nstatus",
        fc="#F1F7F3",
        ec=COLORS["green"],
        lw=0.9,
        fontsize=6.1,
        weight="semibold",
        radius=0.055,
        color=COLORS["green"],
        zorder=7,
    )


def build_figure():
    fig, ax = plt.subplots(figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))
    ax.set_xlim(0, 24)
    ax.set_ylim(1.10, 11.63)
    ax.set_aspect("equal")
    ax.axis("off")

    # The layout follows the common organization used by structured-mesh
    # generation papers: conditioner and representation learning above, then
    # a complete left-to-right generation path below.
    panel_background(
        ax,
        0.38,
        7.35,
        8.75,
        4.02,
        "Multi-scale dental conditioner",
        fill="#FAF8FC",
        edge="#D8CEE5",
        label="a",
    )
    panel_background(
        ax,
        9.35,
        7.35,
        14.27,
        4.02,
        "Oriented signed FDG representation learning",
        fill="#FDF9F5",
        edge="#E7D5C6",
        label="b",
    )
    panel_background(
        ax,
        0.25,
        1.35,
        23.50,
        5.85,
        "Case-conditioned crown generation",
        fill=COLORS["white"],
        edge="#B8C6CF",
        label="c",
    )
    panel_background(
        ax,
        0.38,
        1.55,
        7.45,
        5.00,
        "Structure generation",
        fill="#F7F4FA",
        edge="#D8CEE5",
        title_size=6.4,
        title_x=0.18,
        title_y_offset=0.34,
    )
    panel_background(
        ax,
        8.03,
        1.55,
        4.35,
        5.00,
        "Feature generation",
        fill="#F3F8FB",
        edge="#C9DBE6",
        title_size=6.4,
        title_x=0.18,
        title_y_offset=0.34,
    )
    panel_background(
        ax,
        12.58,
        1.55,
        11.04,
        5.00,
        "Latent decoding and mesh reconstruction",
        fill="#F8FAFB",
        edge="#D3DDE3",
        title_size=6.4,
        title_x=0.18,
        title_y_offset=0.34,
    )

    # (a) Case inputs are aligned once and encoded for the two generation stages.
    draw_case_inputs(ax, 0.70, 8.10, 2.05, 1.92)
    rounded_box(
        ax,
        2.99,
        8.43,
        1.24,
        1.25,
        "Align &\nsample",
        fc=COLORS["white"],
        ec="#A99AC0",
        fontsize=6.2,
        weight="semibold",
        radius=0.055,
    )
    draw_condition_encoder(
        ax,
        4.48,
        8.60,
        1.95,
        1.52,
        "Structure\ncondition",
        ("G", "V"),
    )
    draw_condition_encoder(
        ax,
        6.68,
        8.60,
        1.95,
        1.52,
        "Feature\ncondition",
        ("G", "V"),
    )
    arrow(
        ax,
        (2.78, 9.06),
        (3.01, 9.06),
        color=COLORS["purple"],
        lw=1.0,
        mutation_scale=6.2,
    )
    # Use separate output ports so the two conditioner paths remain distinct
    # after the Align & sample stage at final print scale.
    arrow(
        ax,
        (4.26, 9.36),
        (4.45, 9.36),
        color=COLORS["purple"],
        lw=0.95,
        style=CONDITION_STYLE,
        mutation_scale=5.8,
        zorder=5,
    )
    poly_arrow(
        ax,
        [
            (4.26, 9.56),
            (4.37, 9.56),
            (4.37, 10.34),
            (6.55, 10.34),
            (6.55, 9.36),
            (6.65, 9.36),
        ],
        color=COLORS["purple"],
        lw=0.95,
        style=CONDITION_STYLE,
        mutation_scale=5.8,
        zorder=5,
    )

    # (b) The trainable VAE learns a compact oriented signed FDG latent space.
    b_dx = 0.35
    draw_reference_cad(ax, 9.72 + b_dx, 8.20, 1.25, 1.66)
    draw_fdg(ax, 11.35 + b_dx, 8.20, 1.55, 1.66)
    draw_vae(ax, 13.28 + b_dx, 8.34, 1.05, 1.38, "VAE\nEnc.")
    draw_latent(ax, 14.72 + b_dx, 8.20, 1.45, 1.66)
    draw_vae(
        ax,
        16.55 + b_dx,
        8.34,
        1.05,
        1.38,
        "VAE\nDec.",
        decode=True,
        training=True,
    )
    draw_fdg(ax, 17.98 + b_dx, 8.20, 1.55, 1.66, "Recon.\nFDG")
    draw_output(
        ax,
        19.90 + b_dx,
        8.05,
        2.65,
        1.96,
        title="Reconstructed\nmesh",
        qc=False,
        asset=ASSET_PATHS["reconstructed_mesh"],
    )
    for start, end in (
        ((11.00 + b_dx, 9.03), (11.32 + b_dx, 9.03)),
        ((12.93 + b_dx, 9.03), (13.28 + b_dx, 9.03)),
        ((14.33 + b_dx, 9.03), (14.69 + b_dx, 9.03)),
        ((16.20 + b_dx, 9.03), (16.55 + b_dx, 9.03)),
        ((17.60 + b_dx, 9.03), (17.95 + b_dx, 9.03)),
        ((19.56 + b_dx, 9.03), (19.87 + b_dx, 9.03)),
    ):
        arrow(
            ax,
            start,
            end,
            color=COLORS["orange"],
            lw=1.05,
            style="-",
            mutation_scale=6.4,
        )
    rounded_box(
        ax,
        15.02 + b_dx,
        10.15,
        1.08,
        0.38,
        r"$L_{\mathrm{VAE}}$",
        fc=COLORS["orange_fill"],
        ec=COLORS["orange"],
        lw=0.75,
        fontsize=6.1,
        weight="semibold",
        radius=0.035,
        color=COLORS["orange_dark"],
        zorder=8,
    )
    ax.plot(
        [12.125 + b_dx, 12.125 + b_dx, 14.76 + b_dx],
        [9.89, 10.34, 10.34],
        color=COLORS["orange"],
        linewidth=0.82,
        linestyle=TRAIN_STYLE,
        zorder=6,
    )
    arrow(
        ax,
        (14.76 + b_dx, 10.34),
        (14.99 + b_dx, 10.34),
        color=COLORS["orange"],
        lw=0.82,
        style=TRAIN_STYLE,
        mutation_scale=5.0,
    )
    ax.plot(
        [18.755 + b_dx, 18.755 + b_dx, 16.34 + b_dx],
        [9.89, 10.34, 10.34],
        color=COLORS["orange"],
        linewidth=0.82,
        linestyle=TRAIN_STYLE,
        zorder=6,
    )
    arrow(
        ax,
        (16.34 + b_dx, 10.34),
        (16.13 + b_dx, 10.34),
        color=COLORS["orange"],
        lw=0.82,
        style=TRAIN_STYLE,
        mutation_scale=5.0,
    )
    arrow(
        ax,
        (15.445 + b_dx, 9.91),
        (15.445 + b_dx, 10.125),
        color=COLORS["orange"],
        lw=0.82,
        style=TRAIN_STYLE,
        mutation_scale=5.0,
    )

    # (c) Structure and feature flows generate the latent support and geometry.
    draw_noise(ax, 0.74, 2.53, 0.90, 1.58)
    draw_flow(ax, 1.95, 2.23, 2.75, 2.18, "Structure Flow", "sparse structure")
    rounded_box(
        ax,
        5.05,
        2.48,
        1.20,
        1.68,
        "Frozen\nS-Dec",
        fc=COLORS["gray_fill"],
        ec=COLORS["gray"],
        fontsize=6.2,
        weight="semibold",
        radius=0.055,
        color="#4F5A62",
    )
    draw_support(ax, 6.60, 2.48, 0.76, 1.68)
    draw_noise(ax, 8.30, 1.78, 0.78, 1.18, r"$\epsilon^F_{\hat O}$")
    draw_flow(
        ax,
        9.35,
        2.23,
        2.65,
        2.18,
        "Feature Flow",
        r"local geometry on $\hat O$",
        feature=True,
    )
    rounded_box(
        ax,
        12.25,
        2.86,
        0.80,
        0.92,
        r"$\hat Z$" + "\n" + r"$(\hat O,\hat F)$",
        fc=COLORS["white"],
        ec="#A9C2D2",
        fontsize=5.6,
        weight="semibold",
        radius=0.045,
        color=COLORS["blue_dark"],
        zorder=8,
    )
    draw_vae(
        ax,
        13.35,
        2.48,
        1.20,
        1.68,
        "Frozen\nVAE\nDecoder",
        frozen=True,
        decode=True,
        fontsize=5.5,
        linespacing=0.90,
    )
    draw_reconstruction(ax, 14.92, 2.08, 3.35, 2.48)
    draw_output(
        ax,
        18.72,
        1.98,
        2.70,
        2.68,
        title="Posterior crown\n3D mesh",
        qc=False,
        asset=ASSET_PATHS["crown_mesh"],
    )
    draw_qc_gate(ax, 22.07, 4.58, 1.10, 0.95)

    main_arrows = (
        ((1.67, 3.32), (1.92, 3.32)),
        ((4.73, 3.32), (5.02, 3.32)),
        ((6.28, 3.32), (6.57, 3.32)),
        ((7.39, 3.32), (9.32, 3.32)),
        ((12.03, 3.32), (12.22, 3.32)),
        ((13.08, 3.32), (13.35, 3.32)),
        ((14.55, 3.32), (14.89, 3.32)),
        ((18.30, 3.32), (18.69, 3.32)),
    )
    for start, end in main_arrows:
        arrow(
            ax,
            start,
            end,
            color=COLORS["blue"],
            lw=1.25,
            mutation_scale=7.2,
        )
    for xpos, ypos, label in (
        (4.87, 3.68, r"$\hat x^S$"),
        (8.35, 3.68, r"$\hat O$"),
        (12.13, 4.03, r"$\hat F$"),
    ):
        ax.text(
            xpos,
            ypos,
            label,
            ha="center",
            va="center",
            fontsize=5.8,
            color=COLORS["blue_dark"],
            zorder=9,
        )
    # The support identifies the coordinates on which feature noise is defined;
    # it is not a generative transition from support to noise.
    ax.plot(
        [6.98, 6.98, 8.30],
        [2.455, 2.18, 2.18],
        color=COLORS["blue"],
        linewidth=0.78,
        solid_capstyle="round",
        zorder=5.5,
    )
    arrow(
        ax,
        (9.105, 2.64),
        (9.325, 2.84),
        color=COLORS["blue"],
        lw=0.90,
        mutation_scale=6.0,
    )
    arrow(
        ax,
        (21.45, 4.45),
        (22.04, 5.04),
        color=COLORS["green"],
        lw=0.95,
        style="-",
        mutation_scale=6.2,
    )

    # Stage-specific conditions descend from the conditioner into the two flows.
    poly_arrow(
        ax,
        [
            (5.455, 8.57),
            (5.455, 7.58),
            (7.15, 7.58),
            (7.15, 5.45),
            (3.34, 5.45),
            (3.34, 4.44),
        ],
        color=COLORS["purple"],
        lw=1.0,
        style=CONDITION_STYLE,
        mutation_scale=6.6,
        zorder=5,
    )
    poly_arrow(
        ax,
        [
            (7.655, 8.57),
            (7.655, 7.58),
            (7.93, 7.58),
            (7.93, 5.45),
            (10.55, 5.45),
            (10.55, 4.44),
        ],
        color=COLORS["purple"],
        lw=1.0,
        style=CONDITION_STYLE,
        mutation_scale=6.6,
        zorder=5,
    )
    # N(\hat O) is queried after Structure Flow has predicted the active support.
    poly_arrow(
        ax,
        [
            (7.39, 4.03),
            (8.65, 4.03),
            (8.65, 4.92),
            (9.79, 4.92),
        ],
        color=COLORS["blue"],
        lw=0.86,
        mutation_scale=5.5,
        zorder=5.5,
    )
    rounded_box(
        ax,
        2.87,
        4.73,
        0.94,
        0.38,
        r"$G+V$",
        fc=COLORS["white"],
        ec="#B7A4CC",
        fontsize=6.1,
        weight="semibold",
        radius=0.035,
        color=COLORS["purple_dark"],
        zorder=8,
    )
    rounded_box(
        ax,
        9.82,
        4.73,
        1.46,
        0.38,
        r"$G+V+N(\hat O)$",
        fc=COLORS["white"],
        ec="#B7A4CC",
        fontsize=6.1,
        weight="semibold",
        radius=0.035,
        color=COLORS["purple_dark"],
        zorder=8,
    )

    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    for ext, kwargs in {"png": {"dpi": 600}, "pdf": {}, "svg": {}}.items():
        fig.savefig(
            ROOT / f"method_framework.{ext}",
            facecolor=COLORS["white"],
            edgecolor="none",
            metadata={"Title": "Case-conditioned crown-shape generation framework"},
            **kwargs,
        )
    plt.close(fig)


if __name__ == "__main__":
    build_figure()
