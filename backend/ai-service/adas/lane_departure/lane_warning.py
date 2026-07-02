"""Warning generation for Lane Departure Warning."""

from __future__ import annotations

from typing import Optional

from ..data_models import Warning
from .models import LaneDepartureResult


def is_warning_status(status: str) -> bool:
    return status in {"LEFT_LANE_DEPARTURE", "RIGHT_LANE_DEPARTURE", "LANE_DEPARTURE"}


def warning_from_result(result: LaneDepartureResult) -> Optional[Warning]:
    if not result.warning:
        return None

    if result.status == "LEFT_LANE_DEPARTURE":
        message = "Vehicle is departing to the left lane boundary"
        warning_type = "Left Lane Departure"
    elif result.status == "RIGHT_LANE_DEPARTURE":
        message = "Vehicle is departing to the right lane boundary"
        warning_type = "Right Lane Departure"
    else:
        message = "Vehicle is departing from lane"
        warning_type = "Lane Departure"

    return Warning(
        type=warning_type,
        priority="HIGH",
        message=message,
        value={
            "offset": result.offset,
            "normalized_offset": result.normalized_offset,
            "direction": result.direction,
            "status": result.status,
        },
        track_id=result.tracking_id,
    )

