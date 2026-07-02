"""Configuration for ADAS decision logic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ADASConfig:
    lane_departure_offset_threshold_px: float = 70.0
    speed_tolerance_kmh: float = 0.0
    ldw_safe_threshold_ratio: float = 0.10
    ldw_warning_threshold_ratio: float = 0.22
    ldw_safe_threshold_px: float = 35.0
    ldw_min_lane_width_px: float = 40.0
    ldw_require_tracking_id: bool = False
