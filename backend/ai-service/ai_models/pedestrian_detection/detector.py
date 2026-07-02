"""
Pedestrian Detection Module using YOLOv11
Nhận diện người đi bộ (person) trong frame
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

AI_SERVICE_ROOT = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_ROOT))

from preprocessing.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class PedestrianDetector:
    """
    Nhận diện người đi bộ sử dụng YOLOv11
    Hỗ trợ CPU/GPU
    """

    def __init__(
        self,
        model_name: str = "yolo11n",
        conf_threshold: float = 0.5,
        enable_preprocessing: bool = True,
        preprocessing_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Khởi tạo detector

        Args:
            model_name: Tên model YOLOv11 (yolo11n, yolo11s, yolo11m, yolo11l, yolo11x)
            conf_threshold: Ngưỡng confidence
            enable_preprocessing: Bật/tắt preprocessing trước inference
            preprocessing_config: Cấu hình preprocessing theo module
        """
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self.enable_preprocessing = enable_preprocessing
        self.preprocessing_config = preprocessing_config or {}
        self.model = None
        # Chỉ quan tâm class "person" trong bộ class chuẩn COCO
        self.class_names = {
            0: "person",
        }
        self._init_model()

    def _init_model(self):
        """Khởi tạo model - dùng thư viện ultralytics"""
        try:
            from ultralytics import YOLO
            logger.info(f"Loading model: {self.model_name}")
            self.model = YOLO(f"{self.model_name}.pt")
            logger.info("Model loaded successfully!")
        except ImportError:
            logger.warning("ultralytics not installed. Using mock detector for demo.")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def detect(self, frame: np.ndarray) -> List[dict]:
        """
        Detect người đi bộ trong frame

        Args:
            frame: Input frame (numpy array)

        Returns:
            List of dict: {x1, y1, x2, y2, confidence, class_id, class_name, width, height}
        """
        if self.model is None:
            return self._mock_detect(frame)

        try:
            input_frame = self._prepare_frame(frame)
            results = self.model(input_frame, conf=self.conf_threshold, verbose=False)

            detections = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = box.conf[0].item()
                    class_id = int(box.cls[0].item())

                    # Chỉ giữ lại class "person" (id = 0 trong COCO)
                    if class_id != 0:
                        continue

                    detections.append({
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "confidence": conf,
                        "class_id": class_id,
                        "class_name": "person",
                        "width": x2 - x1,
                        "height": y2 - y1
                    })

            return detections
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []

    def _prepare_frame(self, frame: np.ndarray) -> np.ndarray:
        if not self.enable_preprocessing or frame is None or frame.size == 0:
            return frame

        processor = ImageProcessor(target_size=(frame.shape[1], frame.shape[0]))
        return processor.apply_module_preprocessing(
            frame,
            module_name="pedestrian",
            config=self.preprocessing_config,
        )

    def _mock_detect(self, frame: np.ndarray) -> List[dict]:
        """
        Mock detection cho testing (khi không có model)
        """
        h, w = frame.shape[:2]
        detections = [
            {
                "x1": w * 0.35,
                "y1": h * 0.3,
                "x2": w * 0.45,
                "y2": h * 0.8,
                "confidence": 0.91,
                "class_id": 0,
                "class_name": "person",
                "width": w * 0.1,
                "height": h * 0.5
            },
            {
                "x1": w * 0.6,
                "y1": h * 0.35,
                "x2": w * 0.68,
                "y2": h * 0.75,
                "confidence": 0.85,
                "class_id": 0,
                "class_name": "person",
                "width": w * 0.08,
                "height": h * 0.4
            },
        ]
        return detections

    def set_confidence_threshold(self, threshold: float):
        """Thay đổi ngưỡng confidence"""
        self.conf_threshold = threshold

    def get_pedestrian_count(self, detections: List[dict]) -> int:
        """Đếm số lượng người đi bộ phát hiện được"""
        return len(detections)