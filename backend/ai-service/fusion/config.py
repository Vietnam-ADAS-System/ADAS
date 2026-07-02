"""Configuration for the Fusion layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FusionConfig:
    """Tunable thresholds for logic-only Fusion processing."""

    detection_confidence_threshold: float = 0.5
    tracking_iou_threshold: float = 0.3
    lane_boundary_margin_px: float = 25.0
    lane_center_deadzone_px: float = 15.0

