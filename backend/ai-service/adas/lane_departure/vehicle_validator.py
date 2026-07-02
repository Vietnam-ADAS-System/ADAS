"""Vehicle-center validation."""

from __future__ import annotations

from typing import List, Optional, Tuple

from .models import ValidationError


Point = Tuple[float, float]


def validate_vehicle_center(
    center: Optional[Point],
    image_width: Optional[int] = None,
    image_height: Optional[int] = None,
) -> List[ValidationError]:
    errors: List[ValidationError] = []
    if center is None:
        return [ValidationError("MISSING_VEHICLE_CENTER", "Vehicle center is missing.")]

    cx, cy = center
    if image_width is not None and not (0 <= cx <= image_width):
        errors.append(ValidationError("INVALID_VEHICLE_CENTER_X", "Vehicle center x is outside frame."))
    if image_height is not None and not (0 <= cy <= image_height):
        errors.append(ValidationError("INVALID_VEHICLE_CENTER_Y", "Vehicle center y is outside frame."))
    return errors

