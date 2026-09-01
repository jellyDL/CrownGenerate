#!/usr/bin/env python3
"""Generate the two-stage conditional flow matching schematic for Section 3.5."""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, ConnectionPatch, FancyArrowPatch, FancyBboxPatch, Rectangle

try:
    from audit_panel_alignment import require_matplotlib_panel_alignment
except ImportError as exc:
    raise RuntimeError("Run with the publication-figure audit scripts on PYTHONPATH.") from exc


ROOT = Path(__file__).resolve().parent
FIG_WIDTH_MM = 180.0
FIG_HEIGHT_MM = 98.0
FIG_WIDTH_IN = FIG_WIDTH_MM / 25.4
FIG_HEIGHT_IN = FIG_HEIGHT_MM / 25.4

COLORS = {
    "ink": "#23313E",
    "muted": "#687784",
    "blue": "#2D78A6",
    "blue_dark": "#1C5D83",
    "blue_fill": "#EAF4FA",
    "teal": "#2A9997",
    "teal_dark": "#176C6D",
    "teal_fill": "#E9F7F5",
    "green": "#5A956F",
    "green_dark": "#34734E",
    "green_fill": "#EAF6EE",
    "amber": "#D38A3D",
    "amber_dark": "#97591B",
    "amber_fill": "#FFF4E4",
    "coral": "#C86D5E",
    "coral_dark": "#994C42",
    "coral_fill": "#FCEDEA",
    "purple": "#7656A7",
    "purple_dark": "#553D79",
    "purple_fill": "#F2EEF9",
    "purple_alt_fill": "#F8EFF5",
    "line": "#C7D5DD",
    "panel_structure": "#FCFDFE",
    "panel_feature": "#FCFEFD",
    "panel_structure_edge": "#BDD3E0",
    "panel_feature_edge": "#B9DAD5",
    "white": "#FFFFFF",
}

CONDITION_STYLE = (0, (4.0, 1.8, 1.0, 1.8))
FONT_NOTE = 7.2
FONT_CARD = 8.0
FONT_TITLE = 9.4

mpl.rcParams.update(
    {
        "font.family": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": FONT_CARD,
        "text.color": COLORS["ink"],
        "mathtext.fontset": "dejavusans",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "figure.facecolor": COLORS["white"],
        "savefig.facecolor": COLORS["white"],
    }
)


def rounded_box(
    ax,
    x,
    y,
    width,
    height,
    *,
    facecolor=COLORS["white"],
    edgecolor=COLORS["line"],
    linewidth=0.8,
    radius=1.2,
    border=True,
    zorder=3,
):
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor if border else "none",
        linewidth=linewidth if border else 0.0,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def arrow(ax, start, end, *, color, linewidth=1.15, linestyle="-", zorder=5):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=8.5,
        linewidth=linewidth,
        linestyle=linestyle,
        color=color,
        shrinkA=1.8,
        shrinkB=2.0,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def poly_arrow(ax, points, *, color, linewidth=1.15, linestyle="-", zorder=5):
    xs, ys = zip(*points[:-1])
    ax.plot(
        xs,
        ys,
        color=color,
        linewidth=linewidth,
        linestyle=linestyle,
        solid_capstyle="round",
        dash_capstyle="round",
        zorder=zorder,
    )
    return arrow(
        ax,
        points[-2],
        points[-1],
        color=color,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=zorder + 0.1,
    )


def configure_axis(ax):
    ax.set_xlim(0.0, 180.0)
    ax.set_ylim(0.0, 100.0)
    ax.set_aspect("auto")
    ax.axis("off")


def draw_panel_frame(ax, label, title, *, facecolor, edgecolor, accent):
    rounded_box(
        ax,
        1.0,
        1.0,
        178.0,
        98.0,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=0.9,
        radius=1.8,
        zorder=0,
    )
    ax.text(4.0, 92.0, f"({label})", ha="left", va="center", fontsize=FONT_TITLE, fontweight="bold", color=accent, zorder=8)
    ax.text(13.0, 92.0, title, ha="left", va="center", fontsize=FONT_TITLE, fontweight="semibold", zorder=8)
    ax.plot([13.0, 34.0], [85.4, 85.4], color=accent, linewidth=1.25, solid_capstyle="round", zorder=2)


