import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

import cv2
import numpy as np
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[4]
AI_SERVICE_ROOT = Path(__file__).resolve().parents[2]

TARGET_LABELS = ("person", "car", "motorcycle")
LABEL_VI = {
    "person": "nguoi_di_bo",
    "car": "xe_hoi",
    "motorcycle": "xe_may",
}
LABEL_ALIASES = {
    "person": "person",
    "pedestrian": "person",
    "human": "person",
    "nguoi_di_bo": "person",
    "car": "car",
    "auto": "car",
    "automobile": "car",
    "vehicle_car": "car",
    "xe_hoi": "car",
    "motorcycle": "motorcycle",
    "motorbike": "motorcycle",
    "motor_cycle": "motorcycle",
    "bike_motor": "motorcycle",
    "xe_may": "motorcycle",
}


@dataclass
class VehicleDetectorConfig:
    model_path: str = "yolo26x.pt"
    confidence_threshold: float = 0.35
    iou_threshold: float = 0.50
    image_size: int = 960
    device: Optional[str] = None
    augment: bool = False
    end2end: Optional[bool] = False
    use_preprocessing: bool = False
    target_labels: Tuple[str, ...] = TARGET_LABELS


class VehicleObjectDetector:
    """YOLO object detector limited to car, motorcycle and pedestrian classes."""

    def __init__(self, config: Optional[VehicleDetectorConfig] = None):
        self.config = config or VehicleDetectorConfig()
        self._model = None
        self._class_ids: Optional[List[int]] = None
        self._names: Dict[int, str] = {}

    @classmethod
    def from_env(cls) -> "VehicleObjectDetector":
        _load_project_env()
        device = os.getenv("AI_DEVICE", "auto").strip()
        if device.lower() == "auto":
            device = None

        target_labels = tuple(
            label
            for label in (
                _normalize_label(item)
                for item in os.getenv(
                    "VEHICLE_DETECTION_TARGET_CLASSES",
                    ",".join(TARGET_LABELS),
                ).split(",")
            )
            if label
        )

        return cls(
            VehicleDetectorConfig(
                model_path=os.getenv("YOLO_VEHICLE_MODEL_PATH", "yolo26x.pt"),
                confidence_threshold=_float_env(
                    "VEHICLE_DETECTION_CONFIDENCE_THRESHOLD",
                    _float_env("AI_CONFIDENCE_THRESHOLD", 0.35),
                ),
                iou_threshold=_float_env(
                    "VEHICLE_DETECTION_IOU_THRESHOLD",
                    _float_env("AI_IOU_THRESHOLD", 0.50),
                ),
                image_size=_int_env(
                    "VEHICLE_DETECTION_IMAGE_SIZE",
                    _int_env("AI_IMAGE_SIZE", 960),
                ),
                device=device,
                augment=_bool_env("VEHICLE_DETECTION_AUGMENT", False),
                end2end=_optional_bool_env("VEHICLE_DETECTION_END2END", False),
                use_preprocessing=_bool_env("VEHICLE_DETECTION_PREPROCESS", False),
                target_labels=target_labels or TARGET_LABELS,
            )
        )

    @property
    def model(self):
        if self._model is None:
            _add_torch_dll_paths()
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError(
                    "Missing dependency 'ultralytics'. Install AI service requirements first."
                ) from exc

            self._model = YOLO(_resolve_model_path(self.config.model_path))
            self._names = _names_to_dict(getattr(self._model, "names", {}))
            self._class_ids = self._resolve_target_class_ids(self._names)
            if not self._class_ids:
                raise RuntimeError(
                    "The loaded model has no supported target classes: "
                    + ", ".join(self.config.target_labels)
                )
        return self._model

    def detect_image_bytes(
        self,
        image_bytes: bytes,
        confidence: Optional[float] = None,
        image_size: Optional[int] = None,
        augment: Optional[bool] = None,
        source_name: Optional[str] = None,
        return_image: bool = False,
    ):
        image = _decode_image(image_bytes)
        result = self.detect_frame(
            image,
            confidence=confidence,
            image_size=image_size,
            augment=augment,
            source_name=source_name,
        )
        if return_image:
            return result, image
        return result

    def detect_frame(
        self,
        frame: np.ndarray,
        confidence: Optional[float] = None,
        image_size: Optional[int] = None,
        augment: Optional[bool] = None,
        source_name: Optional[str] = None,
    ) -> Dict:
        if frame is None or frame.size == 0:
            raise ValueError("Input image is empty.")

        inference_frame = self._prepare_frame(frame)
        conf = confidence if confidence is not None else self.config.confidence_threshold
        imgsz = image_size if image_size is not None else self.config.image_size
        use_augment = augment if augment is not None else self.config.augment

        started = time.perf_counter()
        predict_kwargs = {
            "source": inference_frame,
            "classes": self._class_ids,
            "conf": conf,
            "iou": self.config.iou_threshold,
            "imgsz": imgsz,
            "device": self.config.device,
            "augment": use_augment,
            "verbose": False,
        }
        if self.config.end2end is not None:
            predict_kwargs["end2end"] = self.config.end2end

        predictions = self.model.predict(**predict_kwargs)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        detections = self._parse_predictions(predictions[0])
        height, width = frame.shape[:2]
        return {
            "source": source_name,
            "model": self.config.model_path,
            "image_size": {"width": width, "height": height},
            "target_classes": [
                {"name": label, "label_vi": LABEL_VI[label]}
                for label in self.config.target_labels
            ],
            "count": len(detections),
            "detections": detections,
            "inference_ms": elapsed_ms,
            "confidence_threshold": conf,
            "iou_threshold": self.config.iou_threshold,
            "end2end": self.config.end2end,
        }

    def draw_detections(self, image: np.ndarray, detections: Iterable[Dict]) -> np.ndarray:
        output = image.copy()
        colors = {
            "person": (40, 220, 40),
            "car": (255, 120, 40),
            "motorcycle": (40, 180, 255),
        }

        for detection in detections:
            box = detection["bbox"]
            label = detection["class_name"]
            confidence = detection["confidence"]
            color = colors.get(label, (255, 255, 255))
            x1, y1, x2, y2 = (
                int(box["x1"]),
                int(box["y1"]),
                int(box["x2"]),
                int(box["y2"]),
            )
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            caption = "{} {:.2f}".format(LABEL_VI.get(label, label), confidence)
            _draw_caption(output, caption, x1, y1, color)

        return output

    def _prepare_frame(self, frame: np.ndarray) -> np.ndarray:
        if not self.config.use_preprocessing:
            return frame

        from preprocessing.image_processor import ImageProcessor

        processor = ImageProcessor(target_size=(frame.shape[1], frame.shape[0]))
        return processor.preprocess_for_vehicle_detection(frame)

    def _resolve_target_class_ids(self, names: Dict[int, str]) -> List[int]:
        target_labels = set(self.config.target_labels)
        return [
            class_id
            for class_id, name in names.items()
            if _normalize_label(name) in target_labels
        ]

    def _parse_predictions(self, prediction) -> List[Dict]:
        detections = []
        names = _names_to_dict(getattr(prediction, "names", self._names))

        for box in prediction.boxes:
            class_id = int(box.cls.item())
            raw_name = names.get(class_id, str(class_id))
            class_name = _normalize_label(raw_name)
            if class_name not in self.config.target_labels:
                continue

            x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
            confidence = float(box.conf.item())
            detections.append(
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "label_vi": LABEL_VI[class_name],
                    "confidence": round(confidence, 4),
                    "bbox": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2),
                        "width": round(x2 - x1, 2),
                        "height": round(y2 - y1, 2),
                    },
                }
            )

        detections.sort(key=lambda item: item["confidence"], reverse=True)
        return detections


