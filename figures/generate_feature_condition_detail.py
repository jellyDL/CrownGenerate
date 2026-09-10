#!/usr/bin/env python3
"""Compact Section 3.5 schematic: support first, then local features.

Contract: support prediction precedes feature generation on that support.
Two complementary stage panels separate support prediction from local feature
generation. Token columns mark module interfaces; Feature conditions and their
projection branches share one compound fusion module. Architecture settings and numerical data are
absent. Token strips and sparse-grid icons are schematic, not measured data.
Python/Matplotlib provides all drawing and exports at 180 x 132 mm.
"""

from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from audit_panel_alignment import require_matplotlib_panel_alignment

ROOT = Path(__file__).resolve().parent
FIG_WIDTH_MM = 180.0
FIG_HEIGHT_MM = 132.0
PANEL_WIDTH_MM = 172.0
PANEL_HEIGHT_MM = 60.0
INK, MUTED = "#263F50", "#526675"
COLORS = {
    "flow": ("#326E99", "#EAF3FA"),
    "transformer": ("#4C6C47", "#E6EFDF"),
    "dental": ("#775E8C", "#F4EFF8"),
    "fusion": ("#966648", "#FCF0E5"),
    "support": ("#347B80", "#EAF5F4"),
    "solver": ("#92702D", "#FCF4DE"),
    "neutral": ("#647581", "#F4F7F8"),
}
TEXT_CONTAINMENT = []
mpl.rcParams.update({
    "font.family": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "font.size": 8.0,
    "mathtext.fontset": "dejavusans",
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "svg.hashsalt": "crown-two-stage-compact",
    "text.color": INK,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def txt(ax, x, y, value, *, size=8., color=INK, bold=False, ha="center"):
    return ax.text(
        x, y, value, fontsize=size, color=color, ha=ha, va="center",
        fontweight="semibold" if bold else "normal", linespacing=1.2, zorder=8,
    )


def frame(ax, x, y, w, h, *, family="neutral", panel=False):
    edge, fill = COLORS[family]
    radius = 2.0 if family == "transformer" else .9
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor="white" if panel else fill,
        edgecolor="#C0CDD5" if panel else edge,
        linewidth=.6 if panel else .7, zorder=0 if panel else 2,
    )
    ax.add_patch(patch)


def card(ax, x, y, w, h, title, body, *, family="neutral", size=7.6, body_size=6.9, title_dx=0.):
    frame(ax, x, y, w, h, family=family)
    labels = [
        txt(ax, x+w/2+title_dx, y+h*.27, title, size=size,
            color=COLORS[family][0], bold=True),
        txt(ax, x+w/2, y+h*.69, body, size=body_size, color=MUTED),
    ]
    TEXT_CONTAINMENT.extend((ax, label, (x, y, w, h)) for label in labels)


def wire(ax, points, *, family="flow", condition=False):
    path = MplPath(points, [MplPath.MOVETO] + [MplPath.LINETO]*(len(points)-1))
    ax.add_patch(FancyArrowPatch(
        path=path, arrowstyle="-|>", mutation_scale=6.5,
        linewidth=.75 if condition else .95, color=COLORS[family][0],
        linestyle=(0, (3.2, 2.0)) if condition else "-", zorder=5,
    ))


def operation_band(ax,x,y,w,label,*,family="transformer"):
    ax.add_patch(FancyBboxPatch((x,y),w,3.4,
        boxstyle="round,pad=0,rounding_size=.45",facecolor="white",
        edgecolor=COLORS[family][0],linewidth=.25,alpha=.72,zorder=3))
    t=txt(ax,x+w/2,y+1.7,label,size=6.7,color=MUTED)
    TEXT_CONTAINMENT.append((ax,t,(x,y,w,3.4)))


def integration_mark(ax,x,y,w):
    path=MplPath([(x,y+1.4),(x+w*.3,y-.5),(x+w*.6,y+1.7),(x+w,y)],
                 [MplPath.MOVETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4])
    ax.add_patch(FancyArrowPatch(path=path,arrowstyle="-|>",mutation_scale=4.5,
        linewidth=.65,color=COLORS["solver"][0],zorder=4))


def frozen_mark(ax,x,y):
    edge=COLORS["neutral"][0]
    ax.add_patch(FancyBboxPatch((x+.4,y),1.4,1.9,
        boxstyle="round,pad=0,rounding_size=.6",facecolor="none",edgecolor=edge,lw=.5,zorder=3))
    ax.add_patch(FancyBboxPatch((x,y+1.1),2.2,1.7,
        boxstyle="round,pad=0,rounding_size=.2",facecolor=edge,edgecolor=edge,lw=.4,zorder=4))


def tensor_stack(ax, x, y, w, h, *, family="flow"):
    """A generic feature tensor glyph; sheet count does not encode dimensions."""
    edge, fill = COLORS[family]
    for offset in (1.4, .7, 0.):
        ax.add_patch(Rectangle((x+offset, y-offset*.6), w, h,
            facecolor=fill, edgecolor=edge, linewidth=.55, zorder=3))
    cell_w, cell_h = (w-1.8)/4, (h-1.6)/3
    for row in range(3):
        for col in range(4):
            alpha = (.22, .48, .72)[(row+2*col) % 3]
            ax.add_patch(Rectangle((x+.9+col*cell_w, y+.8+row*cell_h),
                cell_w-.25, cell_h-.25, facecolor=edge,
                edgecolor="none", alpha=alpha, zorder=4))


def token_strip(ax, x, y, *, family="dental", conditioned=False):
    edge, fill = COLORS[family]
    ax.add_patch(FancyBboxPatch((x-.65, y-.65), 5.1, 9.3,
        boxstyle="round,pad=0,rounding_size=.6", facecolor="white",
        edgecolor=edge, linewidth=.5, zorder=3))
    for row, alpha in enumerate((.3, .55, .8, .45)):
        ax.add_patch(Rectangle((x, y+row*2.1), 3.8, 1.6,
            facecolor=fill, edgecolor=edge, linewidth=.35, zorder=4))
        ax.add_patch(Rectangle((x+.35, y+row*2.1+.3), 3.1, 1.,
            facecolor=fill if conditioned else edge, edgecolor="none",
            alpha=1 if conditioned else alpha, zorder=4))
        if conditioned:
            for shift in (0., .8, 1.6):
                ax.plot([x+.55+shift,x+1.15+shift],
                        [y+row*2.1+1.1,y+row*2.1+.3],color=edge,lw=.4,zorder=5)


def support_grid(ax, x, y):
    edge = COLORS["support"][0]
    occupied = {(0, 1), (0, 2), (1, 0), (1, 1), (1, 3), (2, 1), (2, 2)}
    for row in range(3):
        for col in range(4):
            active = (row, col) in occupied
            ax.add_patch(Rectangle((x+col*2.0, y+row*2.0), 1.55, 1.55,
                facecolor=edge if active else "white", edgecolor=edge,
                linewidth=.35, alpha=.85 if active else .32, zorder=3))


def latent_input(ax, symbol, detail, *, feature=False):
    center = 11.5
    txt(ax, center, 33.5 if not feature else 40, symbol, size=9.,
        color=COLORS["flow"][0])
    tensor_stack(ax, 5.0, 37.5 if not feature else 43.5, 11, 8)
    txt(ax, center, 48.5 if not feature else 54, detail, size=6.8, color=MUTED)


def condition_interface(ax, *, feature=False):
    """Unboxed representation beside a token column on a condition path."""
    x = 113 if not feature else 107.1
    token_strip(ax, x, 13 if not feature else 12.5)
    # Place each description directly beside its token glyph with a shared
    # left edge; the condition arrow remains centered on the token column.
    label_x = x + 8
    labels = [
        txt(ax, label_x, 13.8,
            "Condition tokens" if not feature else "Cross-attention", size=7.6,
            color=COLORS["dental"][0], bold=True, ha="left"),
        txt(ax, label_x, 19.4,
            "Global condition\nCoarse voxel tokens", size=7., color=MUTED, ha="left"),
    ]
    TEXT_CONTAINMENT.extend((ax, label, (label_x-1, 10, 169-label_x, 14))
                            for label in labels)


def fusion_module(ax):
    """Keep each condition source adjacent to its own learned projection."""
    frame(ax, 26, 15, 52, 39, family="fusion")
    labels = [
        txt(ax, 52, 18.7, "Condition fusion", size=8.1,
            color=COLORS["fusion"][0], bold=True),
    ]
    TEXT_CONTAINMENT.extend((ax, label, (26, 15, 52, 39)) for label in labels)
    for x, w, title, body, operation, family in (
        (28, 24, "Residual injection", "Global condition\nVoxel readout at $q$",
         "Linear maps", "dental"),
        (54, 22, "Local modulation", "Neighbor geometry\nAxial occupancy",
         "Local MLPs", "fusion"),
    ):
        center = x+w/2
        title_text = txt(ax, center, 24, title, size=7., bold=True,
                         color=COLORS[family][0])
        body_text = txt(ax, center, 29.6, body, size=6.6, color=MUTED)
        TEXT_CONTAINMENT.extend((ax, label, (x, 22, w, 11))
                                for label in (title_text, body_text))
        frame(ax, x+1, 36.5, w-2, 5.5, family=family)
        operation_text = txt(ax, center, 39.25, operation, size=6.8,
                             color=COLORS[family][0])
        TEXT_CONTAINMENT.append((ax, operation_text, (x+1, 36.5, w-2, 5.5)))
        wire(ax, [(center, 33), (center, 36.5)], family=family, condition=True)

    frame(ax, 29, 44.5, 22, 6, family="flow")
    text = txt(ax, 40, 47.5, "Input adaptation", size=6.8,
               color=COLORS["flow"][0])
    TEXT_CONTAINMENT.append((ax, text, (29, 44.5, 22, 6)))
    ax.plot([52.8,52.8],[22.4,41.8],color=COLORS["fusion"][0],alpha=.25,lw=.35,zorder=3)
    edge = COLORS["fusion"][0]
    ax.add_patch(Circle((65, 47.5), 1.9, facecolor="white",
        edgecolor=edge, linewidth=.75, zorder=4))
    ax.plot([64, 66], [47.5, 47.5], color=edge, lw=.75, zorder=5)
    ax.plot([65, 65], [46.5, 48.5], color=edge, lw=.75, zorder=5)
    wire(ax, [(40, 42), (40, 43.3), (60.5, 43.3), (63.7, 46.1)],
         family="dental", condition=True)
    wire(ax, [(65, 42), (65, 45.6)], family="fusion", condition=True)
    wire(ax, [(51, 47.5), (63.1, 47.5)])
    wire(ax, [(66.9, 47.5), (79.5, 47.5), (79.5, 40.5), (81.35, 40.5)])


def result_glyph(ax, *, support=False):
    """Outputs are data glyphs, distinct from all processing blocks."""
    family = "support" if support else "flow"
    txt(ax, 162, 33 if support else 32.1, "Active\nsupport" if support else "Local\nfeatures",
        size=7.3, color=COLORS[family][0], bold=True)
    txt(ax, 162, 47.7, r"$\hat O$" if support else r"$\hat F_q$",
        size=9.5, color=COLORS[family][0])
    if support:
        support_grid(ax, 158.2, 38.725)
    else:
        tensor_stack(ax, 157, 37, 9, 7, family="flow")


def axes_panel(fig, bottom, letter, title, subtitle):
    ax = fig.add_axes([
        4/FIG_WIDTH_MM, bottom/FIG_HEIGHT_MM,
        PANEL_WIDTH_MM/FIG_WIDTH_MM, PANEL_HEIGHT_MM/FIG_HEIGHT_MM,
    ])
    ax.set(xlim=(0, PANEL_WIDTH_MM), ylim=(PANEL_HEIGHT_MM, 0), aspect="equal")
    ax.axis("off")
    frame(ax, .15, .15, 171.7, 59.7, panel=True)
    txt(ax, 3, 4.8, letter, size=9.5, bold=True,
        color=COLORS["flow"][0], ha="left")
    txt(ax, 10, 4.8, title, size=9.4, bold=True, ha="left")
    txt(ax, 168, 4.8, subtitle, size=6.9, color=MUTED, ha="right")
    return ax


def structure_panel(ax):
    # Conditions form one upper row; the generation path is the lower row.
    card(ax, 4, 11, 35, 12, "Dental inputs",
         "Maxillary / mandibular points\nPreparation margin · FDI", family="dental")
    card(ax, 47, 11, 55, 12, "Multiscale dental encoder",
         "Point MLP + source embedding\nGlobal pooling · voxel refinement", family="dental")
    condition_interface(ax)
    wire(ax, [(39, 17), (47, 17)], family="dental")
    wire(ax, [(102, 17), (112.35, 17)], family="dental")
    wire(ax, [(114.9, 21.65), (114.9, 26), (65, 26), (65, 29)],
         family="dental", condition=True)
    # The aligned readout is a separate encoder output, not attention tokens.
    wire(ax, [(55, 23), (55, 26), (42, 26), (42, 29)],
         family="dental", condition=True)

    latent_input(ax, r"$x^S(t)$", "Noisy latent")
    token_strip(ax, 23, 37.5, family="flow")
    frame(ax, 33, 29, 42, 25, family="transformer")
    structure_labels = [
        txt(ax, 42, 31.5, "Aligned injection", size=6.3,
            color=COLORS["dental"][0]),
        txt(ax, 65, 31.5, "Cross-attention", size=6.3,
            color=COLORS["dental"][0]),
        txt(ax, 54, 37.4, "Structure DiT", size=8.3,
            color=COLORS["transformer"][0], bold=True),

    ]
    TEXT_CONTAINMENT.extend((ax, label, (33, 29, 42, 25)) for label in structure_labels)
    for y,label,family in ((41.5,"Time-modulated self-attention","transformer"),
                           (45.4,"Dental cross-attention","dental"),
                           (49.3,"Feed-forward","transformer")):
        operation_band(ax,35,y,38,label,family=family)
    card(ax, 85, 32, 20, 19, "ODE solver", "Velocity\nintegration",
         family="solver")
    card(ax, 115, 32, 30, 19, "Frozen decoder", "Structure decoding\nOccupancy selection",
         family="neutral", body_size=6.7, title_dx=1.1)
    integration_mark(ax,89,39.8,12)
    frozen_mark(ax,118,35.5)
    result_glyph(ax, support=True)
    for start, end in ((17.5, 22.35), (27.45, 33), (75, 85), (105, 115)):
        wire(ax, [(start, 41.5), (end, 41.5)])
    wire(ax, [(145, 41.5), (157, 41.5)], family="support")
    txt(ax, 80, 38.6, r"$v^S$", size=9., color=COLORS["flow"][0])


def feature_panel(ax):
    # Consolidate source, projection and fusion in one compound network module.
    condition_interface(ax, feature=True)
    wire(ax, [(109, 21.15), (109, 25)],
         family="dental", condition=True)

    latent_input(ax, r"$x^F(q,t)$", "Noisy features", feature=True)
    fusion_module(ax)
    token_strip(ax, 82, 36.5, family="flow", conditioned=True)
    txt(ax, 84, 32.6, "Fused\ntokens", size=6.7, color=COLORS["flow"][0])
    frame(ax,95,25,28,29,family="transformer")
    t=txt(ax,109,32.2,"Feature DiT",size=8.3,bold=True,color=COLORS["transformer"][0])
    TEXT_CONTAINMENT.append((ax,t,(95,25,28,29)))
    for y,label,family in ((37.5,"Sparse self-attention","transformer"),
                           (42.,"Dental cross-attention","dental"),
                           (46.5,"Time modulation","transformer")):
        operation_band(ax,96.5,y,25,label,family=family)
    card(ax, 132.5, 31, 20, 19, "ODE solver", "Velocity\nintegration",
         family="solver")
    integration_mark(ax,136.5,38.8,12)
    result_glyph(ax)
    wire(ax,[(17.5,47.5),(29,47.5)])
    for start, end in ((86.45,95),(123,132.5),(152.5,156.5)):
        wire(ax,[(start,40.5),(end,40.5)])
    txt(ax, 127.75, 37.6, r"$v^F$", size=9., color=COLORS["flow"][0])
    txt(ax, 69, 11, r"$S=\hat O,\quad q\in S$", size=8.,
        color=COLORS["support"][0], ha="left")
    txt(ax, 168, 57.1, r"$\hat Z=(\hat O,\hat F)$", size=8.,
        color=COLORS["support"][0], ha="right")
    wire(ax, [(79, 57), (86, 57)])
    txt(ax, 88, 57, "Data flow", size=6.6, color=MUTED, ha="left")
    wire(ax, [(109, 57), (116, 57)], family="dental", condition=True)
    txt(ax, 118, 57, "Conditioning", size=6.6, color=MUTED, ha="left")


def containment_gate(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    failures = []
    for ax, label, (x, y, w, h) in TEXT_CONTAINMENT:
        box = label.get_window_extent(renderer).transformed(ax.transData.inverted())
        left, right = sorted((box.x0, box.x1))
        top, bottom = sorted((box.y0, box.y1))
        if left < x+.45 or right > x+w-.45 or top < y+.25 or bottom > y+h-.25:
            failures.append(f"{label.get_text()!r} does not fit its card")
    if failures:
        raise RuntimeError("Text containment: " + "; ".join(failures))


def build_figure():
    TEXT_CONTAINMENT.clear()
    fig = plt.figure(figsize=(FIG_WIDTH_MM/25.4, FIG_HEIGHT_MM/25.4))
    a = axes_panel(fig, 68, "a", "Structure Flow", "Predict the active support")
    b = axes_panel(fig, 4, "b", "Feature Flow", "Generate local latent features")
    structure_panel(a)
    feature_panel(b)

    # The only connection between stages carries support to local conditioning.
    support_path = MplPath(
        [(166/180, 77.2/132), (166/180, 66/132),
         (69/180, 66/132), (69/180, 42.5/132)],
        [MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO, MplPath.LINETO],
    )
    fig.add_artist(FancyArrowPatch(
        path=support_path, transform=fig.transFigure, arrowstyle="-|>",
        mutation_scale=6.5, linewidth=.85, color=COLORS["support"][0], zorder=5,
    ))
    containment_gate(fig)
    require_matplotlib_panel_alignment(
        fig, axes=[a, b], panel_ids=["a", "b"],
        column_groups=[{"id": "two-stage-flows", "panels": ["a", "b"]}],
        json_out=ROOT/"feature_condition_detail.alignment.json",
        overlay_svg=ROOT/"feature_condition_detail.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    metadata = {"Title": "Two-stage conditional flow matching"}
    fig.savefig(ROOT/"feature_condition_detail.png", dpi=600, metadata=metadata)
    fig.savefig(ROOT/"feature_condition_detail.pdf", metadata=metadata)
    fig.savefig(ROOT/"feature_condition_detail.svg", metadata=metadata)
    svg_path = ROOT / "feature_condition_detail.svg"
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
    )
    fig.savefig(ROOT/"feature_condition_detail.tiff", dpi=600,
                pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(ROOT/"feature_condition_detail.preview.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    build_figure()