def draw_process_node(
    ax,
    x,
    y,
    width,
    height,
    title,
    detail,
    *,
    facecolor,
    edgecolor,
    textcolor,
    note=None,
    note_color=None,
):
    rounded_box(
        ax,
        x,
        y,
        width,
        height,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=0.85,
        radius=1.1,
        zorder=3,
    )
    if note is None:
        title_y, detail_y = y + 0.68 * height, y + 0.30 * height
    else:
        title_y, detail_y = y + 0.74 * height, y + 0.43 * height
    ax.text(x + width / 2, title_y, title, ha="center", va="center", fontsize=FONT_CARD, fontweight="semibold", color=textcolor, zorder=7)
    if detail:
        ax.text(x + width / 2, detail_y, detail, ha="center", va="center", fontsize=FONT_NOTE, color=textcolor, zorder=7)
    if note:
        ax.text(x + width / 2, y + 0.17 * height, note, ha="center", va="center", fontsize=FONT_NOTE, color=note_color or COLORS["muted"], zorder=7)


def draw_dit_block(
    ax,
    x,
    y,
    width,
    height,
    *,
    title,
    detail,
    sparse=False,
    facecolor,
    edgecolor,
    textcolor,
    mark_color,
):
    rounded_box(
        ax,
        x,
        y,
        width,
        height,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.05,
        radius=1.3,
        zorder=3,
    )
    ax.text(
        x + width / 2,
        y + height - 11.0,
        title,
        ha="center",
        va="center",
        fontsize=FONT_CARD,
        fontweight="semibold",
        color=textcolor,
        linespacing=1.05,
        zorder=7,
    )
    if sparse:
        dot_offsets = ((-7, 3), (-4, 7), (-1, 2), (2, 6), (5, 1), (7, 5), (-6, -2), (-2, -5), (1, -1), (4, -5), (7, -2))
        center_x, center_y = x + width / 2, y + height / 2 - 2.0
        for dx, dy in dot_offsets:
            ax.add_patch(Circle((center_x + dx, center_y + dy), 0.95, facecolor=mark_color, edgecolor="none", zorder=5))
        for index in range(3):
            rounded_box(
                ax,
                center_x + 3.5 + index * 0.7,
                center_y - 5.5 + index * 0.7,
                3.2,
                5.4,
                facecolor=COLORS["white"],
                edgecolor=edgecolor,
                linewidth=0.5,
                radius=0.35,
                zorder=5 + index,
            )
    else:
        grid_x, grid_y, cell = x + width / 2 - 8.0, y + height / 2 - 6.0, 3.2
        for row in range(3):
            for col in range(5):
                active = (row + col) % 3 != 0
                ax.add_patch(
                    Rectangle(
                        (grid_x + col * cell, grid_y + row * cell),
                        cell - 0.35,
                        cell - 0.35,
                        facecolor=mark_color if active else COLORS["white"],
                        edgecolor="none",
                        zorder=5,
                    )
                )
    ax.text(x + width / 2, y + 8.0, detail, ha="center", va="center", fontsize=FONT_NOTE, color=textcolor, zorder=7)


