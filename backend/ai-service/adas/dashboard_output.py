"""Dashboard payload builder based on SceneContext and ADAS output."""

from __future__ import annotations

from typing import Any, Dict


class DashboardOutputBuilder:
    def build(self, scene_context: Any, adas_output: Any) -> Dict[str, Any]:
        context = scene_context.to_dict() if hasattr(scene_context, "to_dict") else dict(scene_context or {})
        output = adas_output.to_dict() if hasattr(adas_output, "to_dict") else dict(adas_output or {})
        return {
            "frame": context.get("frame"),
            "vehicle_count": len(context.get("vehicles", [])),
            "traffic_rule": context.get("traffic_rule"),
            "warnings": output.get("warnings", []),
            "timestamp": context.get("timestamp"),
        }

