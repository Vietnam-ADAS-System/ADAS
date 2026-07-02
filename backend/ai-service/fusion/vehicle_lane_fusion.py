"""Vehicle-lane fusion logic."""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from .config import FusionConfig
from .data_models import LaneInfo, VehicleDetection, VehicleLaneState
from .utils import center_from_bbox, lane_bounds_from_mask, points_to_x


class VehicleLaneFusion:
    """Assign each detected vehicle to lane state and lane offset."""

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()

    def process(
        self,
        vehicles: Iterable[VehicleDetection],
        lane_info: LaneInfo,
    ) -> List[VehicleLaneState]:
        lane_left, lane_right, lane_center = self._resolve_lane_geometry(lane_info)
        states: List[VehicleLaneState] = []

        for vehicle in vehicles:
            center = center_from_bbox(vehicle.bbox)
            offset = None if lane_center is None else center[0] - lane_center
            lane = self._classify_lane(offset, lane_center)
            lane_status = self._classify_lane_status(vehicle, center[0], lane_left, lane_right)

            states.append(
                VehicleLaneState(
                    detection_id=vehicle.id,
                    type=vehicle.type,
                    center=center,
                    lane=lane,
                    lane_status=lane_status,
                    offset=offset,
                )
            )

        return states

    def _resolve_lane_geometry(self, lane_info: LaneInfo) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        mask_left, mask_right, mask_center = lane_bounds_from_mask(lane_info.mask)
        lane_left = points_to_x(lane_info.lane_left)
        lane_right = points_to_x(lane_info.lane_right)
        lane_center = points_to_x(lane_info.lane_center)

        lane_left = lane_left if lane_left is not None else mask_left
        lane_right = lane_right if lane_right is not None else mask_right

        if lane_center is None:
            if lane_left is not None and lane_right is not None:
                lane_center = (lane_left + lane_right) / 2.0
            else:
                lane_center = mask_center

        return lane_left, lane_right, lane_center

    def _classify_lane(self, offset: Optional[float], lane_center: Optional[float]) -> str:
        if offset is None or lane_center is None:
            return "unknown"
        if abs(offset) <= self.config.lane_center_deadzone_px:
            return "center"
        return "right" if offset > 0 else "left"

    def _classify_lane_status(
        self,
        vehicle: VehicleDetection,
        center_x: float,
        lane_left: Optional[float],
        lane_right: Optional[float],
    ) -> str:
        if lane_left is None or lane_right is None:
            return "unknown"

        left, right = sorted((lane_left, lane_right))
        crosses_left = vehicle.bbox.x1 < left < vehicle.bbox.x2
        crosses_right = vehicle.bbox.x1 < right < vehicle.bbox.x2
        if crosses_left or crosses_right:
            return "crossing_lane"

        if center_x < left or center_x > right:
            return "outside_lane"

        distance_to_boundary = min(abs(center_x - left), abs(right - center_x))
        if distance_to_boundary <= self.config.lane_boundary_margin_px:
            return "near_boundary"

        return "inside_lane"

