"""Lane width calculation."""

from __future__ import annotations


def calculate_lane_width(lane_left: float, lane_right: float) -> float:
    return abs(float(lane_right) - float(lane_left))

