"""Offset calculation service."""

from __future__ import annotations

from .direction import determine_direction
from .lane_offset import calculate_lane_offset
from .lane_width import calculate_lane_width
from .models import OffsetData, ValidatedFrameData
from .normalize_offset import normalize_offset


class LaneOffsetService:
    def calculate_offset(self, data: ValidatedFrameData) -> OffsetData:
        lane_width = calculate_lane_width(data.lane_left, data.lane_right)
        offset = calculate_lane_offset(data.vehicle_center[0], data.lane_center)
        normalized = normalize_offset(offset, lane_width)
        if normalized is None:
            normalized = 0.0

        return OffsetData(
            frame_id=data.frame_id,
            vehicle_id=data.vehicle_id,
            tracking_id=data.tracking_id,
            vehicle_center=data.vehicle_center,
            lane_left=data.lane_left,
            lane_right=data.lane_right,
            lane_center=data.lane_center,
            lane_width=lane_width,
            offset=offset,
            normalized_offset=normalized,
            direction=determine_direction(offset),
            source_lane_status=data.source_lane_status,
        )

