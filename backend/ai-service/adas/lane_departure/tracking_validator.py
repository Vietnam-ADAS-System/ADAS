"""Tracking validation."""

from __future__ import annotations

from typing import List, Optional

from .config import LaneDepartureConfig
from .models import ValidationError


def validate_tracking_id(tracking_id: Optional[int], config: LaneDepartureConfig) -> List[ValidationError]:
    if tracking_id is None and config.require_tracking_id:
        return [ValidationError("MISSING_TRACKING_ID", "Tracking ID is missing.")]
    return []

