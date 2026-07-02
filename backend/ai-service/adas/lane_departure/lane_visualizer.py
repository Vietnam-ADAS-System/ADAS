"""OpenCV visualization helpers for LDW output."""

from __future__ import annotations

from typing import Any, Dict, Iterable


STATUS_COLORS = {
    "SAFE": (0, 200, 0),
    "NEAR_BOUNDARY": (0, 220, 255),
    "LEFT_LANE_DEPARTURE": (0, 0, 255),
    "RIGHT_LANE_DEPARTURE": (0, 0, 255),
    "LANE_DEPARTURE": (0, 0, 255),
    "LANE_UNKNOWN": (180, 180, 180),
}


def draw_lane_departure_overlay(frame: Any, results: Iterable[Dict[str, Any]]) -> Any:
    try:
        import cv2
    except ImportError:
        return frame

    output = frame.copy()
    for result in results:
        center = result.get("vehicle_center")
        if isinstance(center, list) and len(center) >= 2:
            cx, cy = int(center[0]), int(center[1])
            status = str(result.get("status", "LANE_UNKNOWN"))
            color = STATUS_COLORS.get(status, (255, 255, 255))
            cv2.circle(output, (cx, cy), 5, color, -1)
            cv2.putText(
                output,
                f"LDW: {status}",
                (max(cx - 80, 5), max(cy - 18, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

        lane_center = result.get("lane_center")
        if lane_center is not None:
            x = int(lane_center)
            cv2.line(output, (x, 0), (x, output.shape[0] - 1), (255, 255, 255), 1)

    return output

