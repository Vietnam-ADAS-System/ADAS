"""
Vehicle Detection Module
Wrapper cho src/detector.py với interface mà main.py expect.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

# Re-export class gốc
try:
    from .src.detector import VehicleDetector  # noqa: F401
except ImportError:
    # Fallback khi load qua importlib (không có parent package)
    import sys
    from pathlib import Path as _P

    _src_dir = _P(__file__).resolve().parent / "src"
    if str(_src_dir) not in sys.path:
        sys.path.insert(0, str(_src_dir))
    try:
        import detector as _detector_module  # type: ignore

        VehicleDetector = _detector_module.VehicleDetector
    except Exception:
        VehicleDetector = None  # type: ignore


class VehicleDetectorConfig:
    """Configuration cho VehicleObjectDetector (compatible với main.py)."""

    def __init__(self, model_path: str, use_preprocessing: bool = False):
        self.model_path = model_path
        self.use_preprocessing = use_preprocessing


class VehicleObjectDetector:
    """High-level wrapper xung quanh VehicleDetector.

    Cung cấp:
      - `detect(frame)` -> List[Dict] (interface gốc)
      - `detect_frame(frame)` -> Dict với key 'detections' (interface main.py expect)
    """

    _LABEL_VI = {
        "car": "Xe hơi",
        "xe_hoi": "Xe hơi",
        "motorcycle": "Xe máy",
        "motorbike": "Xe máy",
        "xe_may": "Xe máy",
        "truck": "Xe tải",
        "bus": "Xe buýt",
        "person": "Người đi bộ",
        "pedestrian": "Người đi bộ",
    }

    def __init__(
        self,
        config: Optional[VehicleDetectorConfig] = None,
        model_path: Optional[Union[str, Path]] = None,
        conf_threshold: float = 0.25,
        use_preprocessing: bool = False,
    ):
        if config is not None:
            self.config = config
            weights_path = config.model_path
            self.use_preprocessing = bool(config.use_preprocessing)
        else:
            weights_path = model_path
            self.use_preprocessing = bool(use_preprocessing)
            self.config = VehicleDetectorConfig(
                model_path=str(weights_path) if weights_path is not None else "",
                use_preprocessing=self.use_preprocessing,
            )

        if VehicleDetector is None:
            raise ImportError(
                "Cannot load VehicleDetector from src.detector. "
                "Please ensure backend/ai-service/ai_models/vehicle_detection/src/detector.py exists."
            )
        self.detector = VehicleDetector(
            weights_path=weights_path,
            conf_threshold=conf_threshold,
        )
        self.last_count = 0
        self.last_result: Optional[Dict[str, Any]] = None

    def _prepare_frame(self, frame: np.ndarray) -> np.ndarray:
        if not self.use_preprocessing or frame is None or frame.size == 0:
            return frame
        try:
            import sys
            from pathlib import Path as _P

            ai_root = _P(__file__).resolve().parents[2]
            if str(ai_root) not in sys.path:
                sys.path.insert(0, str(ai_root))
            from preprocessing.image_processor import ImageProcessor

            processor = ImageProcessor(target_size=(frame.shape[1], frame.shape[0]))
            return processor.apply_module_preprocessing(
                frame,
                module_name="vehicle_detection",
                config={"enable_preprocessing": True, "apply_resize": False},
            )
        except Exception:
            return frame

    def _enrich_detection(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        """Bổ sung các field mà main.py/fusion engine cần."""
        bbox = detection.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) >= 4:
            x1, y1, x2, y2 = bbox[:4]
            detection["x1"] = float(x1)
            detection["y1"] = float(y1)
            detection["x2"] = float(x2)
            detection["y2"] = float(y2)
            detection.setdefault("xyxy", [float(x1), float(y1), float(x2), float(y2)])

        label = detection.get("label", detection.get("class_name", "vehicle"))
        label_norm = str(label).lower().replace("-", "_").replace(" ", "_")
        detection["class_name"] = label
        detection["label_vi"] = self._LABEL_VI.get(label_norm, label)

        if "confidence" in detection and "conf" not in detection:
            detection["conf"] = float(detection["confidence"])
        return detection

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Trả về list detection thuần (compatible với VehicleDetector gốc)."""
        if not isinstance(frame, np.ndarray):
            raise TypeError("frame must be a numpy.ndarray")
        if frame.size == 0:
            return []

        prepared = self._prepare_frame(frame)
        detections = self.detector.detect(prepared)
        enriched = [self._enrich_detection(d) for d in detections]
        self.last_count = len(enriched)
        return enriched

    def detect_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Interface main.py expect: trả dict với key 'detections' và metadata."""
        detections = self.detect(frame)
        result = {
            "detections": detections,
            "count": len(detections),
            "model": str(self.config.model_path),
        }
        self.last_result = result
        return result