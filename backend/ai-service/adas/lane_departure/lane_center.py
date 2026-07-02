"""Lane center helpers."""

from __future__ import annotations

from typing import Optional


def calculate_lane_center(lane_left: Optional[float], lane_right: Optional[float]) -> Optional[float]:
    if lane_left is None or lane_right is None:
        return None
    left, right = sorted((float(lane_left), float(lane_right)))
    return (left + right) / 2.0

