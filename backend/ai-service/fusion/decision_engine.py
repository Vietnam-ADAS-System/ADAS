"""Fusion orchestration and final SceneContext normalization."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Dict, List, Optional

from .config import FusionConfig
from .data_models import (
    BoundingBox,
    LaneInfo,
    PedestrianDetection,
    SceneContext,
    TrackInfo,
    TrafficSign,
    VehicleDetection,
)
from .scene_understanding import SceneUnderstandingEngine
from .traffic_sign_fusion import TrafficSignFusion
from .tracking_fusion import TrackingFusion
from .utils import bbox_from_any, format_timestamp, normalize_vehicle_type
from .vehicle_lane_fusion import VehicleLaneFusion


class FusionDecisionEngine:
    """Final Fusion step: ensure SceneContext is ADAS-ready."""

    def normalize(self, context: SceneContext) -> SceneContext:
        return SceneContext(
            frame=int(context.frame),
            vehicles=tuple(context.vehicles),
            traffic_rule=context.traffic_rule,
            timestamp=context.timestamp,
            pedestrians=tuple(context.pedestrians),
        )


class FusionEngine:
    """High-level facade that runs the Fusion flow in the required order."""

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
        self.vehicle_lane_fusion = VehicleLaneFusion(self.config)
        self.tracking_fusion = TrackingFusion(self.config)
        self.traffic_sign_fusion = TrafficSignFusion()
        self.scene_understanding = SceneUnderstandingEngine()
        self.decision_engine = FusionDecisionEngine()

    def build_scene_context(
        self,
        frame_index: int,
        vehicle_detections: Any = None,
        lane_detection: Any = None,
        traffic_sign_detections: Any = None,
        tracking: Any = None,
        pedestrian_detections: Any = None,
        fps: Optional[float] = None,
    ) -> SceneContext:
        vehicles = normalize_vehicle_detections(
            vehicle_detections,
            self.config.detection_confidence_threshold,
        )
        pedestrians = normalize_pedestrian_detections(pedestrian_detections)
        lane_info = normalize_lane_info(lane_detection)
        traffic_signs = normalize_traffic_signs(traffic_sign_detections)
        tracks = normalize_tracks(tracking)

        lane_states = self.vehicle_lane_fusion.process(vehicles, lane_info)
        tracking_associations = self.tracking_fusion.associate(vehicles, tracks)
        traffic_rule = self.traffic_sign_fusion.interpret(traffic_signs)
        context = self.scene_understanding.build_context(
            frame_index=frame_index,
            vehicle_lane_states=lane_states,
            tracking_associations=tracking_associations,
            traffic_rule=traffic_rule,
            timestamp=format_timestamp(frame_index, fps),
            pedestrians=pedestrians,
        )
        return self.decision_engine.normalize(context)


def normalize_vehicle_detections(value: Any, min_confidence: float = 0.0) -> List[VehicleDetection]:
    records = _extract_records(value, key="detections")
    vehicles: List[VehicleDetection] = []

    for index, record in enumerate(records, start=1):
        box = bbox_from_any(record)
        if box is None:
            continue
        confidence = float(record.get("confidence", record.get("conf", 0.0))) if isinstance(record, dict) else 0.0
        if confidence < min_confidence:
            continue
        vehicle_type = "vehicle"
        detection_id = index
        if isinstance(record, dict):
            vehicle_type = normalize_vehicle_type(record.get("class", record.get("class_name", record.get("type"))))
            detection_id = int(record.get("id", index))
        if vehicle_type == "person":
            continue
        vehicles.append(
            VehicleDetection(
                id=detection_id,
                type=vehicle_type,
                bbox=box,
                confidence=confidence,
            )
        )

    return vehicles


def normalize_pedestrian_detections(value: Any) -> List[PedestrianDetection]:
    records = _extract_records(value)
    pedestrians: List[PedestrianDetection] = []
    for index, record in enumerate(records, start=1):
        box = bbox_from_any(record)
        if box is None:
            continue
        confidence = float(record.get("confidence", record.get("conf", 0.0))) if isinstance(record, dict) else 0.0
        pedestrians.append(PedestrianDetection(id=index, bbox=box, confidence=confidence))
    return pedestrians


def normalize_lane_info(value: Any) -> LaneInfo:
    if isinstance(value, LaneInfo):
        return value
    if value is None:
        return LaneInfo()
    if isinstance(value, dict):
        lane_left = value.get("lane_left")
        lane_right = value.get("lane_right")
        lane_center = value.get("lane_center")
        mask = value.get("mask", value.get("lane_mask"))

        detections = value.get("detections") or value.get("lane_detections")
        if detections and (lane_left is None or lane_right is None):
            left, right = _lane_edges_from_detection_boxes(detections)
            lane_left = lane_left if lane_left is not None else left
            lane_right = lane_right if lane_right is not None else right

        return LaneInfo(
            lane_left=lane_left,
            lane_right=lane_right,
            lane_center=lane_center,
            mask=mask,
        )
    return LaneInfo(mask=value)


def normalize_traffic_signs(value: Any) -> List[TrafficSign]:
    records = _extract_records(value)
    signs: List[TrafficSign] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        box = bbox_from_any(record)
        sign_type = record.get("type", record.get("class", record.get("class_name", "UNKNOWN")))
        confidence = float(record.get("confidence", record.get("conf", 0.0)))
        raw_value = record.get("value")
        value_int = int(raw_value) if isinstance(raw_value, (int, float)) else None
        signs.append(TrafficSign(type=str(sign_type), value=value_int, bbox=box, confidence=confidence))
    return signs


def normalize_tracks(value: Any) -> List[TrackInfo]:
    records = _extract_records(value)
    tracks: List[TrackInfo] = []
    for record in records:
        box = bbox_from_any(record)
        if box is None:
            continue
        if hasattr(record, "track_id"):
            track_id = int(record.track_id)
            track_type = normalize_vehicle_type(getattr(record, "class_name", "vehicle"))
        elif isinstance(record, dict):
            track_id = int(record.get("track_id"))
            track_type = normalize_vehicle_type(record.get("class", record.get("class_name", "vehicle")))
        else:
            continue
        tracks.append(TrackInfo(track_id=track_id, bbox=box, type=track_type))
    return tracks


def _extract_records(value: Any, key: Optional[str] = None) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, dict):
        if key and isinstance(value.get(key), list):
            return list(value[key])
        for candidate in ("detections", "items", "tracks", "traffic_signs", "pedestrians"):
            if isinstance(value.get(candidate), list):
                return list(value[candidate])
        return [value]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _lane_edges_from_detection_boxes(detections: Iterable[Dict[str, Any]]) -> tuple[Optional[float], Optional[float]]:
    centers: List[float] = []
    for detection in detections:
        box = bbox_from_any(detection)
        if box is not None:
            centers.append(box.center[0])
    if len(centers) < 2:
        return None, None
    centers.sort()
    return centers[0], centers[-1]
