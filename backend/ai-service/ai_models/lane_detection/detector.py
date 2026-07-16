"""
YOLOv11n-seg Lane Detection Wrapper
Multi-class Lane Segmentation cho hệ thống hỗ trợ lái xe (ADAS)

Phát hiện 11 loại vạch/lane đặc thù đường Việt Nam:
    - white_solid, white_dashed, yellow_solid, yellow_dashed
    - double_yellow, stop_line, crosswalk
    - arrow_straight, arrow_turn, road_surface, background

Tương thích với interface trong main.py:
    - get_detections(frame, debug=False) -> List[Dict]
    - get_class_masks(frame) -> Dict[str, np.ndarray]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError as exc:
    raise ImportError(
        "Cannot import ultralytics. Please install it with: pip install ultralytics"
    ) from exc


# 11 class names cho lane detection (Vietnamese roads)
CLASS_NAMES = {
    0: "background",
    1: "road_surface",
    2: "white_solid",
    3: "white_dashed",
    4: "yellow_solid",
    5: "yellow_dashed",
    6: "double_yellow",
    7: "stop_line",
    8: "crosswalk",
    9: "arrow_straight",
    10: "arrow_turn",
}

# Mapping class_name -> ADAS rule tiếng Việt
CLASS_RULE_VI = {
    "background": "Nền",
    "road_surface": "Mặt đường",
    "white_solid": "⛔ KHÔNG ĐÈ (vạch trắng liền)",
    "white_dashed": "✅ ĐÈ ĐƯỢC (vạch trắng đứt)",
    "yellow_solid": "⛔ KHÔNG ĐÈ (vạch vàng liền)",
    "yellow_dashed": "✅ ĐÈ ĐƯỢC (vạch vàng đứt)",
    "double_yellow": "⛔ NGUY HIỂM (vạch vàng đôi)",
    "stop_line": "🚦 Vạch dừng - Dừng xe",
    "crosswalk": "🚶 Vạch qua đường",
    "arrow_straight": "➡️ Mũi tên thẳng",
    "arrow_turn": "↔️ Mũi tên rẽ",
}

# BGR colors cho visualization (OpenCV dùng BGR)
CLASS_COLOR_BGR = {
    0: (50, 50, 50),      # dark gray - background
    1: (80, 80, 80),      # gray - road surface
    2: (255, 255, 255),   # white solid
    3: (200, 200, 200),   # light gray - white dashed
    4: (0, 255, 255),     # yellow solid
    5: (0, 200, 200),     # yellow dashed
    6: (0, 150, 255),     # orange-yellow - double yellow
    7: (255, 0, 255),     # magenta - stop line
    8: (255, 100, 100),   # pink - crosswalk
    9: (0, 255, 0),       # green - arrow straight
    10: (0, 128, 255),    # orange - arrow turn
}


class LaneDetector:
    """YOLO segmentation-based lane detector cho ADAS."""

    def __init__(
        self,
        weights_path: Optional[Union[str, Path]] = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        enable_preprocessing: bool = True,
        imgsz: int = 640,
    ) -> None:
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.enable_preprocessing = enable_preprocessing
        self.imgsz = imgsz
        self.weights_path = self._resolve_weights_path(weights_path)
        self.model = YOLO(str(self.weights_path))
        # Sync class names từ model metadata nếu có
        if hasattr(self.model, "names") and isinstance(self.model.names, dict):
            model_names = self.model.names
            # Nếu model có đủ 11 classes và khớp với config, dùng của model
            if len(model_names) >= len(CLASS_NAMES):
                for idx, name in CLASS_NAMES.items():
                    if idx in model_names and model_names[idx] != name:
                        # Model đã có mapping riêng, giữ nguyên
                        break
        self.class_names = CLASS_NAMES
        self.class_rules = CLASS_RULE_VI
        self.class_colors = CLASS_COLOR_BGR
        self.last_count = 0

    @staticmethod
    def _resolve_weights_path(weights_path: Optional[Union[str, Path]]) -> Path:
        if weights_path is None:
            module_dir = Path(__file__).resolve().parent
            weights_path = module_dir / "weights" / "best.pt"
        resolved_path = Path(weights_path).expanduser().resolve()
        if not resolved_path.is_file():
            raise FileNotFoundError(
                f"Lane detection weights not found: {resolved_path}"
            )
        return resolved_path

    def _prepare_image(self, frame: np.ndarray) -> np.ndarray:
        if not self.enable_preprocessing or frame is None or frame.size == 0:
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
                module_name="lane_detection",
                config={"enable_preprocessing": True, "apply_resize": False},
            )
        except Exception:
            return frame

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Run lane detection on a single OpenCV frame.

        Returns:
            List of detection dicts with keys:
                - bbox: [x1, y1, x2, y2]
                - confidence: float
                - class_id: int
                - class_name: str
                - rule_vi: str  (ADAS rule tiếng Việt)
        """
        if not isinstance(frame, np.ndarray):
            raise TypeError("frame must be a numpy.ndarray")
        if frame.size == 0:
            raise ValueError("frame must not be empty")

        frame_prepared = self._prepare_image(frame)
        results = self.model.predict(
            source=frame_prepared,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=self.imgsz,
            verbose=False,
        )

        detections: List[Dict[str, Any]] = []
        if not results:
            self.last_count = 0
            return detections

        result = results[0]
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            self.last_count = 0
            return detections

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            class_name = self.class_names.get(class_id, f"class_{class_id}")

            detections.append(
                {
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "confidence": confidence,
                    "class_id": class_id,
                    "class_name": class_name,
                    "label": class_name,
                    "label_vi": self.class_rules.get(class_name, class_name),
                    "conf": confidence,
                }
            )

        self.last_count = len(detections)
        return detections

    def get_detections(self, frame: np.ndarray, debug: bool = False) -> List[Dict[str, Any]]:
        """Compatibility method cho main.py: trả về list of detections."""
        return self.detect(frame)

    def detect_with_masks(self, frame: np.ndarray, debug: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, np.ndarray]]:
        """Trả về (detections, class_masks) cho visualization.

        Mỗi detection có key 'mask' (uint8 binary mask) để main.py vẽ outline polygon
        thay vì bbox (vì YOLO-seg bbox to bao trùm cả vùng mask).
        """
        detections = self.detect(frame)
        if not detections:
            return detections, {}

        h, w = frame.shape[:2]
        frame_prepared = self._prepare_image(frame)
        results = self.model.predict(
            source=frame_prepared,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=self.imgsz,
            verbose=False,
        )
        if not results:
            return detections, {}

        result = results[0]
        masks = getattr(result, "masks", None)
        boxes = getattr(result, "boxes", None)
        if masks is None or boxes is None or len(boxes) == 0:
            return detections, {}

        mask_array = masks.data.cpu().numpy()
        classes = boxes.cls.cpu().numpy().astype(int)
        xyxy = boxes.xyxy.cpu().numpy() if hasattr(boxes, "xyxy") else None

        for idx, (mask, cls_id) in enumerate(zip(mask_array, classes)):
            if idx >= len(detections):
                break
            # Resize mask về kích thước frame
            resized = cv2.resize(mask, (w, h))
            binary = (resized * 255).astype(np.uint8)
            detections[idx]["mask"] = binary
            detections[idx]["class_id"] = int(cls_id)

        return detections, {det.get("class_name"): det["mask"] for det in detections if "mask" in det}

    def get_class_masks(self, frame: np.ndarray) -> Dict[str, np.ndarray]:
        """Trả về dict mask nhị phân cho từng class.

        Returns:
            Dict[class_name -> uint8 mask (0/255)] với shape (H, W).
        """
        if not isinstance(frame, np.ndarray):
            raise TypeError("frame must be a numpy.ndarray")
        if frame.size == 0:
            raise ValueError("frame must not be empty")

        h, w = frame.shape[:2]
        frame_prepared = self._prepare_image(frame)
        results = self.model.predict(
            source=frame_prepared,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=self.imgsz,
            verbose=False,
        )

        output_masks: Dict[str, np.ndarray] = {
            name: np.zeros((h, w), dtype=np.uint8)
            for name in self.class_names.values()
        }

        if not results:
            return output_masks

        result = results[0]
        masks = getattr(result, "masks", None)
        boxes = getattr(result, "boxes", None)

        if masks is None or boxes is None or len(boxes) == 0:
            return output_masks

        mask_array = masks.data.cpu().numpy()
        classes = boxes.cls.cpu().numpy().astype(int)

        for mask, cls_id in zip(mask_array, classes):
            cls_name = self.class_names.get(int(cls_id))
            if cls_name is None:
                continue
            resized = cv2.resize(mask, (w, h))
            binary = (resized * 255).astype(np.uint8)
            output_masks[cls_name] = np.maximum(output_masks[cls_name], binary)

        return output_masks

    def get_all_class_masks(self, frame: np.ndarray) -> Dict[str, np.ndarray]:
        """Alias cho get_class_masks để tương thích với main.py."""
        return self.get_class_masks(frame)

    def visualize(self, frame: np.ndarray, alpha: float = 0.5) -> np.ndarray:
        """Vẽ detection overlay lên frame (mask + bbox + label)."""
        if frame is None or frame.size == 0:
            return frame

        output = frame.copy()
        masks = self.get_class_masks(frame)
        detections = self.get_detections(frame)

        # Vẽ mask cho từng class (skip background & road_surface)
        for cls_id, cls_name in self.class_names.items():
            if cls_id in (0, 1):
                continue
            mask = masks.get(cls_name)
            if mask is None or int(np.count_nonzero(mask)) == 0:
                continue
            color = self.class_colors.get(cls_id, (0, 255, 0))
            color_layer = np.zeros_like(output)
            color_layer[mask > 0] = color
            cv2.addWeighted(color_layer, alpha, output, 1 - alpha, 0, output)

        # Vẽ bbox + label
        for det in detections:
            bbox = det.get("bbox", [])
            if len(bbox) < 4:
                continue
            x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
            cls_id = det.get("class_id", 0)
            color = self.class_colors.get(cls_id, (0, 255, 0))
            label = f"{det.get('class_name', 'lane')} {det.get('confidence', 0):.2f}"
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(output, (x1, max(y1 - th - 6, 0)), (x1 + tw, y1), color, -1)
            cv2.putText(
                output, label, (x1, max(y1 - 4, th)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1
            )

        return output


def predict_from_image(
    image_path: str,
    weights_path: Optional[str] = None,
    conf: float = 0.25,
    output_path: Optional[str] = None,
) -> np.ndarray:
    """Helper để predict từ image file path."""
    detector = LaneDetector(weights_path=weights_path, conf_threshold=conf)
    frame = cv2.imread(image_path)
    if frame is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    result = detector.visualize(frame)
    if output_path:
        cv2.imwrite(output_path, result)
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YOLOv11n-seg Lane Detection")
    parser.add_argument("--weights", type=str, default=None)
    parser.add_argument("--source", type=str, required=True)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--conf", type=float, default=0.25)
    args = parser.parse_args()

    img = cv2.imread(args.source)
    if img is None:
        raise SystemExit(f"Cannot read: {args.source}")
    detector = LaneDetector(weights_path=args.weights, conf_threshold=args.conf)
    detections = detector.detect(img)
    print(f"Detected {len(detections)} lanes:")
    for d in detections:
        print(f"  - {d['class_name']} (conf={d['confidence']:.2f}): {d['label_vi']}")

    result = detector.visualize(img)
    if args.output:
        cv2.imwrite(args.output, result)
    else:
        cv2.imshow("Lane Detection", result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()