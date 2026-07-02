"""Lane status classification for LDW."""

from __future__ import annotations

from .config import LaneDepartureConfig
from .models import OffsetData


class LaneStatusClassifier:
    def __init__(self, config: LaneDepartureConfig):
        self.config = config

    def classify(self, data: OffsetData) -> str:
        if data.source_lane_status in {"crossing_lane", "outside_lane"}:
            return self._departure_status(data.direction)

        normalized_abs = abs(data.normalized_offset)
        if normalized_abs < self.config.safe_threshold_ratio:
            return "SAFE"
        if normalized_abs < self.config.warning_threshold_ratio:
            return "NEAR_BOUNDARY"
        return self._departure_status(data.direction)

    @staticmethod
    def _departure_status(direction: str) -> str:
        if direction == "LEFT":
            return "LEFT_LANE_DEPARTURE"
        if direction == "RIGHT":
            return "RIGHT_LANE_DEPARTURE"
        return "LANE_DEPARTURE"

