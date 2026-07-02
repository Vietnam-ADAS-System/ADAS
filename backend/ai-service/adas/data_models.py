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


@dataclass(frozen=True)
class ADASOutput:
    frame: int
    warnings: Sequence[Warning] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "warnings": [warning.to_dict() for warning in self.warnings],
        }

