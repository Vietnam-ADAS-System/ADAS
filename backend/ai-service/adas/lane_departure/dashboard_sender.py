"""Dashboard payload builder for LDW."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .models import LaneDepartureResult


class LaneDashboardSender:
    def build_payload(self, results: Iterable[LaneDepartureResult]) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = [result.to_dict() for result in results]
        return {
            "lane_departure": items,
            "warning_count": sum(1 for item in items if item.get("warning")),
        }

