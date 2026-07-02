"""Lane offset calculation."""

from __future__ import annotations


def calculate_lane_offset(vehicle_center_x: float, lane_center: float) -> float:
    return float(vehicle_center_x) - float(lane_center)

