"""Tracking association for Fusion."""

from __future__ import annotations

from typing import Iterable, List, Optional

from .config import FusionConfig
from .data_models import TrackInfo, TrackingAssociation, VehicleDetection
from .utils import bbox_iou


class TrackingFusion:
    """Associate vehicle detections with tracker IDs using IoU."""

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()

    def associate(
        self,
        vehicles: Iterable[VehicleDetection],
        tracks: Iterable[TrackInfo],
    ) -> List[TrackingAssociation]:
        track_list = list(tracks)
        associations: List[TrackingAssociation] = []

        for vehicle in vehicles:
            best_track: Optional[TrackInfo] = None
            best_iou = 0.0
            for track in track_list:
                if track.type in {"person", "pedestrian"}:
                    continue
                iou = bbox_iou(vehicle.bbox, track.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_track = track

            if best_track is not None and best_iou >= self.config.tracking_iou_threshold:
                associations.append(
                    TrackingAssociation(
                        detection_id=vehicle.id,
                        track_id=best_track.track_id,
                        tracking=True,
                    )
                )
            else:
                associations.append(
                    TrackingAssociation(
                        detection_id=vehicle.id,
                        track_id=None,
                        tracking=False,
                    )
                )

        return associations
