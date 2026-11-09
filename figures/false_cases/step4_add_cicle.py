#!/usr/bin/env python3
"""Draw configurable ellipse annotations on the failure-case figure.

Each item in ``ELLIPSES`` is independent. By default, positions and radii use
percentages of the image width/height, so the configuration remains valid if
the source figure is regenerated at a different resolution.

Available per-ellipse options:
    name           Optional identifier used in the console output.
    enabled        Set to False to temporarily hide the ellipse.
    units          "percent" (default) or "px".
    center         (x, y) in the selected units.
    radii          (radius_x, radius_y) in the selected units.
    rotation_deg   Clockwise rotation in degrees.
    color          Outline color as an RGB tuple.
    alpha          Outline opacity in [0, 1].
    line_width_px  Outline width in output-image pixels.
    dashed         True for a dashed outline, False for a solid outline.
    dash_px        Dash length in output-image pixels.
    gap_px         Gap length in output-image pixels.
"""

from __future__ import annotations

import bisect
import math
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required. Install it with: pip install Pillow") from exc


HERE = Path(__file__).resolve().parent
INPUT_IMAGE = HERE / "merged_heatmaps.png"
OUTPUT_IMAGE = HERE / "merged_heatmaps_annotated.png"

# Draw the annotations at 4x resolution, then downsample for smooth edges.
SUPERSAMPLE = 4
ELLIPSE_SAMPLES = 1800
ARC_SAMPLE_STEP_PX = 3.0


ELLIPSES: list[dict[str, Any]] = [
    {
        "name": "row1-1",
        "enabled": True,
        "units": "percent", # 按图像宽高的百分比定位
        "center": (39, 10.5), # 椭圆中心
        "radii": (4, 3.8), # 椭圆横、纵半径 
        "rotation_deg": 0, # 旋转角度 
        "color": (225, 35, 35), # 
        "alpha": 1.0, # 透明度
        "line_width_px": 20, # 线宽
        "dashed": True, # True 为虚线，False 为实线
        "dash_px": 40, # 单段虚线长度
        "gap_px": 20,  # 相邻虚线之间的间隔
    },
    {
        "name": "row1-2",
        "enabled": True,
        "units": "percent", # 按图像宽高的百分比定位
        "center": (40, 19), # 椭圆中心
        "radii": (5, 3.2), # 椭圆横、纵半径 
        "rotation_deg": 0, # 旋转角度 
        "color": (225, 35, 35), # 
        "alpha": 1.0, # 透明度
        "line_width_px": 20, # 线宽
        "dashed": True, # True 为虚线，False 为实线
        "dash_px": 40, # 单段虚线长度
        "gap_px": 20,  # 相邻虚线之间的间隔
    },
    {
        "name": "row2-1",
        "enabled": True,
        "units": "percent", # 按图像宽高的百分比定位
        "center": (42, 38.5), # 椭圆中心
        "radii": (5, 6), # 椭圆横、纵半径 
        "rotation_deg": 0, # 旋转角度 
        "color": (225, 35, 35), # 
        "alpha": 1.0, # 透明度
        "line_width_px": 20, # 线宽
        "dashed": True, # True 为虚线，False 为实线
        "dash_px": 40, # 单段虚线长度
        "gap_px": 20,  # 相邻虚线之间的间隔
    },
    {
        "name": "row3-1",
        "enabled": True,
        "units": "percent", # 按图像宽高的百分比定位
        "center": (37, 59), # 椭圆中心
        "radii": (4.5, 4.2), # 椭圆横、纵半径 
        "rotation_deg": 0, # 旋转角度 
        "color": (225, 35, 35), # 
        "alpha": 1.0, # 透明度
        "line_width_px": 20, # 线宽
        "dashed": True, # True 为虚线，False 为实线
        "dash_px": 40, # 单段虚线长度
        "gap_px": 20,  # 相邻虚线之间的间隔
    },
    {
        "name": "row4-1",
        "enabled": True,
        "units": "percent", # 按图像宽高的百分比定位
        "center": (36.5, 82.8), # 椭圆中心
        "radii": (4.2, 3.5), # 椭圆横、纵半径 
        "rotation_deg": 0, # 旋转角度 
        "color": (225, 35, 35), # 
        "alpha": 1.0, # 透明度
        "line_width_px": 20, # 线宽
        "dashed": True, # True 为虚线，False 为实线
        "dash_px": 40, # 单段虚线长度
        "gap_px": 20,  # 相邻虚线之间的间隔
    },
    {
        "name": "row4-2",
        "enabled": True,
        "units": "percent", # 按图像宽高的百分比定位
        "center": (37.2, 93.2), # 椭圆中心
        "radii": (4.7, 3.8), # 椭圆横、纵半径 
        "rotation_deg": 0, # 旋转角度 
        "color": (225, 35, 35), # 
        "alpha": 1.0, # 透明度
        "line_width_px": 20, # 线宽
        "dashed": True, # True 为虚线，False 为实线
        "dash_px": 40, # 单段虚线长度
        "gap_px": 20,  # 相邻虚线之间的间隔
    },
]


