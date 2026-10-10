#!/usr/bin/env python3
"""Plot manuscript-reported technician modification proportions.

These are case-level aggregate percentages, not individual technician scores.
Raw ratings and case counts are not present in this repository. The fifth
rubric level (unusable) is not reported, so it is not assigned a zero value.
Run: python figures/generate_figure5_technician_score_distribution.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_STEM = "figure5_technician_score_distribution_template"
# Sources: main.tex, Blinded Technician Assessment; manuscript_zh_v0.1.md,
# 技师盲评与临床适用性. Values have not been checked against raw rating records.
CATEGORIES = ("No modification", "Minor modification", "Moderate modification", "Major modification")
METHODS = (
    ("Manual design", (65.2, 23.8, 8.5, 2.5), "#E69F00", "//"),
    ("Proposed CAD draft", (68.5, 22.1, 7.2, 2.2), "#0072B2", None),
)


def main() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 12,
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 12,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "hatch.linewidth": 0.45,
        "savefig.dpi": 300,
    })
    fig, ax = plt.subplots(figsize=(7.4, 4.7))
    fig.subplots_adjust(left=0.31, right=0.96, bottom=0.23, top=0.72)
    fig.text(0.04, 0.945, "Blinded technician assessment", fontsize=17,
             fontweight="bold", color="#24323D", va="top")
    fig.text(0.04, 0.868, "Case-level distribution of modification requirements",
             fontsize=12, color="#56616B", va="top")

    y = np.arange(len(CATEGORIES))[::-1]
    height = 0.30
    for index, (method, values, color, hatch) in enumerate(METHODS):
        if len(values) != len(CATEGORIES) or not np.isclose(sum(values), 100):
            raise ValueError(f"Invalid percentage distribution: {method}")
        bars = ax.barh(y + (0.17 if index == 0 else -0.17), values,
                       height=height, color=color, label=method,
                       hatch=hatch, edgecolor="white", linewidth=0.7, zorder=3)
        for bar, value in zip(bars, values):
            ax.text(value + 1.2, bar.get_y() + bar.get_height() / 2,
                    f"{value:.1f}%", va="center", fontsize=11, color="#24323D")
    ax.set_yticks(y, CATEGORIES)
    ax.set_ylim(-0.55, len(CATEGORIES) - 0.45)
    ax.set_xlim(0, 80)
    ax.set_xticks(np.arange(0, 81, 20))
    ax.set_xlabel("Cases (%)", labelpad=8)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#DDE2E6", linewidth=0.65)
    ax.tick_params(axis="y", length=0, pad=10)
    ax.tick_params(axis="x", length=3, color="#AAB2B9")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#AAB2B9")
    fig.legend(*ax.get_legend_handles_labels(), loc="upper left",
               bbox_to_anchor=(0.305, 0.825), ncol=2, frameon=False,
               fontsize=11, handlelength=1.7, columnspacing=1.5)
    fig.text(0.04, 0.070, "Source: manuscript-reported percentages; raw ratings pending verification.",
             fontsize=9.5, color="#65717B")
    fig.text(0.04, 0.030, "Fifth rubric level (unusable): not reported; individual-rater scores unavailable.",
             fontsize=9.5, color="#65717B")
    for extension in ("png", "pdf"):
        output = OUTPUT_DIR / f"{OUTPUT_STEM}.{extension}"
        fig.savefig(output, facecolor="white")
        print(f"Saved {output}")
    plt.close(fig)


if __name__ == "__main__":
    main()
