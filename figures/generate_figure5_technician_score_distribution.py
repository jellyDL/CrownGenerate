#!/usr/bin/env python3
"""Render a blinded-technician modification-need distribution figure.

The figure supports two modes:

* ``--template`` creates a clearly watermarked layout preview. Its segment
  widths are placeholders and must not be used as results.
* ``--data`` reads locked case-level consensus counts from JSON and renders a
  publication figure. Expected schema::

    {
      "manual_workflow": {
        "no_modification": 0,
        "minor_modification": 0,
        "moderate_modification": 0,
        "major_modification": 0
      },
      "proposed_cad_draft": {
        "no_modification": 0,
        "minor_modification": 0,
        "moderate_modification": 0,
        "major_modification": 0
      }
    }

Counts must be case-level consensus observations, not pooled reader ratings.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np


ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE_BASE = ROOT / "figure5_technician_score_distribution_template"
DEFAULT_RESULT_BASE = ROOT / "figure5_technician_score_distribution"

CATEGORIES = (
    ("no_modification", "No modification", "#3F8E89"),
    ("minor_modification", "Minor modification", "#8FC3A8"),
    ("moderate_modification", "Moderate modification", "#D9AF52"),
    ("major_modification", "Major modification", "#B84C4A"),
)
TEXT = "#24313C"
MUTED = "#687681"
LINE = "#D5DEE4"
PANEL = "#F7F9FA"
WARNING = "#A96824"
ACCENT = "#0F4D92"

plt.rcParams.update(
    {
        "font.family": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 8.5,
        "text.color": TEXT,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "figure.facecolor": "#FFFFFF",
        "savefig.facecolor": "#FFFFFF",
    }
)


def _load_counts(path: Path) -> Dict[str, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Score JSON must contain a mapping.")

    loaded: Dict[str, np.ndarray] = {}
    for method_key in ("manual_workflow", "proposed_cad_draft"):
        values = payload.get(method_key)
        if not isinstance(values, Mapping):
            raise ValueError("Missing '{}' score mapping.".format(method_key))
        counts = []
        for category_key, _, _ in CATEGORIES:
            value = values.get(category_key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("{} must be a non-negative integer for '{}'.".format(category_key, method_key))
            counts.append(value)
        array = np.asarray(counts, dtype=np.int64)
        if int(array.sum()) == 0:
            raise ValueError("'{}' contains no scored cases.".format(method_key))
        loaded[method_key] = array
    return loaded


def _panel(ax, title: str, values: np.ndarray, template: bool) -> None:
    colors = [color for _, _, color in CATEGORIES]
    wedges, _ = ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.33, "edgecolor": "#FFFFFF", "linewidth": 1.5},
        radius=1.0,
    )
    if template:
        for wedge in wedges:
            wedge.set_alpha(0.38)
            wedge.set_hatch("//")
        center_top = "TEMPLATE"
        center_bottom = "ratings required"
    else:
        center_top = "n = {}".format(int(values.sum()))
        center_bottom = "case consensus"
        total = float(values.sum())
        for value, wedge in zip(values, wedges):
            if value == 0:
                continue
            theta = np.deg2rad((wedge.theta1 + wedge.theta2) / 2.0)
            x = 1.19 * np.cos(theta)
            y = 1.19 * np.sin(theta)
            ax.text(
                x,
                y,
                "{}\n({:.1f}%)".format(int(value), 100.0 * value / total),
                ha="center",
                va="center",
                fontsize=6.8,
                color=TEXT,
                fontweight="semibold",
            )

    circle = plt.Circle((0.0, 0.0), 0.62, color="#FFFFFF", zorder=2)
    ax.add_artist(circle)
    ax.text(0.0, 0.10, center_top, ha="center", va="center", fontsize=10.0, fontweight="bold", color=ACCENT if not template else WARNING)
    ax.text(0.0, -0.12, center_bottom, ha="center", va="center", fontsize=6.6, color=MUTED)
    ax.set_title(title, fontsize=10.2, fontweight="semibold", color=TEXT, pad=8)
    ax.set(aspect="equal")
    ax.set_axis_off()


def _save(fig: plt.Figure, output_base: Path, dpi: int, formats: Sequence[str]) -> None:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        fig.savefig(output_base.with_suffix("." + fmt), dpi=dpi, bbox_inches="tight", pad_inches=0.03)


def _render(counts: Dict[str, np.ndarray], output_base: Path, dpi: int, template: bool, formats: Sequence[str]) -> None:
    fig = plt.figure(figsize=(180.0 / 25.4, 96.0 / 25.4), dpi=dpi)
    grid = fig.add_gridspec(nrows=1, ncols=2, left=0.16, right=0.98, top=0.68, bottom=0.19, wspace=0.22)

    fig.text(0.10, 0.94, "Blinded technician assessment", ha="left", va="center", fontsize=13.2, fontweight="bold")
    subtitle = "Case-level consensus distribution of prespecified modification need"
    if template:
        subtitle += "  |  layout template only; replace with locked ratings"
    fig.text(0.10, 0.885, subtitle, ha="left", va="center", fontsize=7.7, color=WARNING if template else MUTED)

    ax_manual = fig.add_subplot(grid[0, 0])
    ax_proposed = fig.add_subplot(grid[0, 1])
    _panel(ax_manual, "(a) Manual workflow", counts["manual_workflow"], template)
    _panel(ax_proposed, "(b) Proposed CAD draft", counts["proposed_cad_draft"], template)

    legend_handles = [Patch(facecolor=color, edgecolor="none", label=label) for _, label, color in CATEGORIES]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.58, 0.815),
        ncol=2,
        frameon=False,
        fontsize=6.2,
        handlelength=1.1,
        columnspacing=2.6,
        labelspacing=0.35,
    )
    fig.text(0.10, 0.075, "Unit of analysis: matched case; technician ratings are reconciled before aggregation.", ha="left", va="center", fontsize=6.3, color=MUTED)
    if template:
        fig.text(0.57, 0.47, "TEMPLATE - NOT RESULTS", ha="center", va="center", fontsize=22, fontweight="bold", color=WARNING, alpha=0.10, rotation=15)
        fig.text(0.10, 0.035, "The equal template sectors do not represent score proportions.", ha="left", va="center", fontsize=6.1, color=WARNING)

    _save(fig, output_base, dpi, formats)
    plt.close(fig)
    provenance = {
        "template": template,
        "message": "Template segment widths are non-evidentiary." if template else "Rendered from locked case-level consensus counts.",
        "categories": [key for key, _, _ in CATEGORIES],
    }
    output_base.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--template", action="store_true", help="Render the watermarked planning template.")
    source.add_argument("--data", type=Path, help="JSON file containing locked case-level consensus counts.")
    parser.add_argument("--output-base", type=Path, default=None, help="Output path without a suffix.")
    parser.add_argument("--formats", nargs="+", default=["png", "pdf", "svg"], choices=["png", "pdf", "svg"])
    parser.add_argument("--dpi", type=int, default=600)
    args = parser.parse_args()

    if args.dpi < 300:
        raise ValueError("Use at least 300 dpi for manuscript figures.")

    if args.template:
        counts = {
            "manual_workflow": np.ones(len(CATEGORIES), dtype=np.int64),
            "proposed_cad_draft": np.ones(len(CATEGORIES), dtype=np.int64),
        }
        _render(counts, args.output_base or DEFAULT_TEMPLATE_BASE, args.dpi, True, args.formats)
    else:
        data_path = args.data.expanduser().resolve()
        if not data_path.is_file():
            raise FileNotFoundError("Score JSON not found: {}".format(data_path))
        _render(_load_counts(data_path), args.output_base or DEFAULT_RESULT_BASE, args.dpi, False, args.formats)


if __name__ == "__main__":
    main()
