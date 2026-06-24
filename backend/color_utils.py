import math
import random
from collections.abc import Iterable, Sequence


ColorEntry = dict[str, str]
LabColor = tuple[float, float, float]
RgbColor = tuple[int, int, int]


def hex_to_rgb(hex_color: str) -> RgbColor:
    value = hex_color.removeprefix("#")
    if len(value) != 6:
        raise ValueError(f"Expected 6-digit hex color, got {hex_color!r}")
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


def _srgb_to_linear(channel: int) -> float:
    normalized = channel / 255
    if normalized <= 0.04045:
        return normalized / 12.92
    return ((normalized + 0.055) / 1.055) ** 2.4


def rgb_to_lab(r: int, g: int, b: int) -> LabColor:
    linear_r = _srgb_to_linear(r)
    linear_g = _srgb_to_linear(g)
    linear_b = _srgb_to_linear(b)

    x = linear_r * 0.4124 + linear_g * 0.3576 + linear_b * 0.1805
    y = linear_r * 0.2126 + linear_g * 0.7152 + linear_b * 0.0722
    z = linear_r * 0.0193 + linear_g * 0.1192 + linear_b * 0.9505

    return (
        (116 * _lab_pivot(y / 1.00000)) - 16,
        500 * (_lab_pivot(x / 0.95047) - _lab_pivot(y / 1.00000)),
        200 * (_lab_pivot(y / 1.00000) - _lab_pivot(z / 1.08883)),
    )


def _lab_pivot(value: float) -> float:
    if value > 0.008856:
        return value ** (1 / 3)
    return (7.787 * value) + (16 / 116)


def color_distance(hex1: str, hex2: str) -> float:
    lab1 = rgb_to_lab(*hex_to_rgb(hex1))
    lab2 = rgb_to_lab(*hex_to_rgb(hex2))
    return math.sqrt(
        (lab1[0] - lab2[0]) ** 2
        + (lab1[1] - lab2[1]) ** 2
        + (lab1[2] - lab2[2]) ** 2
    )


def pick_most_distinct_color(
    palette: Sequence[ColorEntry],
    used_bgs: Iterable[str],
) -> ColorEntry:
    used = set(used_bgs)
    if not used:
        return random.choice(palette)

    best_score = -1.0
    best: list[ColorEntry] = []
    for entry in palette:
        score = min(color_distance(entry["bg"], used_bg) for used_bg in used)
        if score > best_score:
            best_score = score
            best = [entry]
        elif score == best_score:
            best.append(entry)

    return random.choice(best)
