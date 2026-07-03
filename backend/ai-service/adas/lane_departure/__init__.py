"""Lane Departure Warning package."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .config import LaneDepartureConfig
from .lane_departure_service import LaneDepartureService
from .lane_visualizer import draw_lane_departure_overlay
from .models import FrameData, LaneDepartureBatch, LaneDepartureResult


class LaneDepartureDecision:
    """Compatibility facade used by ADASDecisionEngine."""

    def __init__(self, config: Optional[Any] = None):
        self.service = LaneDepartureService.from_adas_config(config)

    def evaluate_scene(self, scene_context: Any, frame_size: Optional[Tuple[int, int]] = None) -> LaneDepartureBatch:
        return self.service.process_scene(scene_context, frame_size=frame_size)

    def evaluate_vehicle(self, vehicle: Dict[str, Any]) -> List[Any]:
        batch = self.service.process_scene({"frame": 0, "vehicles": [vehicle]})
        return self.service.warning_objects(batch)

    def warnings_from_batch(self, batch: LaneDepartureBatch) -> List[Any]:
        return self.service.warning_objects(batch)


__all__ = [
    "FrameData",
    "LaneDepartureBatch",
    "LaneDepartureConfig",
    "LaneDepartureDecision",
    "LaneDepartureResult",
    "LaneDepartureService",
    "draw_lane_departure_overlay",
]
