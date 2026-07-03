"""Lane Departure Warning input validation."""

from __future__ import annotations

from typing import List

from .config import LaneDepartureConfig
from .frame_validator import validate_frame_id
from .lane_center import calculate_lane_center
from .lane_validator import validate_lane_geometry
from .models import FrameData, ValidatedFrameData, ValidationError, ValidationResult
from .tracking_validator import validate_tracking_id
from .vehicle_validator import validate_vehicle_center


class LaneDepartureValidator:
    def __init__(self, config: LaneDepartureConfig):
        self.config = config

    def validate(self, frame_data: FrameData) -> ValidationResult:
        lane_center = frame_data.lane_center
        if lane_center is None:
            lane_center = calculate_lane_center(frame_data.lane_left, frame_data.lane_right)

        errors: List[ValidationError] = []
        errors.extend(validate_frame_id(frame_data.frame_id))
        errors.extend(validate_vehicle_center(frame_data.vehicle_center, frame_data.image_width, frame_data.image_height))
        errors.extend(validate_lane_geometry(frame_data.lane_left, frame_data.lane_right, lane_center, self.config))
        errors.extend(validate_tracking_id(frame_data.tracking_id, self.config))

        if errors:
            return ValidationResult(valid=False, errors=tuple(errors))

        return ValidationResult(
            valid=True,
            data=ValidatedFrameData(
                frame_id=frame_data.frame_id,
                vehicle_id=frame_data.vehicle_id,
                tracking_id=frame_data.tracking_id,
                vehicle_center=frame_data.vehicle_center,  # type: ignore[arg-type]
                lane_left=float(frame_data.lane_left),  # type: ignore[arg-type]
                lane_right=float(frame_data.lane_right),  # type: ignore[arg-type]
                lane_center=float(lane_center),  # type: ignore[arg-type]
                image_width=frame_data.image_width,
                image_height=frame_data.image_height,
                source_lane_status=frame_data.source_lane_status,
            ),
        )

