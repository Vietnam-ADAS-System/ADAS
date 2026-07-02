"""Thresholds for Lane Departure Warning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LaneDepartureConfig:
    safe_threshold_ratio: float = 0.10
    warning_threshold_ratio: float = 0.22
    fallback_safe_threshold_px: float = 35.0
    fallback_warning_threshold_px: float = 70.0
    min_lane_width_px: float = 40.0
    require_tracking_id: bool = False

    @classmethod
    def from_adas_config(cls, config: Any) -> "LaneDepartureConfig":
        if config is None:
            return cls()
        return cls(
            safe_threshold_ratio=float(getattr(config, "ldw_safe_threshold_ratio", cls.safe_threshold_ratio)),
            warning_threshold_ratio=float(getattr(config, "ldw_warning_threshold_ratio", cls.warning_threshold_ratio)),
            fallback_safe_threshold_px=float(
                getattr(config, "ldw_safe_threshold_px", cls.fallback_safe_threshold_px)
            ),
            fallback_warning_threshold_px=float(
                getattr(
                    config,
                    "lane_departure_offset_threshold_px",
                    getattr(config, "ldw_warning_threshold_px", cls.fallback_warning_threshold_px),
                )
            ),
            min_lane_width_px=float(getattr(config, "ldw_min_lane_width_px", cls.min_lane_width_px)),
            require_tracking_id=bool(getattr(config, "ldw_require_tracking_id", cls.require_tracking_id)),
        )

