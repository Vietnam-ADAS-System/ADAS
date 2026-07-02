"""ADAS Streamlit demo app for image, video, and webcam workflows."""

from __future__ import annotations

import importlib.util
import io
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent
AI_SERVICE_ROOT = REPO_ROOT / "backend" / "ai-service"


MODULE_PATHS = {
    "pedestrian": AI_SERVICE_ROOT / "ai_models" / "pedestrian_detection" / "detector.py",
    "vehicle": AI_SERVICE_ROOT / "ai_models" / "vehicle_detection" / "vehicle_detector.py",
    "lane_detection": AI_SERVICE_ROOT / "ai_models" / "lane_detection" / "detector.py",
    "lane_segmentation": AI_SERVICE_ROOT / "ai_models" / "lane_segmentation" / "predict.py",
    "traffic_sign": AI_SERVICE_ROOT / "ai_models" / "traffic_sign_detection" / "predict.py",
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


def draw_results(frame: np.ndarray, models: Dict[str, Any], modules: Sequence[str]) -> Tuple[np.ndarray, Dict[str, int], float]:
    output = frame.copy()
    counts = {name: 0 for name in MODULE_LABELS}

    started = cv2.getTickCount()
    selected_modules = list(modules)
    if "all" in selected_modules:
        selected_modules = ["pedestrian", "vehicle", "lane_detection", "lane_segmentation", "traffic_sign"]

    for module_name in selected_modules:
        if module_name == "pedestrian":
            detections = models["pedestrian"].detect(output)
            counts["pedestrian"] = len(detections)
            for detection in detections:
                _draw_box(output, detection, MODULE_COLORS["pedestrian"])
        elif module_name == "vehicle":
            result = models["vehicle"].detect_frame(output)
            detections = result.get("detections", []) if isinstance(result, dict) else []
            counts["vehicle"] = len(detections)
            output = models["vehicle"].draw_detections(output, detections)
        elif module_name == "lane_detection":
            counts["lane_detection"] = len(models["lane_detection"].get_detections(output))
            output = models["lane_detection"].visualize(output)
        elif module_name == "lane_segmentation":
            mask = models["lane_segmentation"].get_lane_mask(output)
            counts["lane_segmentation"] = int(np.count_nonzero(mask))
            output = models["lane_segmentation"].visualize(output)
        elif module_name == "traffic_sign":
            output = models["traffic_sign"].detect(output)
            counts["traffic_sign"] = getattr(models["traffic_sign"], "last_count", 0)

    elapsed = (cv2.getTickCount() - started) / cv2.getTickFrequency()
    return output, counts, elapsed



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



def process_image(image: np.ndarray, models: Dict[str, Any], modules: Sequence[str]) -> Tuple[np.ndarray, Dict[str, int], float]:
    return draw_results(image, models, modules)



def process_video(video_path: str, models: Dict[str, Any], modules: Sequence[str], enable_preview: bool = False) -> Tuple[str, float]:
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")

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
            annotated, counts, elapsed = process_image(frame, models, modules)
            annotated = _annotate_frame_with_counts(annotated, counts, elapsed, modules)
            writer.write(annotated)
            total_elapsed += elapsed

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
    output, counts, elapsed = process_image(image, models, config.modules)
    output = _annotate_frame_with_counts(output, counts, elapsed, config.modules)

    st.image(cv2.cvtColor(output, cv2.COLOR_BGR2RGB), caption="Kết quả", use_container_width=True)
    st.write(f"Thời gian xử lý: {elapsed:.2f}s")
    st.write({k: v for k, v in counts.items() if v > 0})

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
    output, counts, elapsed = process_image(image, models, config.modules)
    output = _annotate_frame_with_counts(output, counts, elapsed, config.modules)

    st.image(cv2.cvtColor(output, cv2.COLOR_BGR2RGB), caption="Kết quả webcam", use_container_width=True)
    st.write(f"Thời gian xử lý: {elapsed:.2f}s")
    st.write({k: v for k, v in counts.items() if v > 0})

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
