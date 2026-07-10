"""ADAS Streamlit demo app for image, video, and webcam workflows."""

from __future__ import annotations

import importlib.util
import inspect
import io
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent
AI_SERVICE_ROOT = REPO_ROOT / "backend" / "ai-service"
if str(AI_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_ROOT))

APP_CACHE_VERSION = "adas-fusion-lane-departure-v4"

def _has_signature_parameter(callable_obj: Any, parameter_name: str) -> bool:
    try:
        return parameter_name in inspect.signature(callable_obj).parameters
    except (AttributeError, TypeError, ValueError):
        return False


def _drop_adas_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "adas" or module_name.startswith("adas."):
            sys.modules.pop(module_name, None)


def _drop_stale_adas_modules() -> None:
    importlib.invalidate_caches()

    lane_departure_module = sys.modules.get("adas.lane_departure")
    if lane_departure_module is not None and not hasattr(lane_departure_module, "__path__"):
        _drop_adas_modules()
        return

    data_models_module = sys.modules.get("adas.data_models")
    output_class = getattr(data_models_module, "ADASOutput", None)
    if output_class is not None and not _has_signature_parameter(output_class, "lane_departure"):
        _drop_adas_modules()
        return

    decision_engine_module = sys.modules.get("adas.decision_engine")
    engine_class = getattr(decision_engine_module, "ADASDecisionEngine", None)
    evaluate_method = getattr(engine_class, "evaluate", None)
    if evaluate_method is not None and not _has_signature_parameter(evaluate_method, "frame_size"):
        _drop_adas_modules()


def _resize_for_preview(
    frame: np.ndarray,
    scale: float,
    max_width: int = 960,
    max_height: int = 620,
) -> np.ndarray:
    height, width = frame.shape[:2]
    if height <= 0 or width <= 0:
        return frame

    scale = max(0.1, min(scale, 1.0))
    scale_by_width = max_width / float(width)
    scale_by_height = max_height / float(height)
    fit_scale = min(scale, scale_by_width, scale_by_height, 1.0)

    if fit_scale >= 0.999:
        return frame

    new_width = max(1, int(width * fit_scale))
    new_height = max(1, int(height * fit_scale))
    return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)


def _create_browser_video_writer(
    output_path: Path,
    fps: float,
    frame_size: Tuple[int, int],
) -> Tuple[cv2.VideoWriter, str, Path]:
    codec_candidates = (
        ("avc1", ".mp4"),
        ("H264", ".mp4"),
        ("VP80", ".webm"),
        ("VP90", ".webm"),
        ("mp4v", ".mp4"),
    )
    for codec, suffix in codec_candidates:
        candidate_path = output_path.with_suffix(suffix)
        writer = cv2.VideoWriter(
            str(candidate_path),
            cv2.VideoWriter_fourcc(*codec),
            fps,
            frame_size,
        )
        if writer.isOpened():
            return writer, codec, candidate_path
        writer.release()
    raise RuntimeError("Could not create output video writer.")


def _find_ffmpeg_executable() -> Optional[str]:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    try:
        import imageio_ffmpeg  # type: ignore
    except ImportError:
        return None

    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _ensure_browser_playable_video(video_path: Path, codec: str) -> Path:
    if codec in {"avc1", "H264", "VP80", "VP90"}:
        return video_path

    ffmpeg_path = _find_ffmpeg_executable()
    if ffmpeg_path is None:
        return video_path

    temp_output = video_path.with_name(f"{video_path.stem}_playable_tmp{video_path.suffix}")
    for encoder in ("libx264", "h264"):
        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(video_path),
            "-an",
            "-c:v",
            encoder,
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(temp_output),
        ]
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if result.returncode == 0 and temp_output.exists() and temp_output.stat().st_size > 0:
            temp_output.replace(video_path)
            return video_path
        temp_output.unlink(missing_ok=True)

    return video_path


_drop_stale_adas_modules()

from adas.lane_departure import draw_lane_departure_overlay
from fusion import FusionEngine
try:
    from adas.traffic_sign import (
        SignInputService,
        WarningDecisionService,
        WarningManager,
    )
except ImportError:
    pass  # Traffic Sign Warning Module not available


