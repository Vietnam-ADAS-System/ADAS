"""Frame synchronization validation."""

from __future__ import annotations

from typing import List, Optional

from .models import ValidationError


def validate_frame_id(frame_id: Optional[int]) -> List[ValidationError]:
    if frame_id is None:
        return [ValidationError("MISSING_FRAME_ID", "Frame ID is missing.")]
    if frame_id < 0:
        return [ValidationError("INVALID_FRAME_ID", "Frame ID must be non-negative.")]
    return []

