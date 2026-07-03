"""Data models for Lane Departure Warning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


Point = Tuple[float, float]


@dataclass(frozen=True)
class FrameData:
    frame_id: int
    vehicle_id: Optional[int]
    tracking_id: Optional[int]
    vehicle_center: Optional[Point]
    lane_left: Optional[float]
    lane_right: Optional[float]
    lane_center: Optional[float]
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    source_lane_status: Optional[str] = None


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class ValidatedFrameData:
    frame_id: int
    vehicle_id: Optional[int]
    tracking_id: Optional[int]
    vehicle_center: Point
    lane_left: float
    lane_right: float
    lane_center: float
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    source_lane_status: Optional[str] = None


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    data: Optional[ValidatedFrameData] = None
    errors: Sequence[ValidationError] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [error.to_dict() for error in self.errors],
        }


@dataclass(frozen=True)
class OffsetData:
    frame_id: int
    vehicle_id: Optional[int]
    tracking_id: Optional[int]
    vehicle_center: Point
    lane_left: float
    lane_right: float
    lane_center: float
    lane_width: float
    offset: float
    normalized_offset: float
    direction: str
    source_lane_status: Optional[str] = None


@dataclass(frozen=True)
class LaneDepartureResult:
    vehicle_id: Optional[int]
    tracking_id: Optional[int]
    frame_id: int
    offset: Optional[float]
    normalized_offset: Optional[float]
    direction: str
    status: str
    warning: bool
    vehicle_center: Optional[Point] = None
    lane_left: Optional[float] = None
    lane_right: Optional[float] = None
    lane_center: Optional[float] = None
    lane_width: Optional[float] = None
    errors: Sequence[ValidationError] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vehicle_id": self.vehicle_id,
            "tracking_id": self.tracking_id,
            "frame_id": self.frame_id,
            "offset": None if self.offset is None else round(self.offset, 3),
            "normalized_offset": None if self.normalized_offset is None else round(self.normalized_offset, 4),
            "direction": self.direction,
            "status": self.status,
            "warning": self.warning,
            "vehicle_center": None
            if self.vehicle_center is None
            else [round(self.vehicle_center[0], 2), round(self.vehicle_center[1], 2)],
            "lane_left": None if self.lane_left is None else round(self.lane_left, 2),
            "lane_right": None if self.lane_right is None else round(self.lane_right, 2),
            "lane_center": None if self.lane_center is None else round(self.lane_center, 2),
            "lane_width": None if self.lane_width is None else round(self.lane_width, 2),
            "errors": [error.to_dict() for error in self.errors],
        }


@dataclass(frozen=True)
class LaneDepartureBatch:
    results: Sequence[LaneDepartureResult]

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [result.to_dict() for result in self.results]

