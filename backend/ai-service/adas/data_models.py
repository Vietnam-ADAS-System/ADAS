"""Data models emitted by the ADAS layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


PRIORITY_RANK = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "INFO": 0,
}


@dataclass(frozen=True)
class Warning:
    type: str
    priority: str
    message: str
    action: Optional[str] = None
    value: Optional[Any] = None
    track_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "type": self.type,
            "priority": self.priority,
            "message": self.message,
        }
        if self.action is not None:
            data["action"] = self.action
        if self.value is not None:
            data["value"] = self.value
        if self.track_id is not None:
            data["track_id"] = self.track_id
        return data


def normalize_priority(priority: Any) -> str:
    value = str(priority or "INFO").upper()
    return value if value in PRIORITY_RANK else "INFO"


def warning_from_any(value: Any) -> Warning:
    if isinstance(value, Warning):
        return value

    if isinstance(value, dict):
        track_id = value.get("track_id")
        try:
            track_id = None if track_id is None else int(track_id)
        except (TypeError, ValueError):
            track_id = None

        return Warning(
            type=str(value.get("type", "UNKNOWN")),
            priority=normalize_priority(value.get("priority")),
            message=str(value.get("message", value.get("type", "Warning"))),
            action=value.get("action"),
            value=value.get("value"),
            track_id=track_id,
        )

    return Warning(
        type=type(value).__name__,
        priority="INFO",
        message=str(value),
    )


@dataclass(frozen=True)
class ADASOutput:
    frame: int
    warnings: Sequence[Warning] = field(default_factory=list)
    lane_departure: Sequence[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "warnings": [warning_from_any(warning).to_dict() for warning in self.warnings],
            "lane_departure": list(self.lane_departure),
        }
