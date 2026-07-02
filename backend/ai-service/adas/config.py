"""Configuration for ADAS decision logic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ADASConfig:
    lane_departure_offset_threshold_px: float = 70.0
    speed_tolerance_kmh: float = 0.0

