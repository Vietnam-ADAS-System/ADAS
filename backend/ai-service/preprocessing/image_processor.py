import cv2
import numpy as np
from typing import Any, Dict, Optional, Tuple

from preprocessing.color_space.converter import rgb_to_gray, rgb_to_hsv
from preprocessing.enhancement.equalizer import histogram_equalization, clahe
from preprocessing.filtering.filters import gaussian_filter, median_filter


class ImageProcessor:
    """
    Entry point duy nhất cho preprocessing pipeline.
    Tất cả method nhận BGR numpy array (từ OpenCV).
    """

    def __init__(self, target_size: Tuple[int, int] = (640, 480)):
        self.target_size = target_size

    def resize(self, frame: np.ndarray,
               size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        return cv2.resize(frame, size or self.target_size)

    def enhance_contrast(self, frame: np.ndarray) -> np.ndarray:
        """CLAHE trên LAB — BGR in, BGR out"""
        return clahe(frame, clip_limit=2.0)

    def process_frame(self, frame: np.ndarray,
                      enhance: bool = True) -> np.ndarray:
        """
        Pipeline chung: resize → (CLAHE nếu enhance=True)
        Được gọi từ API — không thay đổi signature này.
        """
        frame = self.resize(frame)
        if enhance:
            frame = self.enhance_contrast(frame)
        return frame

    def apply_module_preprocessing(
        self,
        frame: np.ndarray,
        module_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        """
        Apply module-specific preprocessing and return an image array.

        The shared detector wrappers expect ndarray input, so lane-specific
        preprocessing is reduced to an image output even though the lower-level
        lane helper can also return multiple derived representations.
        """
        if frame is None or frame.size == 0:
            return frame

        config = config or {}
        if not config.get("enable_preprocessing", True):
            return frame

        module_key = (module_name or "").strip().lower()
        if module_key in {"vehicle", "pedestrian"}:
            return self.preprocess_for_vehicle_detection(frame)
        if module_key in {"lane_detection", "lane_segmentation", "lane"}:
            lane_output = self.preprocess_for_lane_detection(frame)
            output_key = config.get("output_key", "bgr")
            if isinstance(lane_output, dict):
                return lane_output.get(output_key, lane_output.get("bgr", frame))
            return lane_output
        if module_key in {"traffic_sign", "traffic_sign_detection", "sign"}:
            return self.preprocess_for_traffic_sign(frame)
        if module_key in {"tracking"}:
            return self.preprocess_for_tracking(frame)

        return self.process_frame(frame, enhance=config.get("enhance", True))

    def preprocess_for_vehicle_detection(self, frame: np.ndarray) -> np.ndarray:
        """
        BGR → gaussian_filter → CLAHE → BGR
        Dùng cho: YOLOv11 vehicle detection
        """
        frame = self.resize(frame)
        frame = gaussian_filter(frame, kernel_size=5, sigma=1.0)
        frame = clahe(frame, clip_limit=2.0)
        return frame

    def preprocess_for_pedestrian_detection(self, frame: np.ndarray) -> np.ndarray:
        """
        Dùng chung pipeline với vehicle (cùng YOLOv11, class 'person')
        """
        return self.preprocess_for_vehicle_detection(frame)

    def preprocess_for_lane_detection(self, frame: np.ndarray) -> dict:
        """
        BGR → nhiều dạng phục vụ cả CVIP lẫn DeepLab sau này
        Output dict:
          - bgr      : frame gốc đã resize
          - gray     : HxW — cho Canny / Hough Transform
          - hsv      : HxWx3 — cho color-based lane masking
          - clahe    : HxW — gray đã tăng contrast
          - gaussian : HxW — gray đã làm mượt, sẵn sàng cho Canny
        """
        frame = self.resize(frame)
        gray = rgb_to_gray(frame, color_format="BGR")
        hsv = rgb_to_hsv(frame, color_format="BGR")
        clahe_img = clahe(gray, clip_limit=2.0)
        gaussian_img = gaussian_filter(gray, kernel_size=5, sigma=1.0)
        return {
            "bgr": frame,
            "gray": gray,
            "hsv": hsv,
            "clahe": clahe_img,
            "gaussian": gaussian_img,
        }

    def preprocess_for_traffic_sign(
        self,
        frame: np.ndarray,
        target_size: Optional[Tuple[int, int]] = None,
        apply_resize: bool = True,
    ) -> np.ndarray:
        """
        BGR → CLAHE mạnh hơn (clip_limit=3.0) → BGR
        Dùng cho: YOLOv11 traffic sign — cần contrast cao để phân biệt màu biển báo
        """
        if apply_resize:
            frame = self.resize(frame, size=target_size)
        return clahe(frame, clip_limit=3.0)

    def preprocess_for_tracking(self, frame: np.ndarray) -> np.ndarray:
        """
        BGR → histogram_equalization → BGR
        Dùng cho: DeepSORT — ổn định brightness giữa các frame liên tiếp
        """
        frame = self.resize(frame)
        return histogram_equalization(frame)
