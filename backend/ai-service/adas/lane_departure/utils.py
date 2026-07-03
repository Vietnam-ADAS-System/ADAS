"""Common helpers for Lane Departure Warning."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


Point = Tuple[float, float]


def as_dict(value: Any) -> Dict[str, Any]:
    return value.to_dict() if hasattr(value, "to_dict") else dict(value or {})


def parse_center(value: Any) -> Optional[Point]:
    if value is None:
        return None
    if isinstance(value, dict):
        if "center" in value:
            return parse_center(value["center"])
        if "x" in value and "y" in value:
            return float(value["x"]), float(value["y"])
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return float(value[0]), float(value[1])
    return None


def optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

