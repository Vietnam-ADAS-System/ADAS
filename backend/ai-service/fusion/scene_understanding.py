"""Scene Context generation for Fusion."""

from __future__ import annotations

from typing import Iterable, List, Optional

from .data_models import (
    PedestrianDetection,
    PedestrianScene,
    SceneContext,
    TrafficRule,
    TrackingAssociation,
    VehicleLaneState,
    VehicleScene,
)


class SceneUnderstandingEngine:
    """Build a normalized SceneContext from Fusion outputs."""

    def build_context(
        self,
        frame_index: int,
        vehicle_lane_states: Iterable[VehicleLaneState],
        tracking_associations: Iterable[TrackingAssociation],
        traffic_rule: TrafficRule,
        timestamp: Optional[str] = None,
        pedestrians: Optional[Iterable[PedestrianDetection]] = None,
    ) -> SceneContext:
        association_by_detection = {
            item.detection_id: item for item in tracking_associations
        }
        vehicles: List[VehicleScene] = []

        for state in vehicle_lane_states:
            association = association_by_detection.get(state.detection_id)
            vehicles.append(
                VehicleScene(
                    track_id=association.track_id if association else None,
                    type=state.type,
                    lane=state.lane,
                    lane_status=state.lane_status,
                    offset=state.offset,
                    center=state.center,
                    lane_left=state.lane_left,
                    lane_right=state.lane_right,
                    lane_center=state.lane_center,
                    speed=None,
                    tracking=bool(association and association.tracking),
                )
            )

        pedestrian_scenes = [
            PedestrianScene(track_id=None, center=item.bbox.center, tracking=False)
            for item in (pedestrians or [])
        ]

        return SceneContext(
            frame=frame_index,
            vehicles=vehicles,
            traffic_rule=traffic_rule,
            timestamp=timestamp,
            pedestrians=pedestrian_scenes,
        )
