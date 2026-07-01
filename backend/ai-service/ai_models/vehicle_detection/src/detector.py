from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

try:
    from ultralytics import YOLO
except ImportError as exc:
    raise ImportError(
        "Cannot import ultralytics. Please install it with: pip install ultralytics"
    ) from exc


class VehicleDetector:
    """YOLO-based vehicle detector for OpenCV frames."""

    def __init__(
        self,
        weights_path: Optional[Union[str, Path]] = None,
        conf_threshold: float = 0.25,
    ) -> None:
        self.conf_threshold = conf_threshold
        self.weights_path = self._resolve_weights_path(weights_path)
        self.model = YOLO(str(self.weights_path))

    @staticmethod
    def _resolve_weights_path(weights_path: Optional[Union[str, Path]]) -> Path:
        """Resolve model path from this file to avoid cwd-dependent errors."""
        if weights_path is None:
            module_dir = Path(__file__).resolve().parent
            weights_path = module_dir.parent / "weights" / "best.pt"

        resolved_path = Path(weights_path).expanduser().resolve()
        if not resolved_path.is_file():
            raise FileNotFoundError(
                f"Vehicle detection weights not found: {resolved_path}"
            )
        return resolved_path

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run vehicle detection on one OpenCV frame.

        Args:
            frame: BGR image as a numpy array from OpenCV.

        Returns:
            List of clean detection dictionaries.
        """
        if not isinstance(frame, np.ndarray):
            raise TypeError("frame must be a numpy.ndarray")
        if frame.size == 0:
            raise ValueError("frame must not be empty")

        results = self.model.predict(
            source=frame,
            conf=self.conf_threshold,
            verbose=False,
        )

        detections: List[Dict[str, Any]] = []
        if not results:
            return detections

        boxes = results[0].boxes
        if boxes is None:
            return detections

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            label = self._get_label(class_id)

            detections.append(
                {
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "confidence": confidence,
                    "class_id": class_id,
                    "label": label,
                }
            )

        return detections

    def _get_label(self, class_id: int) -> str:
        """Read class name safely from Ultralytics model metadata."""
        names = getattr(self.model, "names", {})
        if isinstance(names, dict):
            return str(names.get(class_id, class_id))
        if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
            return str(names[class_id])
        return str(class_id)
