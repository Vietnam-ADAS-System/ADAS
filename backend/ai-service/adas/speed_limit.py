"""Speed-limit decision."""

from __future__ import annotations

from typing import Optional

from .config import ADASConfig
from .data_models import Warning


class SpeedLimitDecision:
    def __init__(self, config: Optional[ADASConfig] = None):
        self.config = config or ADASConfig()

    def evaluate(self, limit: Optional[int], current_speed: Optional[float]) -> Optional[Warning]:
        if limit is None:
            return None

        if current_speed is None:
            return Warning(
                type="Speed Limit",
                priority="INFO",
                message=f"Speed limit {limit} km/h",
                value=limit,
            )

        if float(current_speed) > float(limit) + self.config.speed_tolerance_kmh:
            return Warning(
                type="Overspeed",
                priority="HIGH",
                message="Vehicle speed exceeds current speed limit",
                value={"limit": limit, "current_speed": round(float(current_speed), 2)},
            )

        return None
