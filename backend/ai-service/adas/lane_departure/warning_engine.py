"""Lane warning decision engine."""

from __future__ import annotations

from .lane_warning import is_warning_status


class LaneWarningEngine:
    def should_warn(self, status: str) -> bool:
        return is_warning_status(status)