def _geometry(cfg: dict[str, Any], width: int, height: int, scale: int) -> tuple[float, float, float, float]:
    units = cfg.get("units", "percent").lower()
    cx, cy = (float(v) for v in cfg["center"])
    rx, ry = (float(v) for v in cfg["radii"])

    if units == "percent":
        cx *= width / 100.0
        rx *= width / 100.0
        cy *= height / 100.0
        ry *= height / 100.0
    elif units != "px":
        raise ValueError(f"{cfg.get('name', '<unnamed>')}: units must be 'percent' or 'px'")

    if rx <= 0 or ry <= 0:
        raise ValueError(f"{cfg.get('name', '<unnamed>')}: radii must be positive")

    return cx * scale, cy * scale, rx * scale, ry * scale


def _ellipse_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    rotation_deg: float,
    count: int = ELLIPSE_SAMPLES,
) -> list[tuple[float, float]]:
    angle = math.radians(rotation_deg)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    points: list[tuple[float, float]] = []

    for i in range(count + 1):
        t = 2.0 * math.pi * i / count
        x, y = rx * math.cos(t), ry * math.sin(t)
        points.append((cx + x * cos_a - y * sin_a, cy + x * sin_a + y * cos_a))

    return points


def _cumulative_lengths(points: list[tuple[float, float]]) -> list[float]:
    distances = [0.0]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        distances.append(distances[-1] + math.hypot(x1 - x0, y1 - y0))
    return distances


def _point_at_distance(
    points: list[tuple[float, float]],
    distances: list[float],
    distance: float,
) -> tuple[float, float]:
    total = distances[-1]
    if distance <= 0.0:
        return points[0]
    if distance >= total:
        return points[-1]

    index = bisect.bisect_right(distances, distance) - 1
    segment = distances[index + 1] - distances[index]
    ratio = 0.0 if segment == 0 else (distance - distances[index]) / segment
    x0, y0 = points[index]
    x1, y1 = points[index + 1]
    return (x0 + ratio * (x1 - x0), y0 + ratio * (y1 - y0))


def _arc_segment(
    points: list[tuple[float, float]],
    distances: list[float],
    start: float,
    end: float,
    step_px: float,
) -> list[tuple[float, float]]:
    count = max(2, math.ceil((end - start) / step_px) + 1)
    return [
        _point_at_distance(points, distances, start + (end - start) * i / (count - 1))
        for i in range(count)
    ]


def _draw_dashed(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    dash_px: float,
    gap_px: float,
    fill: tuple[int, int, int, int],
    line_width: int,
    scale: int,
) -> None:
    distances = _cumulative_lengths(points)
    perimeter = distances[-1]
    dash = dash_px * scale
    gap = gap_px * scale
    step = ARC_SAMPLE_STEP_PX * scale
    position = 0.0

    while position < perimeter:
        dash_end = min(position + dash, perimeter)
        segment = _arc_segment(points, distances, position, dash_end, step)
        if len(segment) >= 2:
            draw.line(segment, fill=fill, width=line_width, joint="curve")
        position = dash_end + gap


def _draw_ellipse(
    draw: ImageDraw.ImageDraw,
    cfg: dict[str, Any],
    width: int,
    height: int,
    scale: int,
) -> None:
    cx, cy, rx, ry = _geometry(cfg, width, height, scale)
    points = _ellipse_points(cx, cy, rx, ry, float(cfg.get("rotation_deg", 0)))

    rgb = tuple(int(v) for v in cfg.get("color", (225, 35, 35)))
    if len(rgb) != 3 or any(v < 0 or v > 255 for v in rgb):
        raise ValueError(f"{cfg.get('name', '<unnamed>')}: color must be an RGB tuple")
    alpha = max(0.0, min(1.0, float(cfg.get("alpha", 1.0))))
    fill = (*rgb, round(255 * alpha))

    line_width = max(1, round(float(cfg.get("line_width_px", 6)) * scale))
    if bool(cfg.get("dashed", False)):
        _draw_dashed(
            draw,
            points,
            float(cfg.get("dash_px", 24)),
            float(cfg.get("gap_px", 14)),
            fill,
            line_width,
            scale,
        )
    else:
        draw.line(points, fill=fill, width=line_width, joint="curve")


def annotate(image: Image.Image, configs: list[dict[str, Any]]) -> Image.Image:
    base = image.convert("RGBA")
    width, height = base.size
    overlay_hi = Image.new("RGBA", (width * SUPERSAMPLE, height * SUPERSAMPLE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay_hi, "RGBA")

    active = 0
    for cfg in configs:
        if not bool(cfg.get("enabled", True)):
            continue
        _draw_ellipse(draw, cfg, width, height, SUPERSAMPLE)
        active += 1

    overlay = overlay_hi.resize((width, height), Image.Resampling.LANCZOS)
    result = Image.alpha_composite(base, overlay)
    result.info["annotated_ellipses"] = active
    return result


def main() -> None:
    if not INPUT_IMAGE.exists():
        raise SystemExit(f"Input image not found: {INPUT_IMAGE}")

    with Image.open(INPUT_IMAGE) as source:
        result = annotate(source, ELLIPSES)

    result.convert("RGB").save(OUTPUT_IMAGE)
    print(f"Saved {OUTPUT_IMAGE} with {result.info['annotated_ellipses']} ellipse annotations.")


if __name__ == "__main__":
    main()
