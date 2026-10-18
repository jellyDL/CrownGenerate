"""IntraoralScan-style colors, kept separate from the exocad color scale.

Reference: https://docs.shining3d.com/intraoralscan/3.5.2/elite/zh-cn/biteadjust/
RGB values approximate the manual's illustration, not a vendor lookup table.
The 0–0.2 mm range is this project's display setting.
"""
from matplotlib.colors import LinearSegmentedColormap

PENETRATION_COLOR = "#4824ff"
BACKGROUND_COLOR = "white"
DEFAULT_LIMITS = (0.0, 0.2)


def occlusion_colormap():
    cmap = LinearSegmentedColormap.from_list(
        "intraoralscan_style",
        [(0.0, "#ed0000"), (0.25, "#ffb080"),
         (0.5, "#f5ed00"), (0.75, "#8ac72a"), (1.0, "#42b000")],
        N=256,
    )
    cmap.set_under(PENETRATION_COLOR)
    cmap.set_over(BACKGROUND_COLOR)
    cmap.set_bad(BACKGROUND_COLOR)
    return cmap