def _load_project_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def _add_torch_dll_paths() -> None:
    try:
        import site
    except ImportError:
        return

    for site_package in site.getsitepackages():
        torch_root = Path(site_package) / "torch"
        for dll_dir in (torch_root / "lib", torch_root / "bin"):
            if dll_dir.exists():
                os.add_dll_directory(str(dll_dir))


def _resolve_model_path(model_path: str) -> str:
    path = Path(model_path)
    if path.is_absolute():
        return str(path)

    for root in (PROJECT_ROOT, AI_SERVICE_ROOT):
        candidate = root / path
        if candidate.exists():
            return str(candidate)

    return model_path


def _decode_image(image_bytes: bytes) -> np.ndarray:
    if not image_bytes:
        raise ValueError("Uploaded image is empty.")
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image. Use JPG, PNG or another OpenCV image format.")
    return image


def _normalize_label(label: Union[str, None]) -> Optional[str]:
    if label is None:
        return None
    key = str(label).strip().lower().replace("-", "_").replace(" ", "_")
    return LABEL_ALIASES.get(key)


def _names_to_dict(names) -> Dict[int, str]:
    if isinstance(names, dict):
        return {int(index): str(name) for index, name in names.items()}
    return {index: str(name) for index, name in enumerate(names)}


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _optional_bool_env(name: str, default: Optional[bool]) -> Optional[bool]:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    if value.strip().lower() in {"none", "null", "auto"}:
        return None
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _draw_caption(
    image: np.ndarray,
    caption: str,
    x: int,
    y: int,
    color: Tuple[int, int, int],
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55
    thickness = 1
    text_size, baseline = cv2.getTextSize(caption, font, scale, thickness)
    y_text = max(y, text_size[1] + baseline + 4)
    cv2.rectangle(
        image,
        (x, y_text - text_size[1] - baseline - 4),
        (x + text_size[0] + 6, y_text + baseline),
        color,
        -1,
    )
    cv2.putText(
        image,
        caption,
        (x + 3, y_text - 3),
        font,
        scale,
        (20, 20, 20),
        thickness,
        cv2.LINE_AA,
    )
