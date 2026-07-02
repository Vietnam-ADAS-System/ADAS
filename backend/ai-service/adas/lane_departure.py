"""Lane departure and lane-status decisions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config import ADASConfig
from .data_models import Warning


class LaneDepartureDecision:
    def __init__(self, config: Optional[ADASConfig] = None):
        self.config = config or ADASConfig()

    def evaluate_vehicle(self, vehicle: Dict[str, Any]) -> List[Warning]:
        warnings: List[Warning] = []
        track_id = vehicle.get("track_id")
        lane_status = vehicle.get("lane_status")
        offset = vehicle.get("offset")

        if lane_status == "crossing_lane":
            warnings.append(
                Warning(
                    type="Lane Crossing",
                    priority="CRITICAL",
                    message="Vehicle is crossing lane boundary",
                    track_id=track_id,
                )
            )
        elif lane_status == "outside_lane":
            warnings.append(
                Warning(
                    type="Lane Departure",
                    priority="HIGH",
                    message="Vehicle is outside lane",
                    track_id=track_id,
                )
            )
        elif lane_status == "near_boundary":
            warnings.append(
                Warning(
                    type="Lane Boundary",
                    priority="LOW",
                    message="Vehicle is near lane boundary",
                    track_id=track_id,
                )
            )

        if offset is not None and abs(float(offset)) > self.config.lane_departure_offset_threshold_px:
            warnings.append(
                Warning(
                    type="Lane Departure",
                    priority="HIGH",
                    message="Vehicle offset exceeds lane threshold",
                    value=round(float(offset), 2),
                    track_id=track_id,
                )
            )

        return warnings
