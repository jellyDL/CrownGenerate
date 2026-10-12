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
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 9.5,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "hatch.linewidth": 0.45,
        "savefig.dpi": 300,
    })
    # Compact, title-free layout: the manuscript caption supplies the title.
    fig, ax = plt.subplots(figsize=(6.8, 3.65))
    fig.subplots_adjust(left=0.30, right=0.96, bottom=0.20, top=0.77)

    y = np.arange(len(CATEGORIES))[::-1]
    height = 0.29
    for index, (method, values, color, hatch) in enumerate(METHODS):
        if len(values) != len(CATEGORIES) or not np.isclose(sum(values), 100):
            raise ValueError(f"Invalid percentage distribution: {method}")
        bars = ax.barh(y + (0.16 if index == 0 else -0.16), values,
                       height=height, color=color, label=method,
                       hatch=hatch, edgecolor="white", linewidth=0.65, zorder=3)
        for bar, value in zip(bars, values):
            ax.text(value + 1.2, bar.get_y() + bar.get_height() / 2,
                    f"{value:.1f}%", va="center", fontsize=9, color="#24323D")
    ax.set_yticks(y, CATEGORIES)
    ax.set_ylim(-0.55, len(CATEGORIES) - 0.45)
    ax.set_xlim(0, 80)
    ax.set_xticks(np.arange(0, 81, 20))
    ax.set_xlabel("Cases (%)", labelpad=5)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#D9DEE3", linewidth=0.55)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.tick_params(axis="x", length=3, color="#AAB2B9")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#9EA7AF")
    ax.set_title("Modification requirement distribution", loc="left", pad=10,
                 fontsize=11, fontweight="bold", color="#26343F")
    fig.legend(*ax.get_legend_handles_labels(), loc="upper left",
               bbox_to_anchor=(0.30, 0.985), ncol=2, frameon=False,
               fontsize=9, handlelength=1.5, columnspacing=1.2)
    for extension in ("png", "pdf"):
        output = OUTPUT_DIR / f"{OUTPUT_STEM}.{extension}"
        fig.savefig(output, facecolor="white")
        print(f"Saved {output}")
    plt.close(fig)


if __name__ == "__main__":
    main()
