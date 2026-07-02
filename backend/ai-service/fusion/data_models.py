"""Typed data models shared by Fusion modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


Point = Tuple[float, float]


@dataclass(frozen=True)
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def center(self) -> Point:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    def to_list(self) -> List[float]:
        return [self.x1, self.y1, self.x2, self.y2]

    def to_dict(self) -> Dict[str, float]:
        return {
            "x1": round(self.x1, 2),
            "y1": round(self.y1, 2),
            "x2": round(self.x2, 2),
            "y2": round(self.y2, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
        }


@dataclass(frozen=True)
class VehicleDetection:
    id: int
    type: str
    bbox: BoundingBox
    confidence: float


@dataclass(frozen=True)
class PedestrianDetection:
    id: int
    bbox: BoundingBox
    confidence: float


@dataclass(frozen=True)
class LaneInfo:
    lane_left: Optional[Any] = None
    lane_right: Optional[Any] = None
    lane_center: Optional[Any] = None
    mask: Optional[Any] = None


@dataclass(frozen=True)
class TrafficSign:
    type: str
    value: Optional[int] = None
    bbox: Optional[BoundingBox] = None
    confidence: float = 0.0


@dataclass(frozen=True)
class TrackInfo:
    track_id: int
    bbox: BoundingBox
    type: str = "vehicle"


@dataclass(frozen=True)
class TrafficRule:
    type: Optional[str] = None
    value: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        if self.type is None:
            return {"type": None, "value": None}
        data: Dict[str, Any] = {"type": self.type}
        if self.value is not None:
            data["value"] = self.value
        return data


@dataclass(frozen=True)
class VehicleLaneState:
    detection_id: int
    type: str
    center: Point
    lane: str
    lane_status: str
    offset: Optional[float]


@dataclass(frozen=True)
class TrackingAssociation:
    detection_id: int
    track_id: Optional[int]
    tracking: bool


@dataclass(frozen=True)
class VehicleScene:
    track_id: Optional[int]
    type: str
    lane: str
    lane_status: str
    offset: Optional[float]
    center: Point
    speed: Optional[float] = None
    tracking: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "type": self.type,
            "lane": self.lane,
            "lane_status": self.lane_status,
            "offset": None if self.offset is None else round(self.offset, 2),
            "center": [round(self.center[0], 2), round(self.center[1], 2)],
            "speed": self.speed,
            "tracking": self.tracking,
        }


@dataclass(frozen=True)
class PedestrianScene:
    track_id: Optional[int]
    center: Point
    tracking: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "center": [round(self.center[0], 2), round(self.center[1], 2)],
            "tracking": self.tracking,
        }


@dataclass(frozen=True)
class SceneContext:
    frame: int
    vehicles: Sequence[VehicleScene] = field(default_factory=list)
    traffic_rule: TrafficRule = field(default_factory=TrafficRule)
    timestamp: Optional[str] = None
    pedestrians: Sequence[PedestrianScene] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "frame": self.frame,
            "vehicles": [vehicle.to_dict() for vehicle in self.vehicles],
            "traffic_rule": self.traffic_rule.to_dict(),
            "timestamp": self.timestamp,
        }
        if self.pedestrians:
            data["pedestrians"] = [item.to_dict() for item in self.pedestrians]
        return data