MODULE_PATHS = {
    "pedestrian": AI_SERVICE_ROOT / "ai_models" / "pedestrian_detection" / "detector.py",
    "vehicle": AI_SERVICE_ROOT / "ai_models" / "vehicle_detection" / "vehicle_detector.py",
    "lane_detection": AI_SERVICE_ROOT / "ai_models" / "lane_detection" / "detector.py",
    "lane_segmentation": AI_SERVICE_ROOT / "ai_models" / "lane_segmentation" / "predict.py",
    "traffic_sign": AI_SERVICE_ROOT / "ai_models" / "traffic_sign_detection" / "predict.py",
    "tracking": AI_SERVICE_ROOT / "tracking" / "deepsort_tracker.py",
}

MODEL_PATHS = {
    "pedestrian": AI_SERVICE_ROOT / "ai_models" / "pedestrian_detection" / "pedestrian_runs" / "pedestrian" / "walking_v1" / "weights" / "best.pt",
    "vehicle": AI_SERVICE_ROOT / "ai_models" / "vehicle_detection" / "weights" / "best.pt",
    "lane_detection": AI_SERVICE_ROOT / "ai_models" / "lane_detection" / "weights" / "best.pt",
    "lane_segmentation": AI_SERVICE_ROOT / "ai_models" / "lane_segmentation" / "weights" / "best.pt",
    "traffic_sign": AI_SERVICE_ROOT / "ai_models" / "traffic_sign_detection" / "traffic_sign_runs_new" / "traffic_sign_52classes" / "weights" / "best.pt",
}

OUTPUT_DIR_IMAGES = REPO_ROOT / "outputs" / "predictions"
OUTPUT_DIR_VIDEOS = REPO_ROOT / "outputs" / "videos"

MODULE_LABELS = {
    "pedestrian": "Pedestrian",
    "vehicle": "Vehicle",
    "lane_detection": "Lane Detection",
    "lane_segmentation": "Lane Segmentation",
    "traffic_sign": "Traffic Sign",
}

MODULE_COLORS = {
    "pedestrian": (0, 255, 0),
    "vehicle": (255, 0, 0),
    "lane_detection": (255, 255, 0),
    "lane_segmentation": (255, 255, 255),
    "traffic_sign": (0, 165, 255),
}


@dataclass
class StreamlitConfig:
    mode: str
    modules: Sequence[str]
    enable_preprocessing: bool
    preview_scale: float = 0.65


@dataclass
class FrameAnalysis:
    image: np.ndarray
    counts: Dict[str, int]
    elapsed_seconds: float
    scene_context: Dict[str, Any]
    adas_output: Dict[str, Any]
    traffic_sign_warnings: List[Dict[str, Any]] = None


