"""Traffic-rule decision router."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config import ADASConfig
from .data_models import Warning
from .no_entry_warning import NoEntryWarningDecision
from .speed_limit import SpeedLimitDecision
from .stop_warning import StopWarningDecision


class TrafficRuleDecision:
    def __init__(self, config: Optional[ADASConfig] = None):
        self.config = config or ADASConfig()
        self.stop_warning = StopWarningDecision()
        self.no_entry_warning = NoEntryWarningDecision()
        self.speed_limit = SpeedLimitDecision(self.config)

    def evaluate(self, traffic_rule: Dict[str, Any], current_speed: Optional[float] = None) -> List[Warning]:
        rule_type = traffic_rule.get("type") if traffic_rule else None
        if not rule_type:
            return []

        if rule_type == "STOP":
            return [self.stop_warning.evaluate()]
        if rule_type == "NO_ENTRY":
            return [self.no_entry_warning.evaluate()]
        if rule_type == "Speed Limit":
            warning = self.speed_limit.evaluate(traffic_rule.get("value"), current_speed)
            return [warning] if warning is not None else []

        return [
            Warning(
                type=str(rule_type),
                priority="INFO",
                message=f"Traffic rule detected: {rule_type}",
                value=traffic_rule.get("value"),
            )
        ]
