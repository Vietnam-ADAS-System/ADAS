"""Lane-geometry validation."""

from __future__ import annotations

from typing import List, Optional

from .config import LaneDepartureConfig
from .lane_width import calculate_lane_width
from .models import ValidationError


def validate_lane_geometry(
    lane_left: Optional[float],
    lane_right: Optional[float],
    lane_center: Optional[float],
    config: LaneDepartureConfig,
) -> List[ValidationError]:
    errors: List[ValidationError] = []
    if lane_left is None or lane_right is None:
        errors.append(ValidationError("MISSING_LANE_BOUNDARY", "Lane boundary is missing."))
        return errors

    if lane_left >= lane_right:
        errors.append(ValidationError("INVALID_LANE_ORDER", "Lane left must be smaller than lane right."))

    lane_width = calculate_lane_width(lane_left, lane_right)
    if lane_width < config.min_lane_width_px:
        errors.append(ValidationError("LANE_WIDTH_TOO_SMALL", "Lane width is smaller than minimum threshold."))

    if lane_center is None:
        errors.append(ValidationError("MISSING_LANE_CENTER", "Lane center is missing."))
    elif not (min(lane_left, lane_right) <= lane_center <= max(lane_left, lane_right)):
        errors.append(ValidationError("INVALID_LANE_CENTER", "Lane center must be inside lane boundaries."))

    return errors