class TrafficSignVision:
    def __init__(self, weights_path: Path, enable_preprocessing: bool = True, device: Optional[int] = None):
        from ultralytics import YOLO
        from gpu_utils import get_inference_device, log_inference_device

        self.model = YOLO(str(weights_path))
        self.enable_preprocessing = enable_preprocessing
        self.last_count = 0
        # Xác định device (GPU hoặc CPU)
        self.device = device if device is not None else get_inference_device()
        log_inference_device(self.device)
        # Di chuyển model sang device
        if self.device is not None:
            self.model.to(self.device)

    def detect(self, frame: np.ndarray) -> np.ndarray:
        module = _load_module("traffic_sign_module", MODULE_PATHS["traffic_sign"])
        frame_for_inference = module.apply_preprocessing(
            frame,
            enable_preprocessing=self.enable_preprocessing,
            preprocessing_config={
                "enable_preprocessing": True,
                "apply_resize": False,  # ✓ YOLO tự xử lý letterbox
            },
        )
        results = self.model.predict(
            source=frame_for_inference,
            conf=0.15,
            agnostic_nms=True,
            verbose=False,
            device=self.device,  # ← GPU/CPU inference
        )
        self.last_count = 0
        if len(results) > 0 and getattr(results[0], "boxes", None) is not None:
            self.last_count = len(results[0].boxes)
        return module.process_frame(frame.copy(), results, self.model.names, {})

    def detect_with_detections(
        self,
        frame: np.ndarray,
        draw_on: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        module = _load_module("traffic_sign_module", MODULE_PATHS["traffic_sign"])
        frame_for_inference = module.apply_preprocessing(
            frame,
            enable_preprocessing=self.enable_preprocessing,
            preprocessing_config={
                "enable_preprocessing": True,
                "apply_resize": False,
            },
        )
        results = self.model.predict(
            source=frame_for_inference,
            conf=0.15,
            agnostic_nms=True,
            verbose=False,
            device=self.device,  # ← GPU/CPU inference
        )
        detections = self._parse_detections(results)
        self.last_count = len(detections)
        canvas = draw_on.copy() if draw_on is not None else frame.copy()
        annotated = module.process_frame(canvas, results, self.model.names, {})
        return annotated, detections

    def _parse_detections(self, results: Iterable[Any]) -> List[Dict[str, Any]]:
        detections: List[Dict[str, Any]] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for index, box in enumerate(boxes, start=1):
                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
                class_id = int(box.cls[0])
                model_text = self.model.names[class_id]
                detections.append(
                    {
                        "id": index,
                        "class": model_text,
                        "bbox": [x1, y1, x2, y2],
                        "confidence": float(box.conf[0].item()),
                    }
                )
        return detections


@st.cache_resource

def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _create_adas_engine() -> Any:
    importlib.invalidate_caches()
    decision_module = importlib.import_module("adas.decision_engine")
    return decision_module.ADASDecisionEngine()


@st.cache_resource

def load_models(enable_preprocessing: bool, cache_version: str = APP_CACHE_VERSION) -> Dict[str, Any]:
    _ = cache_version
    pedestrian_module = _load_module("adas_pedestrian_detection", MODULE_PATHS["pedestrian"])
    vehicle_module = _load_module("adas_vehicle_detection", MODULE_PATHS["vehicle"])
    lane_detection_module = _load_module("adas_lane_detection", MODULE_PATHS["lane_detection"])
    lane_segmentation_module = _load_module("adas_lane_segmentation", MODULE_PATHS["lane_segmentation"])
    tracking_module = _load_module("adas_tracking", MODULE_PATHS["tracking"])

    models = {
        "pedestrian": pedestrian_module.PedestrianDetector(
            model_name=str(MODEL_PATHS["pedestrian"]),
            enable_preprocessing=enable_preprocessing
        ),
        "vehicle": vehicle_module.VehicleObjectDetector(
            vehicle_module.VehicleDetectorConfig(
                model_path=str(MODEL_PATHS["vehicle"]),
                use_preprocessing=enable_preprocessing
            )
        ),
        "lane_detection": lane_detection_module.LaneDetector(
            str(MODEL_PATHS["lane_detection"]),
            enable_preprocessing=enable_preprocessing,
        ),
        "lane_segmentation": lane_segmentation_module.LaneSegmenter(
            str(MODEL_PATHS["lane_segmentation"]),
            enable_preprocessing=enable_preprocessing,
        ),
        "traffic_sign": TrafficSignVision(
            MODEL_PATHS["traffic_sign"],
            enable_preprocessing=enable_preprocessing,
        ),
        "tracker": tracking_module.ObjectTracker(),
        "fusion": FusionEngine(),
        "adas": _create_adas_engine(),
    }
    return models


@st.cache_data(show_spinner=False)
def file_bytes_to_image(file_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(file_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image")
    return image


@st.cache_data(show_spinner=False)
def file_bytes_to_temp_path(file_bytes: bytes, suffix: str) -> str:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(file_bytes)
    temp_file.flush()
    temp_file.close()
    return temp_file.name


def _draw_box(frame: np.ndarray, detection: Dict[str, Any], color: Tuple[int, int, int]) -> None:
    x1 = int(detection.get("x1", 0))
    y1 = int(detection.get("y1", 0))
    x2 = int(detection.get("x2", 0))
    y2 = int(detection.get("y2", 0))
    label = str(detection.get("class_name", detection.get("label_vi", "object")))
    confidence = float(detection.get("confidence", 0.0))
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        frame,
        f"{label} {confidence:.2f}",
        (x1, max(y1 - 10, 15)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        2,
    )


def _draw_lane_detections(frame: np.ndarray, detections: Sequence[Dict[str, Any]]) -> None:
    for detection in detections:
        bbox = detection.get("bbox", [])
        if len(bbox) < 4:
            continue
        x1, y1, x2, y2 = [int(value) for value in bbox[:4]]
        label = str(detection.get("class_name", "lane"))
        confidence = float(detection.get("conf", detection.get("confidence", 0.0)))
        color = MODULE_COLORS["lane_detection"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            f"{label} {confidence:.2f}",
            (x1, max(y1 - 10, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
        )


def _overlay_lane_mask(frame: np.ndarray, mask: Optional[np.ndarray]) -> np.ndarray:
    if mask is None or mask.size == 0 or int(np.count_nonzero(mask)) == 0:
        return frame
    overlay = frame.copy()
    color_layer = np.zeros_like(frame)
    color_layer[mask > 0] = MODULE_COLORS["lane_segmentation"]
    cv2.addWeighted(color_layer, 0.45, overlay, 0.55, 0, overlay)
    return overlay


def _draw_tracks(frame: np.ndarray, tracks: Iterable[Any]) -> None:
    for track in tracks:
        bbox = getattr(track, "bbox", None)
        if bbox is None or len(bbox) < 4:
            continue
        x1, y1, x2, y2 = [int(value) for value in bbox[:4]]
        track_id = getattr(track, "track_id", "?")
        class_name = getattr(track, "class_name", "object")
        label = f"ID {track_id} {class_name}"
        color = (0, 255, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
        cv2.putText(
            frame,
            label,
            (x1, min(y2 + 18, frame.shape[0] - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
        )


def _reset_tracker(models: Dict[str, Any]) -> None:
    tracker = models.get("tracker")
    if tracker is not None and hasattr(tracker, "reset"):
        tracker.reset()


def _annotate_frame_with_warnings(frame: np.ndarray, adas_output: Dict[str, Any]) -> np.ndarray:
    annotated = frame.copy()
    warnings = adas_output.get("warnings", [])[:3]
    if not warnings:
        return annotated

    y = max(30, annotated.shape[0] - 24 * len(warnings) - 12)
    for warning in warnings:
        priority = warning.get("priority", "INFO")
        label = f"{priority}: {warning.get('type', 'Warning')}"
        cv2.putText(
            annotated,
            label,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 255) if priority in {"HIGH", "CRITICAL"} else (0, 255, 255),
            2,
        )
        y += 24
    return annotated


def _draw_traffic_sign_warnings(frame: np.ndarray, warnings: List[Dict[str, Any]]) -> np.ndarray:
    """Vẽ cảnh báo biển báo dưới ảnh"""
    if not warnings:
        return frame
    
    annotated = frame.copy()
    h, w = annotated.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.65
    thickness = 2
    line_height = 30
    margin = 8
    text_color = (255, 255, 255)
    max_text_width = max(120, int(w * 0.56))
    
    def _fit_label(label: str) -> str:
        while len(label) > 12 and cv2.getTextSize(label, font, font_scale, thickness)[0][0] > max_text_width:
            label = label[:-4].rstrip() + "..."
        return label
    
    # Place warnings in the top-right to avoid ADAS/lane text below.
    y = 24
    max_items = min(5, max(1, (h - margin * 2) // line_height))
    
    for warning in warnings[:max_items]:  # Tối đa 5 warnings
        level = warning.get("level", "MEDIUM")
        msg = warning.get("message", warning.get("type", "Warning"))
        
        label = _fit_label(f"[{level}] {msg}")
        text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
        x = max(margin, w - text_size[0] - margin)
        
        # Text
        cv2.putText(
            annotated,
            label,
            (x, y),
            font,
            font_scale,
            text_color,
            thickness,
        )
        y += line_height
    
    return annotated


def _evaluate_adas(models: Dict[str, Any], scene_context: Any, frame_size: Tuple[int, int]) -> Any:
    adas_engine = models["adas"]
    try:
        return adas_engine.evaluate(scene_context, frame_size=frame_size)
    except TypeError as exc:
        if "frame_size" not in str(exc):
            raise

    adas_engine = _create_adas_engine()
    models["adas"] = adas_engine
    try:
        return adas_engine.evaluate(scene_context, frame_size=frame_size)
    except TypeError as exc:
        if "frame_size" not in str(exc):
            raise
        return adas_engine.evaluate(scene_context)


def _generate_traffic_sign_warnings(traffic_sign_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sinh cảnh báo từ traffic sign detections, sắp xếp từ gần tới xa"""
    warnings = []
    
    try:
        # Map detection sang rule cho TV4
        for detection in traffic_sign_detections:
            class_name = detection.get("class", "")
            
            # Tính khoảng cách dựa trên diện tích bbox (bbox lớn = gần hơn)
            x1 = detection.get("x", 0)
            y1 = detection.get("y", 0)
            x2 = detection.get("x2", x1 + 10)
            y2 = detection.get("y2", y1 + 10)
            bbox_area = (x2 - x1) * (y2 - y1)
            
            # Tạo warning rule dựa trên class name
            if "Cam" in class_name or "No entry" in class_name or "Prohibited" in class_name:
                warnings.append({
                    "type": "NO_ENTRY",
                    "message": class_name,
                    "level": "HIGH",
                    "priority": 90,
                    "distance": bbox_area,
                })
            elif "Dung" in class_name or "Stop" in class_name:
                warnings.append({
                    "type": "STOP",
                    "message": class_name,
                    "level": "HIGH",
                    "priority": 95,
                    "distance": bbox_area,
                })
            elif "Gioi han toc do" in class_name or "Speed limit" in class_name:
                # Extract speed value
                speed_match = re.search(r'\d+', class_name)
                speed = speed_match.group() if speed_match else "???"
                warnings.append({
                    "type": "SPEED_LIMIT",
                    "message": f"Speed limit {speed} km/h",
                    "level": "MEDIUM",
                    "priority": 60,
                    "distance": bbox_area,
                })
            elif "Khu vuc hoc" in class_name or "School" in class_name:
                warnings.append({
                    "type": "SCHOOL_ZONE",
                    "message": class_name,
                    "level": "MEDIUM",
                    "priority": 65,
                    "distance": bbox_area,
                })
            elif "Nguoi di bo" in class_name or "Pedestrian" in class_name:
                warnings.append({
                    "type": "PEDESTRIAN_CROSSING",
                    "message": class_name,
                    "level": "HIGH",
                    "priority": 85,
                    "distance": bbox_area,
                })
            else:
                # Generic warning
                warnings.append({
                    "type": "TRAFFIC_SIGN",
                    "message": class_name,
                    "level": "MEDIUM",
                    "priority": 50,
                    "distance": bbox_area,
                })
    except Exception as e:
        print(f"Error generating traffic sign warnings: {e}")
    
    # Sort by distance - gần nhất trước (bbox lớn nhất), xa nhất sau (bbox nhỏ nhất)
    warnings.sort(key=lambda w: w.get("distance", 0), reverse=True)
    return warnings[:5]  # Top 5 warnings


def draw_results(
    frame: np.ndarray,
    models: Dict[str, Any],
    modules: Sequence[str],
    frame_index: int = 0,
    fps: Optional[float] = None,
) -> FrameAnalysis:
    output = frame.copy()
    counts = {name: 0 for name in MODULE_LABELS}
    vehicle_result: Optional[Dict[str, Any]] = None
    pedestrian_detections: List[Dict[str, Any]] = []
    lane_detections: List[Dict[str, Any]] = []
    lane_mask: Optional[np.ndarray] = None
    traffic_sign_detections: List[Dict[str, Any]] = []
    traffic_sign_warnings: List[Dict[str, Any]] = []

    started = cv2.getTickCount()
    selected_modules = list(modules)
    if "all" in selected_modules:
        selected_modules = ["pedestrian", "vehicle", "lane_detection", "lane_segmentation", "traffic_sign"]

    for module_name in selected_modules:
        if module_name == "pedestrian":
            pedestrian_detections = models["pedestrian"].detect(frame)
            counts["pedestrian"] = len(pedestrian_detections)
            for detection in pedestrian_detections:
                _draw_box(output, detection, MODULE_COLORS["pedestrian"])
        elif module_name == "vehicle":
            vehicle_result = models["vehicle"].detect_frame(frame)
            detections = vehicle_result.get("detections", []) if isinstance(vehicle_result, dict) else []
            counts["vehicle"] = len(detections)
            output = models["vehicle"].draw_detections(output, detections)
        elif module_name == "lane_detection":
            lane_detections = models["lane_detection"].get_detections(frame)
            counts["lane_detection"] = len(lane_detections)
            _draw_lane_detections(output, lane_detections)
        elif module_name == "lane_segmentation":
            lane_mask = models["lane_segmentation"].get_lane_mask(frame)
            counts["lane_segmentation"] = int(np.count_nonzero(lane_mask))
            output = _overlay_lane_mask(output, lane_mask)
        elif module_name == "traffic_sign":
            output, traffic_sign_detections = models["traffic_sign"].detect_with_detections(frame, draw_on=output)
            counts["traffic_sign"] = getattr(models["traffic_sign"], "last_count", 0)
            # Generate warnings từ traffic sign detections
            traffic_sign_warnings = _generate_traffic_sign_warnings(traffic_sign_detections)
            # Vẽ warnings lên ảnh
            output = _draw_traffic_sign_warnings(output, traffic_sign_warnings)

    tracks = []
    if vehicle_result is not None or pedestrian_detections:
        tracks = models["tracker"].update(
            vehicle_detections=vehicle_result,
            pedestrian_detections=pedestrian_detections,
            frame=frame,
        )
        _draw_tracks(output, tracks)

    lane_payload = {
        "detections": lane_detections,
        "mask": lane_mask,
    }
    scene_context = models["fusion"].build_scene_context(
        frame_index=frame_index,
        vehicle_detections=vehicle_result,
        lane_detection=lane_payload,
        traffic_sign_detections=traffic_sign_detections,
        tracking=tracks,
        pedestrian_detections=pedestrian_detections,
        fps=fps,
    )
    adas_output = _evaluate_adas(models, scene_context, frame_size=(frame.shape[1], frame.shape[0]))
    scene_context_dict = scene_context.to_dict()
    adas_output_dict = adas_output.to_dict()
    output = draw_lane_departure_overlay(output, adas_output_dict.get("lane_departure", []))
    output = _annotate_frame_with_warnings(output, adas_output_dict)

    elapsed = (cv2.getTickCount() - started) / cv2.getTickFrequency()
    frame_analysis = FrameAnalysis(
        image=output,
        counts=counts,
        elapsed_seconds=elapsed,
        scene_context=scene_context_dict,
        adas_output=adas_output_dict,
    )
    frame_analysis.traffic_sign_warnings = traffic_sign_warnings
    return frame_analysis



def _annotate_frame_with_counts(frame: np.ndarray, counts: Dict[str, int], elapsed_seconds: float, modules: Sequence[str]) -> np.ndarray:
    annotated = frame.copy()
    fps = (1.0 / elapsed_seconds) if elapsed_seconds > 0 else 0.0
    text_lines = [f"FPS: {fps:.2f}"]
    for module_name in modules:
        if module_name == "all":
            continue
        text_lines.append(f"{MODULE_LABELS.get(module_name, module_name)}: {counts.get(module_name, 0)}")

    y = 28
    for line in text_lines:
        cv2.putText(annotated, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        y += 24
    return annotated



def process_image(
    image: np.ndarray,
    models: Dict[str, Any],
    modules: Sequence[str],
    frame_index: int = 0,
    fps: Optional[float] = None,
) -> FrameAnalysis:
    return draw_results(image, models, modules, frame_index=frame_index, fps=fps)



def process_video(
    video_path: str,
    models: Dict[str, Any],
    modules: Sequence[str],
    enable_preview: bool = False,
    preview_placeholder: Optional[Any] = None,
    preview_scale: float = 0.65,
) -> Tuple[str, float]:
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")
    _reset_tracker(models)

    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    output_dir = OUTPUT_DIR_VIDEOS
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{Path(video_path).stem}_streamlit_annotated.mp4"
    writer, writer_codec, output_path = _create_browser_video_writer(output_path, fps, (width, height))

    processed_frames = 0
    total_elapsed = 0.0
    progress_bar = st.progress(0)
    status = st.empty()

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            processed_frames += 1
            analysis = process_image(frame, models, modules, frame_index=processed_frames, fps=fps)
            annotated = _annotate_frame_with_counts(
                analysis.image,
                analysis.counts,
                analysis.elapsed_seconds,
                modules,
            )
            writer.write(annotated)
            total_elapsed += analysis.elapsed_seconds

            progress_value = min(processed_frames / max(total_frames, 1), 1.0)
            progress_bar.progress(progress_value)
            status.write(f"Processing frame {processed_frames}/{total_frames or '?'}")

            if enable_preview:
                preview_image = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                preview_image = _resize_for_preview(preview_image, preview_scale)
                if preview_placeholder is not None:
                    preview_placeholder.image(
                        preview_image,
                        caption=f"Realtime frame {processed_frames}",
                        use_container_width=False,
                    )
                else:
                    st.image(
                        preview_image,
                        caption=f"Realtime frame {processed_frames}",
                        use_container_width=False,
                    )
    finally:
        capture.release()
        writer.release()
        progress_bar.progress(1.0)
        status.write(f"Done: {processed_frames} frames")

    avg_fps = processed_frames / total_elapsed if total_elapsed > 0 else 0.0
    output_path = _ensure_browser_playable_video(output_path, writer_codec)
    return str(output_path), avg_fps



def render_sidebar() -> StreamlitConfig:
    st.sidebar.title("ADAS Demo")
    mode = st.sidebar.radio("Chế độ", ["Ảnh", "Video", "Webcam"], index=0)
    enable_preprocessing = st.sidebar.toggle("Bật preprocessing", value=True)
    preview_scale = st.sidebar.slider(
        "Kích thước khung preview video",
        min_value=0.4,
        max_value=1.0,
        value=0.65,
        step=0.05,
        help="Giảm kích thước hiển thị để nhìn trọn video và giảm tải giao diện, không đổi frame đầu vào cho model.",
    )
    st.sidebar.caption("Chọn module chạy")

    module_selection = []
    for key, label in MODULE_LABELS.items():
        checked = st.sidebar.checkbox(label, value=True, key=f"module_{key}")
        if checked:
            module_selection.append(key)

    if not module_selection:
        module_selection = ["pedestrian", "vehicle", "lane_detection", "lane_segmentation", "traffic_sign"]

    return StreamlitConfig(
        mode=mode,
        modules=module_selection,
        enable_preprocessing=enable_preprocessing,
        preview_scale=preview_scale,
    )



def render_image_mode(config: StreamlitConfig, models: Dict[str, Any]) -> None:
    uploaded = st.file_uploader("Tải ảnh", type=["jpg", "jpeg", "png", "bmp", "webp"])
    if uploaded is None:
        st.info("Chưa có file ảnh.")
        return

    image = file_bytes_to_image(uploaded.read())
    _reset_tracker(models)
    analysis = process_image(image, models, config.modules)
    output = _annotate_frame_with_counts(
        analysis.image,
        analysis.counts,
        analysis.elapsed_seconds,
        config.modules,
    )
    counts = analysis.counts
    elapsed = analysis.elapsed_seconds

    st.image(cv2.cvtColor(output, cv2.COLOR_BGR2RGB), caption="Kết quả", use_container_width=True)
    st.write(f"Thời gian xử lý: {elapsed:.2f}s")
    st.write({k: v for k, v in counts.items() if v > 0})
    
    # Hiển thị Traffic Sign Warnings
    if hasattr(analysis, 'traffic_sign_warnings') and analysis.traffic_sign_warnings:
        st.subheader("⚠️ Cảnh báo biển báo")
        for i, warning in enumerate(analysis.traffic_sign_warnings, 1):
            level = warning.get("level", "MEDIUM")
            msg = warning.get("message", "")
            
            # Chọn màu hiển thị
            if level in ["CRITICAL", "HIGH"]:
                st.error(f"🔴 **#{i}** [{level}] {msg}")
            elif level == "MEDIUM":
                st.warning(f"🟡 **#{i}** [{level}] {msg}")
            else:
                st.info(f"🔵 **#{i}** [{level}] {msg}")
    
    with st.expander("Scene Context / ADAS Output", expanded=False):
        st.json(analysis.scene_context)
        st.json(analysis.adas_output)

    _, buffer = cv2.imencode(".png", output)
    st.download_button(
        "Tải ảnh kết quả",
        data=buffer.tobytes(),
        file_name=f"{Path(uploaded.name).stem}_annotated.png",
        mime="image/png",
    )



def render_video_mode(config: StreamlitConfig, models: Dict[str, Any]) -> None:
    uploaded = st.file_uploader("Tải video", type=["mp4", "avi", "mov", "mkv"])
    if uploaded is None:
        st.info("Chưa có file video.")
        return

    temp_path = file_bytes_to_temp_path(uploaded.read(), suffix=Path(uploaded.name).suffix)
    left_col, center_col, right_col = st.columns([1, 2.2, 1])
    with center_col:
        preview_slot = st.empty()
    output_path, avg_fps = process_video(
        temp_path,
        models,
        config.modules,
        enable_preview=True,
        preview_placeholder=preview_slot,
        preview_scale=config.preview_scale,
    )
    with open(output_path, "rb") as video_file:
        video_bytes = video_file.read()
    video_format = "video/webm" if Path(output_path).suffix.lower() == ".webm" else "video/mp4"
    with center_col:
        st.video(video_bytes, format=video_format)
    st.write(f"FPS trung bình: {avg_fps:.2f}")

    st.download_button(
        "Tải video kết quả",
        data=video_bytes,
        file_name=Path(output_path).name,
        mime=video_format,
    )



def render_webcam_mode(config: StreamlitConfig, models: Dict[str, Any]) -> None:
    st.info("Chế độ webcam dùng camera_input để chụp một ảnh từ webcam trình duyệt.")
    captured = st.camera_input("Chụp ảnh từ webcam")
    if captured is None:
        return

    image = file_bytes_to_image(captured.read())
    _reset_tracker(models)
    analysis = process_image(image, models, config.modules)
    output = _annotate_frame_with_counts(
        analysis.image,
        analysis.counts,
        analysis.elapsed_seconds,
        config.modules,
    )
    counts = analysis.counts
    elapsed = analysis.elapsed_seconds

    st.image(cv2.cvtColor(output, cv2.COLOR_BGR2RGB), caption="Kết quả webcam", use_container_width=True)
    st.write(f"Thời gian xử lý: {elapsed:.2f}s")
    st.write({k: v for k, v in counts.items() if v > 0})
    
    # Hiển thị Traffic Sign Warnings
    if hasattr(analysis, 'traffic_sign_warnings') and analysis.traffic_sign_warnings:
        st.subheader("⚠️ Cảnh báo biển báo")
        for i, warning in enumerate(analysis.traffic_sign_warnings, 1):
            level = warning.get("level", "MEDIUM")
            msg = warning.get("message", "")
            
            # Chọn màu hiển thị
            if level in ["CRITICAL", "HIGH"]:
                st.error(f"🔴 **#{i}** [{level}] {msg}")
            elif level == "MEDIUM":
                st.warning(f"🟡 **#{i}** [{level}] {msg}")
            else:
                st.info(f"🔵 **#{i}** [{level}] {msg}")
    
    with st.expander("Scene Context / ADAS Output", expanded=False):
        st.json(analysis.scene_context)
        st.json(analysis.adas_output)

    _, buffer = cv2.imencode(".png", output)
    st.download_button(
        "Tải ảnh webcam kết quả",
        data=buffer.tobytes(),
        file_name="webcam_annotated.png",
        mime="image/png",
    )



def main() -> None:
    st.set_page_config(page_title="ADAS Demo", layout="wide")
    st.title("ADAS Demo")
    st.caption("Streamlit demo cho ảnh, video và webcam với preprocessing tích hợp")

    config = render_sidebar()
    models = load_models(config.enable_preprocessing, APP_CACHE_VERSION)

    if config.mode == "Ảnh":
        render_image_mode(config, models)
    elif config.mode == "Video":
        render_video_mode(config, models)
    else:
        render_webcam_mode(config, models)


if __name__ == "__main__":
    main()