def draw_support_output(ax, x, y, width, height, *, facecolor, edgecolor, textcolor, active_color):
    rounded_box(
        ax,
        x,
        y,
        width,
        height,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=0.9,
        radius=1.0,
        zorder=3,
    )
    ax.text(x + width / 2, y + height - 7.0, r"$\hat O$", ha="center", va="center", fontsize=11.5, fontweight="semibold", color=textcolor, zorder=7)
    grid_x, grid_y, cell = x + 1.2, y + 13.0, 2.0
    for row in range(3):
        for col in range(3):
            active = (row, col) in {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
            ax.add_patch(
                Rectangle(
                    (grid_x + col * cell, grid_y + row * cell),
                    cell - 0.22,
                    cell - 0.22,
                    facecolor=active_color if active else COLORS["white"],
                    edgecolor=edgecolor,
                    linewidth=0.32,
                    zorder=5,
                )
            )
    ax.text(x + width / 2, y + 6.0, "64³", ha="center", va="center", fontsize=FONT_NOTE, color=textcolor, zorder=7)


def draw_structure_condition_encoding(ax):
    node_color = "#B7A7D1"
    grid_x, grid_y, cell = 18.6, 30.7, 1.8
    for start, end in (((11.0, 33.5), (13.7, 35.2)), ((13.7, 35.2), (15.6, 32.2)), ((11.0, 33.5), (15.6, 32.2))):
        ax.plot([start[0], end[0]], [start[1], end[1]], color=node_color, linewidth=0.55, zorder=4)
    for x, y, size in ((11.0, 33.5, 1.05), (13.7, 35.2, 0.9), (15.6, 32.2, 0.9)):
        ax.add_patch(Circle((x, y), size, facecolor=COLORS["purple"], edgecolor="none", zorder=5))
    ax.plot([16.8, 18.1], [33.4, 33.4], color=COLORS["purple"], linewidth=0.7, zorder=4)
    for row in range(3):
        for col in range(3):
            active = (row, col) in {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
            ax.add_patch(
                Rectangle(
                    (grid_x + col * cell, grid_y + row * cell),
                    cell - 0.28,
                    cell - 0.28,
                    facecolor=COLORS["purple"] if active else COLORS["white"],
                    edgecolor="#C8B9DC",
                    linewidth=0.25,
                    zorder=5,
                )
            )
    ax.plot([24.6, 32.2], [33.4, 33.4], color=node_color, linewidth=0.65, zorder=4)


def draw_condition_icon(ax, x, y, kind):
    if kind == "cross":
        ax.add_patch(Circle((x + 1.0, y + 4.3), 0.85, facecolor=COLORS["purple"], edgecolor="none", zorder=6))
        ax.plot([x + 2.0, x + 3.0], [y + 4.3, y + 4.3], color=COLORS["purple"], linewidth=0.65, zorder=5)
        for row in range(2):
            for col in range(2):
                active = (row, col) != (0, 0)
                ax.add_patch(
                    Rectangle(
                        (x + 3.2 + col * 1.35, y + 3.0 + row * 1.35),
                        1.05,
                        1.05,
                        facecolor=COLORS["purple"] if active else COLORS["white"],
                        edgecolor="#B7A7D1",
                        linewidth=0.25,
                        zorder=6,
                    )
                )
    elif kind == "residual":
        cell = 1.35
        for row in range(3):
            for col in range(3):
                is_query = (row, col) == (1, 1)
                ax.add_patch(
                    Rectangle(
                        (x + col * cell, y + row * cell),
                        cell - 0.22,
                        cell - 0.22,
                        facecolor=COLORS["coral"] if is_query else COLORS["purple_fill"],
                        edgecolor="#BA90AF",
                        linewidth=0.25,
                        zorder=6,
                    )
                )
        ax.add_patch(Circle((x + 1.5 * cell - 0.12, y + 1.5 * cell - 0.12), 0.35, facecolor=COLORS["white"], edgecolor="none", zorder=7))
    elif kind == "local":
        center_x, center_y = x + 3.2, y + 5.0
        for dx, dy in ((-2.0, 1.6), (-1.7, -1.4), (1.8, 1.5), (2.0, -1.3)):
            ax.plot([center_x, center_x + dx], [center_y, center_y + dy], color="#B7A7D1", linewidth=0.5, zorder=4)
            ax.add_patch(Circle((center_x + dx, center_y + dy), 0.72, facecolor=COLORS["purple"], edgecolor="none", zorder=6))
        for dx, dy in ((0.0, 2.9), (0.0, -2.9), (2.9, 0.0)):
            ax.plot([center_x, center_x + dx], [center_y, center_y + dy], color="#9CC9B2", linewidth=0.55, zorder=4)
            ax.add_patch(Circle((center_x + dx, center_y + dy), 0.65, facecolor=COLORS["green"], edgecolor="none", zorder=6))
        ax.add_patch(Circle((center_x, center_y), 0.95, facecolor=COLORS["coral"], edgecolor=COLORS["white"], linewidth=0.35, zorder=7))


def draw_feature_condition_card(ax, x, y, width, height, title, detail, *, facecolor, edgecolor, textcolor, kind):
    rounded_box(
        ax,
        x,
        y,
        width,
        height,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=0.85,
        radius=1.1,
        zorder=3,
    )
    text_x = x + width / 2 + 4.0
    ax.text(text_x, y + 0.68 * height, title, ha="center", va="center", fontsize=FONT_CARD, fontweight="semibold", color=textcolor, zorder=7)
    ax.text(text_x, y + 0.30 * height, detail, ha="center", va="center", fontsize=FONT_NOTE, color=textcolor, zorder=7)
    draw_condition_icon(ax, x + 3.2, y + 2.0, kind)


def draw_support_context_grid(ax, x, y):
    cell = 1.0
    for row in range(3):
        for col in range(3):
            center = (row, col) == (1, 1)
            active = center or (row, col) in {(0, 1), (1, 0), (1, 2), (2, 1)}
            ax.add_patch(
                Rectangle(
                    (x + col * cell, y + row * cell),
                    cell - 0.18,
                    cell - 0.18,
                    facecolor=COLORS["teal"] if center else (COLORS["green"] if active else COLORS["white"]),
                    edgecolor="#8AB89C",
                    linewidth=0.25,
                    zorder=6,
                )
            )


def draw_feature_output(ax, x, y, width, height):
    rounded_box(
        ax,
        x,
        y,
        width,
        height,
        facecolor=COLORS["teal_fill"],
        edgecolor=COLORS["teal"],
        linewidth=0.9,
        radius=1.1,
        zorder=3,
    )
    ax.text(x + width / 2, y + height - 6.2, r"$\hat{F}_q$", ha="center", va="center", fontsize=11.2, fontweight="semibold", color=COLORS["teal_dark"], zorder=7)
    points = ((x + 4.0, y + 5.2), (x + 8.2, y + 7.6), (x + 12.6, y + 5.5), (x + 13.4, y + 9.4))
    for start, end in ((0, 1), (1, 2), (1, 3), (2, 3)):
        ax.plot([points[start][0], points[end][0]], [points[start][1], points[end][1]], color="#82C2BD", linewidth=0.55, zorder=4)
    for index, point in enumerate(points):
        ax.add_patch(Circle(point, 0.75, facecolor=COLORS["teal"] if index != 1 else COLORS["blue"], edgecolor=COLORS["white"], linewidth=0.28, zorder=6))


def draw_noise_texture(ax, x, y, color):
    for dx, dy, radius in ((0.0, 0.0, 0.65), (2.2, 0.6, 0.5), (4.2, -0.35, 0.55), (6.1, 0.45, 0.43)):
        ax.add_patch(Circle((x + dx, y + dy), radius, facecolor=color, edgecolor="none", alpha=0.45, zorder=5))


def draw_decoder_texture(ax, x, y):
    for index, color in enumerate((COLORS["coral"], "#E6A59B", COLORS["coral"], "#E6A59B")):
        ax.add_patch(Rectangle((x + index * 1.65, y), 1.25, 1.25, facecolor=color, edgecolor="none", zorder=5))


def draw_structure_panel(ax):
    draw_panel_frame(
        ax,
        "a",
        "Structure Flow: generate active support",
        facecolor=COLORS["panel_structure"],
        edgecolor=COLORS["panel_structure_edge"],
        accent=COLORS["blue"],
    )

    rounded_box(
        ax,
        5.0,
        25.0,
        37.0,
        49.0,
        facecolor=COLORS["purple_fill"],
        edgecolor="#A793C3",
        linewidth=0.9,
        radius=1.2,
        zorder=3,
    )
    ax.text(23.5, 65.0, "Structure condition", ha="center", va="center", fontsize=FONT_CARD, fontweight="semibold", color=COLORS["purple_dark"], zorder=7)
    ax.text(23.5, 42.0, "global + 16³ voxel", ha="center", va="center", fontsize=FONT_NOTE, color=COLORS["muted"], zorder=7)
    draw_structure_condition_encoding(ax)
    rounded_box(ax, 33.0, 29.5, 7.5, 7.0, facecolor=COLORS["white"], edgecolor="#B9A7CC", linewidth=0.6, radius=0.5, zorder=5)
    ax.text(36.75, 33.0, "FDI", ha="center", va="center", fontsize=FONT_NOTE, fontweight="semibold", color=COLORS["purple_dark"], zorder=6)

    draw_process_node(
        ax,
        50.0,
        13.0,
        21.0,
        17.0,
        "xₜˢ",
        None,
        facecolor=COLORS["blue_fill"],
        edgecolor="#8FB2C8",
        textcolor=COLORS["blue_dark"],
    )
    draw_noise_texture(ax, 56.8, 17.0, COLORS["blue"])
    draw_dit_block(
        ax,
        80.0,
        21.0,
        26.0,
        56.0,
        title="Structure DiT",
        detail="16³ latent",
        sparse=False,
        facecolor=COLORS["blue_fill"],
        edgecolor=COLORS["blue"],
        textcolor=COLORS["blue_dark"],
        mark_color=COLORS["blue"],
    )
    draw_process_node(
        ax,
        113.0,
        39.0,
        12.0,
        22.0,
        "vθˢ",
        "velocity",
        facecolor=COLORS["blue_fill"],
        edgecolor="#8FB2C8",
        textcolor=COLORS["blue_dark"],
    )
    draw_process_node(
        ax,
        131.0,
        35.0,
        13.0,
        30.0,
        "ODE",
        "t = 1 -> 0",
        facecolor=COLORS["amber_fill"],
        edgecolor=COLORS["amber"],
        textcolor=COLORS["amber_dark"],
    )
    draw_process_node(
        ax,
        150.0,
        37.0,
        13.0,
        26.0,
        "Frozen",
        "decoder",
        facecolor=COLORS["coral_fill"],
        edgecolor=COLORS["coral"],
        textcolor=COLORS["coral_dark"],
    )
    draw_decoder_texture(ax, 153.1, 40.2)
    draw_support_output(
        ax,
        168.0,
        27.0,
        9.0,
        45.0,
        facecolor=COLORS["green_fill"],
        edgecolor=COLORS["green"],
        textcolor=COLORS["green_dark"],
        active_color=COLORS["green"],
    )

    poly_arrow(ax, [(42.0, 53.0), (61.0, 53.0), (61.0, 66.0), (80.0, 66.0)], color=COLORS["purple"], linewidth=1.1, linestyle=CONDITION_STYLE)
    arrow(ax, (71.0, 21.5), (80.0, 36.0), color=COLORS["blue"], linewidth=1.2)
    arrow(ax, (106.0, 50.0), (113.0, 50.0), color=COLORS["blue"], linewidth=1.2)
    arrow(ax, (125.0, 50.0), (131.0, 50.0), color=COLORS["blue"], linewidth=1.2)
    arrow(ax, (144.0, 50.0), (150.0, 50.0), color=COLORS["blue"], linewidth=1.2)
    arrow(ax, (163.0, 50.0), (168.0, 50.0), color=COLORS["blue"], linewidth=1.2)


def draw_feature_panel(ax):
    draw_panel_frame(
        ax,
        "b",
        "Feature Flow: generate local features on S",
        facecolor=COLORS["panel_feature"],
        edgecolor=COLORS["panel_feature_edge"],
        accent=COLORS["teal"],
    )

    draw_feature_condition_card(
        ax,
        5.0,
        64.0,
        42.0,
        20.0,
        "Cross-attention",
        "global + 16³ tokens",
        facecolor=COLORS["purple_fill"],
        edgecolor="#A793C3",
        textcolor=COLORS["purple_dark"],
        kind="cross",
    )
    draw_feature_condition_card(
        ax,
        5.0,
        39.0,
        42.0,
        20.0,
        "Residual injection",
        "global + 64³ voxel at q",
        facecolor=COLORS["purple_alt_fill"],
        edgecolor="#B786A5",
        textcolor=COLORS["purple_dark"],
        kind="residual",
    )
    rounded_box(
        ax,
        5.0,
        6.0,
        42.0,
        28.0,
        facecolor=COLORS["teal_fill"],
        edgecolor=COLORS["teal"],
        linewidth=0.85,
        radius=1.1,
        zorder=3,
    )
    ax.text(30.0, 28.0, "Local modulation", ha="center", va="center", fontsize=FONT_CARD, fontweight="semibold", color=COLORS["teal_dark"], zorder=7)
    draw_condition_icon(ax, 8.2, 10.7, "local")
    draw_process_node(
        ax,
        55.0,
        38.0,
        23.0,
        31.0,
        "Feature token",
        "at q",
        facecolor=COLORS["teal_fill"],
        edgecolor=COLORS["teal"],
        textcolor=COLORS["teal_dark"],
    )
    draw_noise_texture(ax, 62.3, 15.7, COLORS["teal"])
    draw_process_node(
        ax,
        55.0,
        12.0,
        23.0,
        16.0,
        "xₜᶠ(q)",
        None,
        facecolor=COLORS["teal_fill"],
        edgecolor=COLORS["teal"],
        textcolor=COLORS["teal_dark"],
    )
    draw_dit_block(
        ax,
        88.0,
        17.0,
        26.0,
        61.0,
        title="Feature DiT",
        detail="sparse on S",
        sparse=True,
        facecolor=COLORS["teal_fill"],
        edgecolor=COLORS["teal"],
        textcolor=COLORS["teal_dark"],
        mark_color=COLORS["teal"],
    )
    draw_process_node(
        ax,
        121.0,
        40.0,
        13.0,
        22.0,
        "vθᶠ(q)",
        "velocity",
        facecolor=COLORS["teal_fill"],
        edgecolor=COLORS["teal"],
        textcolor=COLORS["teal_dark"],
    )
    draw_process_node(
        ax,
        140.0,
        36.0,
        14.0,
        30.0,
        "ODE",
        "t = 1 -> 0",
        facecolor=COLORS["amber_fill"],
        edgecolor=COLORS["amber"],
        textcolor=COLORS["amber_dark"],
    )
    draw_feature_output(ax, 159.0, 35.0, 18.0, 23.0)
    rounded_box(
        ax,
        157.0,
        62.0,
        20.0,
        22.0,
        facecolor=COLORS["green_fill"],
        edgecolor=COLORS["green"],
        linewidth=0.85,
        radius=1.1,
        zorder=3,
    )
    ax.text(167.0, 78.5, "Support S", ha="center", va="center", fontsize=FONT_CARD, fontweight="semibold", color=COLORS["green_dark"], zorder=7)
    ax.text(167.0, 71.0, "context A(q; S)", ha="center", va="center", fontsize=FONT_NOTE, color=COLORS["green_dark"], zorder=7)
    draw_support_context_grid(ax, 165.8, 62.8)

    poly_arrow(ax, [(47.0, 74.0), (82.0, 74.0), (82.0, 68.0), (88.0, 68.0)], color=COLORS["purple"], linewidth=1.1, linestyle=CONDITION_STYLE)
    poly_arrow(ax, [(47.0, 49.0), (51.0, 49.0), (51.0, 57.0), (55.0, 57.0)], color=COLORS["purple"], linewidth=1.1, linestyle=CONDITION_STYLE)
    ax.text(30.0, 18.5, "dental neighborhood", ha="center", va="center", fontsize=FONT_NOTE, color=COLORS["purple_dark"], zorder=7)
    ax.text(30.0, 9.5, "support context A(q; S)", ha="center", va="center", fontsize=FONT_NOTE, color=COLORS["green_dark"], zorder=7)

    poly_arrow(ax, [(157.0, 73.0), (117.0, 73.0), (117.0, 4.5), (47.0, 4.5), (47.0, 8.0)], color=COLORS["blue"], linewidth=1.0)
    poly_arrow(ax, [(47.0, 23.0), (51.0, 23.0), (51.0, 45.0), (55.0, 45.0)], color=COLORS["purple"], linewidth=1.1, linestyle=CONDITION_STYLE)
    arrow(ax, (78.0, 53.5), (88.0, 53.5), color=COLORS["blue"], linewidth=1.2)
    arrow(ax, (78.0, 20.0), (88.0, 35.0), color=COLORS["blue"], linewidth=1.15)
    arrow(ax, (114.0, 51.0), (121.0, 51.0), color=COLORS["blue"], linewidth=1.2)
    arrow(ax, (134.0, 51.0), (140.0, 51.0), color=COLORS["blue"], linewidth=1.2)
    arrow(ax, (154.0, 51.0), (159.0, 51.0), color=COLORS["blue"], linewidth=1.2)


def build_figure():
    fig = plt.figure(figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))
    structure_ax = fig.add_axes([0.02, 0.545, 0.96, 0.41])
    feature_ax = fig.add_axes([0.02, 0.055, 0.96, 0.41])
    configure_axis(structure_ax)
    configure_axis(feature_ax)

    draw_structure_panel(structure_ax)
    draw_feature_panel(feature_ax)
    fig.text(
        0.5,
        0.505,
        "Shared flow matching  |  t = 1 (noise) -> t = 0 (data)",
        ha="center",
        va="center",
        fontsize=FONT_NOTE,
        color=COLORS["amber_dark"],
        bbox={"boxstyle": "round,pad=0.22", "facecolor": COLORS["amber_fill"], "edgecolor": COLORS["amber"], "linewidth": 0.6},
    )
    fig.add_artist(
        ConnectionPatch(
            xyA=(172.5, 27.0),
            coordsA=structure_ax.transData,
            xyB=(172.5, 84.0),
            coordsB=feature_ax.transData,
            arrowstyle="-|>",
            mutation_scale=8.5,
            linewidth=1.25,
            color=COLORS["blue"],
            shrinkA=1.8,
            shrinkB=2.0,
            zorder=8,
        )
    )

    require_matplotlib_panel_alignment(
        fig,
        axes=[structure_ax, feature_ax],
        panel_ids=["a", "b"],
        column_groups=[{"id": "two-stage-flow", "panels": ["a", "b"]}],
        json_out=ROOT / "feature_condition_detail.alignment.json",
        overlay_svg=ROOT / "feature_condition_detail.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
    )

    export_metadata = {"Title": "Two-stage conditional flow matching"}
    fig.savefig(
        ROOT / "feature_condition_detail.png",
        dpi=600,
        facecolor=COLORS["white"],
        edgecolor="none",
        metadata=export_metadata,
    )
    fig.savefig(
        ROOT / "feature_condition_detail.pdf",
        facecolor=COLORS["white"],
        edgecolor="none",
        metadata=export_metadata,
    )
    svg_path = ROOT / "feature_condition_detail.svg"
    fig.savefig(
        svg_path,
        facecolor=COLORS["white"],
        edgecolor="none",
        metadata=export_metadata,
    )
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
    )
    fig.savefig(
        ROOT / "feature_condition_detail.tiff",
        dpi=600,
        facecolor=COLORS["white"],
        edgecolor="none",
    )
    plt.close(fig)


if __name__ == "__main__":
    build_figure()
