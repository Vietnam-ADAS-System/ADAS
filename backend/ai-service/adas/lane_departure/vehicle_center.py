"""Vehicle center helpers."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple


Point = Tuple[float, float]


def calculate_vehicle_center(bbox: Sequence[float]) -> Optional[Point]:
    if len(bbox) < 4:
        return None
    x1, y1, x2, y2 = [float(item) for item in bbox[:4]]
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0

