"""ADAS Decision Engine."""

from __future__ import annotations

from typing import Any, Dict, Optional

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

    def evaluate(self, scene_context: Any, current_speed: Optional[float] = None) -> ADASOutput:
        context = scene_context.to_dict() if hasattr(scene_context, "to_dict") else dict(scene_context or {})
        warnings = []

        for vehicle in context.get("vehicles", []):
            warnings.extend(self.lane_departure.evaluate_vehicle(vehicle))

        warnings.extend(self.traffic_rule.evaluate(context.get("traffic_rule", {}), current_speed))

        return ADASOutput(
            frame=int(context.get("frame", 0)),
            warnings=self.warning_manager.organize(warnings),
        )

