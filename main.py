"""ADAS Streamlit demo app for image, video, and webcam workflows."""

from __future__ import annotations

import importlib.util
import io
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

from adas import ADASDecisionEngine
from fusion import FusionEngine


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


@dataclass
class FrameAnalysis:
    image: np.ndarray
    counts: Dict[str, int]
    elapsed_seconds: float
    scene_context: Dict[str, Any]
    adas_output: Dict[str, Any]


class TrafficSignVision:
    def __init__(self, weights_path: Path, enable_preprocessing: bool = True):
        from ultralytics import YOLO

        self.model = YOLO(str(weights_path))
        self.enable_preprocessing = enable_preprocessing
        self.last_count = 0
        self.mapping_fix = {
            "Cam re phai": "Cam quay dau",
            "Gioi han toc do 40kmh": "Gioi han toc do 50kmh",
            "Gioi han toc do 60kmh": "Gioi han toc do 50kmh",
        }

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
        )
        self.last_count = 0
        if len(results) > 0 and getattr(results[0], "boxes", None) is not None:
            self.last_count = len(results[0].boxes)
        return module.process_frame(frame.copy(), results, self.model.names, self.mapping_fix)

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
        )
        detections = self._parse_detections(results)
        self.last_count = len(detections)
        canvas = draw_on.copy() if draw_on is not None else frame.copy()
        annotated = module.process_frame(canvas, results, self.model.names, self.mapping_fix)
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
                final_text = self.mapping_fix.get(model_text, model_text)
                detections.append(
                    {
                        "id": index,
                        "class": final_text,
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


@st.cache_resource

def load_models(enable_preprocessing: bool) -> Dict[str, Any]:
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
        "adas": ADASDecisionEngine(),
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
    adas_output = models["adas"].evaluate(scene_context)
    scene_context_dict = scene_context.to_dict()
    adas_output_dict = adas_output.to_dict()
    output = _annotate_frame_with_warnings(output, adas_output_dict)

    elapsed = (cv2.getTickCount() - started) / cv2.getTickFrequency()
    return FrameAnalysis(
        image=output,
        counts=counts,
        elapsed_seconds=elapsed,
        scene_context=scene_context_dict,
        adas_output=adas_output_dict,
    )



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



def process_video(video_path: str, models: Dict[str, Any], modules: Sequence[str], enable_preview: bool = False) -> Tuple[str, float]:
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
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

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
                st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), caption=f"Frame {processed_frames}", channels="RGB")
    finally:
        capture.release()
        writer.release()
        progress_bar.progress(1.0)
        status.write(f"Done: {processed_frames} frames")

    avg_fps = processed_frames / total_elapsed if total_elapsed > 0 else 0.0
    return str(output_path), avg_fps



def render_sidebar() -> StreamlitConfig:
    st.sidebar.title("ADAS Demo")
    mode = st.sidebar.radio("Chế độ", ["Ảnh", "Video", "Webcam"], index=0)
    enable_preprocessing = st.sidebar.toggle("Bật preprocessing", value=True)
    st.sidebar.caption("Chọn module chạy")

    module_selection = []
    for key, label in MODULE_LABELS.items():
        checked = st.sidebar.checkbox(label, value=True, key=f"module_{key}")
        if checked:
            module_selection.append(key)

    if not module_selection:
        module_selection = ["pedestrian", "vehicle", "lane_detection", "lane_segmentation", "traffic_sign"]

    return StreamlitConfig(mode=mode, modules=module_selection, enable_preprocessing=enable_preprocessing)



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
    output_path, avg_fps = process_video(temp_path, models, config.modules)
    st.video(output_path)
    st.write(f"FPS trung bình: {avg_fps:.2f}")

    with open(output_path, "rb") as video_file:
        st.download_button(
            "Tải video kết quả",
            data=video_file.read(),
            file_name=Path(output_path).name,
            mime="video/mp4",
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
    models = load_models(config.enable_preprocessing)

    if config.mode == "Ảnh":
        render_image_mode(config, models)
    elif config.mode == "Video":
        render_video_mode(config, models)
    else:
        render_webcam_mode(config, models)


if __name__ == "__main__":
    main()
