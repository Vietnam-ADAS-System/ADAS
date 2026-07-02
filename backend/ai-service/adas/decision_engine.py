"""ADAS Decision Engine."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from .config import ADASConfig
from .data_models import ADASOutput
from .lane_departure import LaneDepartureDecision
from .traffic_rule import TrafficRuleDecision
from .warning_manager import WarningManager


class ADASDecisionEngine:
    """Evaluate a Fusion SceneContext and produce warnings."""

    def __init__(self, config: Optional[ADASConfig] = None):
        self.config = config or ADASConfig()
        self.lane_departure = LaneDepartureDecision(self.config)
        self.traffic_rule = TrafficRuleDecision(self.config)
        self.warning_manager = WarningManager()

    def evaluate(
        self,
        scene_context: Any,
        current_speed: Optional[float] = None,
        frame_size: Optional[Tuple[int, int]] = None,
    ) -> ADASOutput:
        context = scene_context.to_dict() if hasattr(scene_context, "to_dict") else dict(scene_context or {})
        warnings = []
        lane_batch = self.lane_departure.evaluate_scene(context, frame_size=frame_size)
        lane_departure = lane_batch.to_dict_list()

        warnings.extend(self.lane_departure.warnings_from_batch(lane_batch))

        warnings.extend(self.traffic_rule.evaluate(context.get("traffic_rule", {}), current_speed))

        return ADASOutput(
            frame=int(context.get("frame", 0)),
            warnings=self.warning_manager.organize(warnings),
            lane_departure=lane_departure,
        )
