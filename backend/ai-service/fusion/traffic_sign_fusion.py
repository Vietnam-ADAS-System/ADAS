"""Traffic-sign interpretation for Fusion."""

from __future__ import annotations

from typing import Iterable, Optional

from .data_models import TrafficRule, TrafficSign
from .utils import normalize_traffic_rule_type, parse_speed_limit_value


class TrafficSignFusion:
    """Convert sign detections to the current traffic rule."""

    def interpret(self, traffic_signs: Iterable[TrafficSign]) -> TrafficRule:
        signs = sorted(traffic_signs, key=lambda item: item.confidence, reverse=True)
        if not signs:
            return TrafficRule()

        selected = signs[0]
        rule_type = normalize_traffic_rule_type(selected.type)
        value: Optional[int] = selected.value

        if rule_type == "Speed Limit":
            value = parse_speed_limit_value(selected.value, selected.type)

        return TrafficRule(type=rule_type, value=value)

