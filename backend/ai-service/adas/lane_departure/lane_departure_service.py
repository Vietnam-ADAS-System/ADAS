"""Main Lane Departure Warning service."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from .config import LaneDepartureConfig
from .lane_status import LaneStatusClassifier
from .lane_warning import warning_from_result
from .models import FrameData, LaneDepartureBatch, LaneDepartureResult, OffsetData, ValidationError
from .offset_service import LaneOffsetService
from .utils import as_dict, optional_float, optional_int, parse_center
from .validator import LaneDepartureValidator
from .warning_engine import LaneWarningEngine


class LaneDepartureService:
    def __init__(self, config: Optional[LaneDepartureConfig] = None):
        self.config = config or LaneDepartureConfig()
        self.validator = LaneDepartureValidator(self.config)
        self.offset_service = LaneOffsetService()
        self.status_classifier = LaneStatusClassifier(self.config)
        self.warning_engine = LaneWarningEngine()

    @classmethod
    def from_adas_config(cls, config: Any) -> "LaneDepartureService":
        return cls(LaneDepartureConfig.from_adas_config(config))

    def process_scene(
        self,
        scene_context: Any,
        frame_size: Optional[Tuple[int, int]] = None,
    ) -> LaneDepartureBatch:
        context = as_dict(scene_context)
        frame_id = int(context.get("frame", 0))
        vehicles = context.get("vehicles", [])
        results = [
            self.process_frame_data(self._frame_data_from_vehicle(frame_id, vehicle, frame_size))
            for vehicle in vehicles
        ]
        return LaneDepartureBatch(results=tuple(results))

    def process_frame_data(self, frame_data: FrameData) -> LaneDepartureResult:
        validation = self.validator.validate(frame_data)
        if not validation.valid or validation.data is None:
            return self._invalid_result(frame_data, validation.errors)

        offset_data = self.offset_service.calculate_offset(validation.data)
        status = self.status_classifier.classify(offset_data)
        warning = self.warning_engine.should_warn(status)
        return self._result_from_offset(offset_data, status, warning)

    def warning_objects(self, batch: LaneDepartureBatch) -> List[Any]:
        warnings = []
        for result in batch.results:
            warning = warning_from_result(result)
            if warning is not None:
                warnings.append(warning)
        return warnings

    def _frame_data_from_vehicle(
        self,
        frame_id: int,
        vehicle: Dict[str, Any],
        frame_size: Optional[Tuple[int, int]],
    ) -> FrameData:
        image_width = frame_size[0] if frame_size else None
        image_height = frame_size[1] if frame_size else None
        tracking_id = optional_int(vehicle.get("track_id"))

        return FrameData(
            frame_id=frame_id,
            vehicle_id=tracking_id,
            tracking_id=tracking_id,
            vehicle_center=parse_center(vehicle.get("center")),
            lane_left=optional_float(vehicle.get("lane_left")),
            lane_right=optional_float(vehicle.get("lane_right")),
            lane_center=optional_float(vehicle.get("lane_center")),
            image_width=image_width,
            image_height=image_height,
            source_lane_status=vehicle.get("lane_status"),
        )

    def _invalid_result(
        self,
        frame_data: FrameData,
        errors: Iterable[ValidationError],
    ) -> LaneDepartureResult:
        return LaneDepartureResult(
            vehicle_id=frame_data.vehicle_id,
            tracking_id=frame_data.tracking_id,
            frame_id=frame_data.frame_id,
            offset=None,
            normalized_offset=None,
            direction="UNKNOWN",
            status="LANE_UNKNOWN",
            warning=False,
            vehicle_center=frame_data.vehicle_center,
            lane_left=frame_data.lane_left,
            lane_right=frame_data.lane_right,
            lane_center=frame_data.lane_center,
            lane_width=None,
            errors=tuple(errors),
        )

    @staticmethod
    def _result_from_offset(
        offset_data: OffsetData,
        status: str,
        warning: bool,
    ) -> LaneDepartureResult:
        return LaneDepartureResult(
            vehicle_id=offset_data.vehicle_id,
            tracking_id=offset_data.tracking_id,
            frame_id=offset_data.frame_id,
            offset=offset_data.offset,
            normalized_offset=offset_data.normalized_offset,
            direction=offset_data.direction,
            status=status,
            warning=warning,
            vehicle_center=offset_data.vehicle_center,
            lane_left=offset_data.lane_left,
            lane_right=offset_data.lane_right,
            lane_center=offset_data.lane_center,
            lane_width=offset_data.lane_width,
        )

