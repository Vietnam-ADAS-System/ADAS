"""Normalize lane offset by lane width."""

from __future__ import annotations

from typing import Optional


def normalize_offset(offset: float, lane_width: float) -> Optional[float]:
    if lane_width <= 0:
        return None
    return float(offset) / float(lane_width)

