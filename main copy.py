"""ADAS Streamlit demo app for image, video, and webcam workflows."""

from __future__ import annotations

import csv
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

APP_CACHE_VERSION = "adas-fusion-lane-departure-v5"

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
from preprocessing.image_processor import ImageProcessor
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

TRAINING_EVALUATION_RUNS = {
    "vehicle": {
        "label": "Vehicle Detection",
        "run_dir": AI_SERVICE_ROOT / "ai_models" / "vehicle_detection" / "evaluation",
        "csv_path": AI_SERVICE_ROOT / "ai_models" / "vehicle_detection" / "evaluation" / "results.csv",
        "weights_path": MODEL_PATHS["vehicle"],
        "scope": "Xe hơi, xe máy và người đi bộ trong luồng vehicle.",
    },
    "pedestrian": {
        "label": "Pedestrian Detection",
        "run_dir": AI_SERVICE_ROOT / "ai_models" / "pedestrian_detection" / "pedestrian_runs" / "pedestrian" / "walking_v1",
        "csv_path": AI_SERVICE_ROOT / "ai_models" / "pedestrian_detection" / "pedestrian_runs" / "pedestrian" / "walking_v1" / "results.csv",
        "weights_path": MODEL_PATHS["pedestrian"],
        "scope": "Nhận diện người đi bộ.",
    },
    "traffic_sign": {
        "label": "Traffic Sign Detection",
        "run_dir": AI_SERVICE_ROOT / "ai_models" / "traffic_sign_detection" / "traffic_sign_runs_new" / "traffic_sign_52classes",
        "csv_path": AI_SERVICE_ROOT / "ai_models" / "traffic_sign_detection" / "traffic_sign_runs" / "results.csv",
        "weights_path": MODEL_PATHS["traffic_sign"],
        "scope": "Nhận diện biển báo giao thông Việt Nam.",
        "csv_note": "Run mới đang dùng có đủ ảnh biểu đồ nhưng không có results.csv; metric số bên dưới lấy từ traffic_sign_runs/results.csv nếu file tồn tại.",
    },
}

TRAINING_CHARTS = (
    ("results.png", "Tổng quan loss, precision, recall và mAP"),
    ("confusion_matrix_normalized.png", "Ma trận nhầm lẫn chuẩn hóa"),
    ("BoxPR_curve.png", "Precision-Recall"),
    ("BoxF1_curve.png", "F1 theo confidence"),
    ("BoxP_curve.png", "Precision theo confidence"),
    ("BoxR_curve.png", "Recall theo confidence"),
)

TRAINING_SAMPLE_IMAGES = (
    ("labels.jpg", "Phân bố nhãn"),
    ("val_batch0_labels.jpg", "Ground truth validation"),
    ("val_batch0_pred.jpg", "Dự đoán validation"),
)

OUTPUT_DIR_IMAGES = REPO_ROOT / "outputs" / "predictions"
OUTPUT_DIR_VIDEOS = REPO_ROOT / "outputs" / "videos"

MODULE_LABELS = {
    "pedestrian": "Pedestrian",
    "vehicle": "Vehicle",
    "lane_detection": "Lane Detection",
    "lane_segmentation": "Lane Segmentation",
    "traffic_sign": "Traffic Sign",
}

MODULE_UI_LABELS = {
    "pedestrian": "Người đi bộ",
    "vehicle": "Phương tiện",
    "lane_detection": "Vạch làn",
    "lane_segmentation": "Vùng làn",
    "traffic_sign": "Biển báo",
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
    object_details: Dict[str, List[Dict[str, Any]]] = None


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
        annotated = _draw_traffic_sign_detections(canvas, detections)
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


def _prepare_tracking_frame(frame: np.ndarray, enable_preprocessing: bool) -> np.ndarray:
    if not enable_preprocessing or frame is None or frame.size == 0:
        return frame

    height, width = frame.shape[:2]
    processor = ImageProcessor(target_size=(width, height))
    return processor.apply_module_preprocessing(
        frame,
        module_name="tracking",
        config={"enable_preprocessing": True},
    )


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
        "preprocessing_enabled": enable_preprocessing,
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


def inject_app_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --adas-bg: #f6f8fb;
                --adas-panel: #ffffff;
                --adas-text: #172033;
                --adas-muted: #667085;
                --adas-border: #d9e2ec;
                --adas-teal: #0f766e;
                --adas-amber: #d97706;
                --adas-red: #dc2626;
                --adas-blue: #2563eb;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(15, 118, 110, 0.08), transparent 28rem),
                    linear-gradient(180deg, #fbfcff 0%, var(--adas-bg) 42%, #ffffff 100%);
                color: var(--adas-text);
            }

            [data-testid="stHeader"] {
                background: rgba(246, 248, 251, 0.88);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(217, 226, 236, 0.75);
            }

            [data-testid="stSidebar"] {
                background: #ffffff;
                border-right: 1px solid var(--adas-border);
            }

            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {
                color: var(--adas-text);
            }

            .block-container {
                max-width: 1320px;
                padding-top: 1.4rem;
                padding-bottom: 3rem;
            }

            .adas-hero {
                border: 1px solid var(--adas-border);
                border-radius: 8px;
                padding: 1.15rem 1.35rem;
                margin-bottom: 1.2rem;
                background: linear-gradient(135deg, #ffffff 0%, #eefdf8 58%, #fff7ed 100%);
                box-shadow: 0 18px 45px rgba(28, 39, 60, 0.08);
            }

            .adas-hero h1 {
                margin: 0;
                color: var(--adas-text);
                font-size: clamp(1.9rem, 3vw, 3rem);
                line-height: 1.08;
                letter-spacing: 0;
            }

            .adas-hero p {
                margin: 0.45rem 0 0;
                color: var(--adas-muted);
                font-size: 1rem;
                line-height: 1.55;
            }

            .hero-pills {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 0.85rem;
            }

            .hero-pill {
                display: inline-flex;
                align-items: center;
                min-height: 2rem;
                padding: 0.32rem 0.7rem;
                border-radius: 8px;
                border: 1px solid rgba(15, 118, 110, 0.22);
                background: rgba(255, 255, 255, 0.74);
                color: #0f513f;
                font-weight: 650;
                font-size: 0.82rem;
                white-space: nowrap;
            }

            .section-heading {
                margin: 1.35rem 0 0.65rem;
            }

            .section-heading h2 {
                margin: 0;
                font-size: 1.35rem;
                line-height: 1.25;
                letter-spacing: 0;
                color: var(--adas-text);
            }

            .section-heading p {
                margin: 0.28rem 0 0;
                color: var(--adas-muted);
                line-height: 1.5;
            }

            div[data-testid="stMetric"] {
                background: var(--adas-panel);
                border: 1px solid var(--adas-border);
                border-radius: 8px;
                padding: 0.9rem 1rem;
                box-shadow: 0 10px 28px rgba(28, 39, 60, 0.06);
            }

            div[data-testid="stMetric"] label {
                color: var(--adas-muted);
            }

            .result-card {
                border: 1px solid var(--adas-border);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.92);
                padding: 0.95rem 1rem;
                min-height: 8.5rem;
                box-shadow: 0 12px 30px rgba(28, 39, 60, 0.06);
            }

            .result-card h3 {
                margin: 0 0 0.65rem;
                font-size: 1rem;
                line-height: 1.3;
                color: var(--adas-text);
                letter-spacing: 0;
            }

            .result-row {
                display: flex;
                justify-content: space-between;
                gap: 0.8rem;
                padding: 0.32rem 0;
                border-top: 1px solid #eef2f7;
                color: var(--adas-muted);
                font-size: 0.93rem;
            }

            .result-row:first-of-type {
                border-top: 0;
            }

            .result-row strong {
                color: var(--adas-text);
                font-weight: 700;
            }

            .artifact-path {
                color: var(--adas-muted);
                font-size: 0.86rem;
                line-height: 1.45;
                margin: 0.1rem 0 0.65rem;
                word-break: break-word;
            }

            .stImage img,
            [data-testid="stImage"] img {
                border-radius: 8px;
                border: 1px solid var(--adas-border);
                box-shadow: 0 16px 38px rgba(28, 39, 60, 0.08);
            }

            .stDownloadButton button,
            .stButton button,
            [data-testid="stFileUploader"] button {
                border-radius: 8px;
                border: 1px solid rgba(15, 118, 110, 0.22);
                background: #ffffff;
                color: var(--adas-text);
                font-weight: 650;
            }

            .stDownloadButton button:hover,
            .stButton button:hover,
            [data-testid="stFileUploader"] button:hover {
                border-color: var(--adas-teal);
                color: var(--adas-teal);
            }

            div[data-testid="stExpander"] {
                border: 1px solid var(--adas-border);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.92);
                box-shadow: 0 10px 28px rgba(28, 39, 60, 0.05);
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 0.4rem;
                border-bottom: 1px solid var(--adas-border);
            }

            .stTabs [data-baseweb="tab"] {
                border-radius: 8px 8px 0 0;
                color: var(--adas-muted);
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .stTabs [aria-selected="true"] {
                color: var(--adas-teal);
                background: rgba(15, 118, 110, 0.08);
            }

            @media (max-width: 760px) {
                .block-container {
                    padding-left: 1rem;
                    padding-right: 1rem;
                }

                .adas-hero {
                    padding: 1rem;
                }

                .hero-pill {
                    width: 100%;
                    justify-content: center;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header() -> None:
    st.markdown(
        """
        <div class="adas-hero">
            <h1>ADAS Vietnam Vision Suite</h1>
            <p>Dashboard kiểm thử nhận diện, fusion và cảnh báo trên dữ liệu đường phố Việt Nam.</p>
            <div class="hero-pills">
                <span class="hero-pill">Image / Video / Webcam</span>
                <span class="hero-pill">YOLO Detection</span>
                <span class="hero-pill">Lane & Traffic Sign</span>
                <span class="hero-pill">Training Evaluation</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


@st.cache_data(show_spinner=False)
def _read_training_results(csv_path: str) -> List[Dict[str, str]]:
    path = Path(csv_path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _float_value(row: Dict[str, str], key: str) -> Optional[float]:
    try:
        value = row.get(key, "")
        if value in {"", None}:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _best_value(rows: Sequence[Dict[str, str]], key: str) -> Tuple[Optional[float], Optional[int]]:
    values: List[Tuple[float, Optional[int]]] = []
    for row in rows:
        value = _float_value(row, key)
        epoch = _float_value(row, "epoch")
        if value is not None:
            values.append((value, None if epoch is None else int(epoch)))

    if not values:
        return None, None
    return max(values, key=lambda item: item[0])


def _total_loss(row: Dict[str, str]) -> Optional[float]:
    parts = [
        _float_value(row, "train/box_loss"),
        _float_value(row, "train/cls_loss"),
        _float_value(row, "train/dfl_loss"),
    ]
    if any(value is None for value in parts):
        return None
    return float(sum(value or 0.0 for value in parts))


def _format_percent(value: Optional[float]) -> str:
    if value is None:
        return "Chưa có"
    return f"{value * 100:.1f}%"


def _format_decimal(value: Optional[float], suffix: str = "") -> str:
    if value is None:
        return "Chưa có"
    return f"{value:.2f}{suffix}"


def _training_summary(csv_path: Path) -> Dict[str, Any]:
    rows = _read_training_results(str(csv_path))
    if not rows:
        return {"rows": 0}

    final_row = rows[-1]
    best_map50, best_map50_epoch = _best_value(rows, "metrics/mAP50(B)")
    best_map95, best_map95_epoch = _best_value(rows, "metrics/mAP50-95(B)")
    first_loss = _total_loss(rows[0])
    final_loss = _total_loss(final_row)
    final_epoch = _float_value(final_row, "epoch")

    return {
        "rows": len(rows),
        "epochs": None if final_epoch is None else int(final_epoch),
        "best_map50": best_map50,
        "best_map50_epoch": best_map50_epoch,
        "best_map95": best_map95,
        "best_map95_epoch": best_map95_epoch,
        "final_precision": _float_value(final_row, "metrics/precision(B)"),
        "final_recall": _float_value(final_row, "metrics/recall(B)"),
        "final_loss": final_loss,
        "loss_drop": None if first_loss is None or final_loss is None else first_loss - final_loss,
    }


def _training_notes(summary: Dict[str, Any]) -> List[str]:
    if not summary.get("rows"):
        return ["Chưa có results.csv trong run này; đọc trực tiếp xu hướng từ các biểu đồ bên dưới."]

    notes: List[str] = []
    map50 = summary.get("best_map50")
    map95 = summary.get("best_map95")
    precision = summary.get("final_precision")
    recall = summary.get("final_recall")
    loss_drop = summary.get("loss_drop")

    if map50 is not None:
        if map50 >= 0.9:
            notes.append("mAP50 đạt mức rất tốt, model bắt được phần lớn đối tượng ở ngưỡng IoU 0.50.")
        elif map50 >= 0.8:
            notes.append("mAP50 ở mức tốt, đủ ổn cho demo và cần kiểm thêm trên dữ liệu thực tế.")
        elif map50 >= 0.6:
            notes.append("mAP50 ở mức trung bình, nên xem kỹ confusion matrix và mẫu dự đoán lỗi.")
        else:
            notes.append("mAP50 còn thấp, model cần bổ sung dữ liệu hoặc cân bằng lại nhãn.")

    if map50 is not None and map95 is not None and (map50 - map95) > 0.18:
        notes.append("Khoảng cách mAP50 và mAP50-95 còn lớn, bbox có thể chưa thật chặt ở các ngưỡng IoU cao.")

    if precision is not None and recall is not None:
        if recall + 0.08 < precision:
            notes.append("Recall thấp hơn precision, model đang bỏ sót nhiều hơn là nhận nhầm.")
        elif precision + 0.08 < recall:
            notes.append("Precision thấp hơn recall, cần kiểm tra false positive trên PR/confusion matrix.")
        else:
            notes.append("Precision và recall khá cân bằng ở epoch cuối.")

    if loss_drop is not None and loss_drop > 0:
        notes.append("Tổng train loss giảm so với epoch đầu, quá trình học có xu hướng hội tụ.")

    return notes


def _render_training_metrics(summary: Dict[str, Any]) -> None:
    if not summary.get("rows"):
        st.info("Chưa có bảng metric CSV cho run này.")
        return

    metric_cols = st.columns(5)
    metric_cols[0].metric("Epoch", str(summary.get("epochs", "Chưa có")))
    metric_cols[1].metric("Best mAP50", _format_percent(summary.get("best_map50")))
    metric_cols[2].metric("Best mAP50-95", _format_percent(summary.get("best_map95")))
    metric_cols[3].metric("Precision cuối", _format_percent(summary.get("final_precision")))
    metric_cols[4].metric("Recall cuối", _format_percent(summary.get("final_recall")))

    loss_cols = st.columns(2)
    loss_cols[0].metric("Train loss cuối", _format_decimal(summary.get("final_loss")))
    loss_cols[1].metric("Mức giảm train loss", _format_decimal(summary.get("loss_drop")))


def _render_chart_grid(run_dir: Path, charts: Sequence[Tuple[str, str]], columns: int = 2) -> None:
    available = [(run_dir / filename, caption) for filename, caption in charts if (run_dir / filename).exists()]
    if not available:
        st.info("Chưa tìm thấy ảnh biểu đồ trong thư mục run.")
        return

    for start in range(0, len(available), columns):
        cols = st.columns(columns)
        for col, (path, caption) in zip(cols, available[start:start + columns]):
            col.image(str(path), caption=caption, use_container_width=True)


def render_training_evaluation_section() -> None:
    st.markdown(
        """
        <div class="section-heading">
            <h2>Đánh Giá Training Model</h2>
            <p>Các số liệu và biểu đồ được đọc từ artifact training có sẵn trong thư mục model.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Xem biểu đồ training và nhận xét", expanded=True):
        tabs = st.tabs([info["label"] for info in TRAINING_EVALUATION_RUNS.values()])
        for tab, (_, info) in zip(tabs, TRAINING_EVALUATION_RUNS.items()):
            with tab:
                run_dir = info["run_dir"]
                csv_path = info["csv_path"]
                weights_path = info["weights_path"]
                summary = _training_summary(csv_path)

                st.markdown(
                    f"""
                    <div class="artifact-path">
                        Run: {_relative_path(run_dir)}<br>
                        Weights: {_relative_path(weights_path)}<br>
                        Phạm vi: {info["scope"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if info.get("csv_note"):
                    st.caption(info["csv_note"])

                _render_training_metrics(summary)

                notes = _training_notes(summary)
                if notes:
                    st.markdown("**Nhận xét nhanh**")
                    for note in notes:
                        st.markdown(f"- {note}")

                chart_tabs = st.tabs(["Metric curves", "Confusion / PR", "Mẫu dữ liệu"])
                with chart_tabs[0]:
                    _render_chart_grid(run_dir, (TRAINING_CHARTS[0],), columns=1)
                with chart_tabs[1]:
                    _render_chart_grid(run_dir, TRAINING_CHARTS[1:], columns=2)
                with chart_tabs[2]:
                    _render_chart_grid(run_dir, TRAINING_SAMPLE_IMAGES, columns=3)


def _module_count_value(module_name: str, count: int) -> str:
    if module_name == "lane_segmentation":
        return "Có mask" if count > 0 else "Không phát hiện"
    return str(count)


def _render_result_group(title: str, counts: Dict[str, int], module_names: Sequence[str]) -> str:
    rows = []
    for module_name in module_names:
        label = MODULE_UI_LABELS.get(module_name, MODULE_LABELS.get(module_name, module_name))
        value = _module_count_value(module_name, int(counts.get(module_name, 0)))
        rows.append(f'<div class="result-row"><span>{label}</span><strong>{value}</strong></div>')
    return f'<div class="result-card"><h3>{title}</h3>{"".join(rows)}</div>'


def _render_analysis_metrics(counts: Dict[str, int], elapsed: float) -> None:
    fps = (1.0 / elapsed) if elapsed > 0 else 0.0
    detected_total = (
        int(counts.get("pedestrian", 0))
        + int(counts.get("vehicle", 0))
        + int(counts.get("lane_detection", 0))
        + int(counts.get("traffic_sign", 0))
    )
    metric_cols = st.columns(4)
    metric_cols[0].metric("Trạng thái", "Hoàn tất")
    metric_cols[1].metric("Thời gian xử lý", f"{elapsed:.2f}s")
    metric_cols[2].metric("FPS ước tính", f"{fps:.2f}")
    metric_cols[3].metric("Đối tượng / vạch", str(detected_total))


def _render_detection_summary(counts: Dict[str, int]) -> None:
    cols = st.columns(3)
    groups = (
        ("Phương Tiện", ("vehicle", "pedestrian")),
        ("Làn Đường", ("lane_detection", "lane_segmentation")),
        ("Biển Báo", ("traffic_sign",)),
    )
    for col, (title, module_names) in zip(cols, groups):
        col.markdown(_render_result_group(title, counts, module_names), unsafe_allow_html=True)


OBJECT_TYPE_VI = {
    "car": "Xe hơi",
    "xe_hoi": "Xe hơi",
    "motorcycle": "Xe máy",
    "motorbike": "Xe máy",
    "xe_may": "Xe máy",
    "person": "Người đi bộ",
    "pedestrian": "Người đi bộ",
    "nguoi_di_bo": "Người đi bộ",
    "vehicle": "Phương tiện",
    "lane": "Vạch làn",
}

PRIORITY_VI = {
    "CRITICAL": "Khẩn cấp",
    "HIGH": "Cao",
    "MEDIUM": "Trung bình",
    "LOW": "Thấp",
    "INFO": "Thông tin",
}

WARNING_TYPE_VI = {
    "Left Lane Departure": "Lệch làn trái",
    "Right Lane Departure": "Lệch làn phải",
    "Lane Departure": "Lệch làn",
    "Speed Limit": "Giới hạn tốc độ",
    "Overspeed": "Vượt tốc độ",
    "STOP": "Biển dừng",
    "NO_ENTRY": "Cấm đi vào",
    "No Entry": "Cấm đi vào",
    "TRAFFIC_SIGN": "Biển báo giao thông",
}


def _object_type_vi(value: Any) -> str:
    key = str(value or "").strip()
    normalized = key.lower().replace("-", "_").replace(" ", "_")
    return OBJECT_TYPE_VI.get(normalized, key or "Đối tượng")


def _priority_vi(value: Any) -> str:
    key = str(value or "INFO").upper()
    return PRIORITY_VI.get(key, key)


def _bbox_from_value(value: Any) -> Optional[Tuple[float, float, float, float]]:
    if value is None:
        return None

    bbox = value.get("bbox") if isinstance(value, dict) else value
    if isinstance(bbox, dict):
        try:
            return (
                float(bbox["x1"]),
                float(bbox["y1"]),
                float(bbox["x2"]),
                float(bbox["y2"]),
            )
        except (KeyError, TypeError, ValueError):
            return None

    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        try:
            return tuple(float(item) for item in bbox[:4])  # type: ignore[return-value]
        except (TypeError, ValueError):
            return None

    if isinstance(value, dict):
        try:
            return (
                float(value["x1"]),
                float(value["y1"]),
                float(value["x2"]),
                float(value["y2"]),
            )
        except (KeyError, TypeError, ValueError):
            return None

    return None


def _bbox_to_text(bbox: Optional[Tuple[float, float, float, float]]) -> str:
    if bbox is None:
        return "Chưa có"
    x1, y1, x2, y2 = bbox
    return f"({x1:.0f}, {y1:.0f}) - ({x2:.0f}, {y2:.0f})"


def _bbox_iou(
    first: Optional[Tuple[float, float, float, float]],
    second: Optional[Tuple[float, float, float, float]],
) -> float:
    if first is None or second is None:
        return 0.0

    ax1, ay1, ax2, ay2 = first
    bx1, by1, bx2, by2 = second
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    first_area = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    second_area = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = first_area + second_area - intersection
    return 0.0 if union <= 0 else intersection / union


def _find_track_for_bbox(
    bbox: Optional[Tuple[float, float, float, float]],
    tracks: Sequence[Any],
    class_name: str,
) -> Optional[Any]:
    best_track = None
    best_iou = 0.0
    for track in tracks:
        if getattr(track, "class_name", "") != class_name:
            continue
        track_bbox = _bbox_from_value(getattr(track, "bbox", None))
        score = _bbox_iou(bbox, track_bbox)
        if score > best_iou:
            best_iou = score
            best_track = track
    return best_track if best_iou >= 0.1 else None


def _confidence_percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "Chưa có"


def _build_object_details(
    vehicle_detections: Sequence[Dict[str, Any]],
    pedestrian_detections: Sequence[Dict[str, Any]],
    lane_detections: Sequence[Dict[str, Any]],
    traffic_sign_detections: Sequence[Dict[str, Any]],
    tracks: Sequence[Any],
) -> Dict[str, List[Dict[str, Any]]]:
    details: Dict[str, List[Dict[str, Any]]] = {
        "vehicles": [],
        "pedestrians": [],
        "lane_detections": [],
        "traffic_signs": [],
    }

    for index, detection in enumerate(vehicle_detections, 1):
        bbox = _bbox_from_value(detection)
        track = _find_track_for_bbox(bbox, tracks, "vehicle")
        track_id = getattr(track, "track_id", None)
        details["vehicles"].append(
            {
                "STT": index,
                "ID": f"ID {track_id}" if track_id is not None else f"Phát hiện {index}",
                "Loại": _object_type_vi(detection.get("label_vi", detection.get("class_name"))),
                "Độ tin cậy": _confidence_percent(detection.get("confidence")),
                "BBox": _bbox_to_text(bbox),
                "Trạng thái": "Đã gán track" if track_id is not None else "Chưa gán track",
            }
        )

    for index, detection in enumerate(pedestrian_detections, 1):
        bbox = _bbox_from_value(detection)
        track = _find_track_for_bbox(bbox, tracks, "pedestrian")
        track_id = getattr(track, "track_id", None)
        details["pedestrians"].append(
            {
                "STT": index,
                "ID": f"ID {track_id}" if track_id is not None else f"Phát hiện {index}",
                "Loại": "Người đi bộ",
                "Độ tin cậy": _confidence_percent(detection.get("confidence")),
                "BBox": _bbox_to_text(bbox),
                "Trạng thái": "Đã gán track" if track_id is not None else "Chưa gán track",
            }
        )

    for index, detection in enumerate(lane_detections, 1):
        bbox = _bbox_from_value(detection)
        details["lane_detections"].append(
            {
                "STT": index,
                "Loại": _object_type_vi(detection.get("class_name", "lane")),
                "Độ tin cậy": _confidence_percent(detection.get("conf", detection.get("confidence"))),
                "BBox": _bbox_to_text(bbox),
            }
        )

    for index, detection in enumerate(traffic_sign_detections, 1):
        bbox = _bbox_from_value(detection)
        details["traffic_signs"].append(
            {
                "STT": index,
                "ID": f"Biển báo {detection.get('id', index)}",
                "Loại": _translate_sign_text(detection.get("class", "Biển báo giao thông")),
                "Độ tin cậy": _confidence_percent(detection.get("confidence")),
                "BBox": _bbox_to_text(bbox),
            }
        )

    return details


def _render_table(title: str, rows: Sequence[Dict[str, Any]], empty_text: str) -> None:
    st.markdown(f"**{title}**")
    if not rows:
        st.info(empty_text)
        return
    st.dataframe(list(rows), hide_index=True, use_container_width=True)


def _render_object_details(analysis: FrameAnalysis) -> None:
    details = analysis.object_details or {}
    st.markdown("**Chi tiết đối tượng và ID**")
    tabs = st.tabs(["Phương tiện", "Người đi bộ", "Làn đường", "Biển báo"])
    with tabs[0]:
        _render_table("Danh sách phương tiện", details.get("vehicles", []), "Không phát hiện phương tiện.")
    with tabs[1]:
        _render_table("Danh sách người đi bộ", details.get("pedestrians", []), "Không phát hiện người đi bộ.")
    with tabs[2]:
        _render_table("Danh sách vạch làn", details.get("lane_detections", []), "Không phát hiện vạch làn dạng bbox.")
    with tabs[3]:
        _render_table("Danh sách biển báo", details.get("traffic_signs", []), "Không phát hiện biển báo.")


def _translate_sign_text(value: Any) -> str:
    text = str(value or "").replace("_", " ").strip()
    replacements = (
        ("Gioi han toc do", "Giới hạn tốc độ"),
        ("Speed limit", "Giới hạn tốc độ"),
        ("Cam dung va do", "Cấm dừng và đỗ"),
        ("Cam con lai", "Biển cấm"),
        ("Cam di nguoc chieu", "Cấm đi ngược chiều"),
        ("Cam quay dau", "Cấm quay đầu"),
        ("Dung", "Dừng"),
        ("Stop", "Dừng"),
        ("Nguoi di bo", "Người đi bộ"),
        ("Pedestrian", "Người đi bộ"),
        ("Khu vuc hoc", "Khu vực trường học"),
        ("No entry", "Cấm đi vào"),
        ("Prohibited", "Biển cấm"),
    )
    for source, target in replacements:
        text = re.sub(source, target, text, flags=re.IGNORECASE)
    return text or "Biển báo giao thông"


def _translate_warning_message(warning: Dict[str, Any]) -> str:
    warning_type = str(warning.get("type", ""))
    message = str(warning.get("message", warning_type))

    exact_messages = {
        "Vehicle is departing to the left lane boundary": "Xe đang lệch sang vạch làn bên trái.",
        "Vehicle is departing to the right lane boundary": "Xe đang lệch sang vạch làn bên phải.",
        "Vehicle is departing from lane": "Xe đang lệch khỏi làn đường.",
        "Vehicle speed exceeds current speed limit": "Xe đang vượt quá tốc độ giới hạn hiện tại.",
        "Prepare to stop": "Chuẩn bị dừng xe.",
        "No entry warning": "Cảnh báo khu vực cấm đi vào.",
    }
    if message in exact_messages:
        return exact_messages[message]

    speed_match = re.search(r"Speed limit\s+(\d+)\s*km/h", message, flags=re.IGNORECASE)
    if speed_match:
        return f"Giới hạn tốc độ {speed_match.group(1)} km/h."

    if message.startswith("Traffic rule detected:"):
        rule_name = message.split(":", 1)[1].strip()
        return f"Phát hiện quy tắc giao thông: {_translate_sign_text(rule_name)}."

    if warning_type in {"NO_ENTRY", "STOP", "SPEED_LIMIT", "SCHOOL_ZONE", "PEDESTRIAN_CROSSING", "TRAFFIC_SIGN"}:
        return _translate_sign_text(message)

    if warning_type in WARNING_TYPE_VI:
        return WARNING_TYPE_VI[warning_type]

    return _translate_sign_text(message)


def _warning_title_vi(warning: Dict[str, Any], prefix: str, index: int) -> str:
    level = _priority_vi(warning.get("level", warning.get("priority", "INFO")))
    message = _translate_warning_message(warning)
    track_id = warning.get("track_id")
    track_text = f" - ID {track_id}" if track_id is not None else ""
    return f"{prefix} #{index} [{level}]{track_text}: {message}"


def _warning_level_to_streamlit(level: str) -> Any:
    normalized = str(level or "INFO").upper()
    if normalized in {"CRITICAL", "HIGH"}:
        return st.error
    if normalized == "MEDIUM":
        return st.warning
    return st.info


def _render_warning_summary(analysis: FrameAnalysis) -> None:
    traffic_warnings = getattr(analysis, "traffic_sign_warnings", None) or []
    adas_warnings = analysis.adas_output.get("warnings", []) if analysis.adas_output else []

    if not traffic_warnings and not adas_warnings:
        st.success("Không có cảnh báo ưu tiên cao trong khung hình hiện tại.")
        return

    st.markdown("**Cảnh báo hệ thống**")
    for index, warning in enumerate(traffic_warnings[:5], 1):
        level = warning.get("level", "MEDIUM")
        _warning_level_to_streamlit(level)(_warning_title_vi(warning, "Biển báo", index))

    for index, warning in enumerate(adas_warnings[:5], 1):
        level = warning.get("priority", "INFO")
        _warning_level_to_streamlit(level)(_warning_title_vi(warning, "ADAS", index))


def render_analysis_dashboard(
    source_image: np.ndarray,
    output_image: np.ndarray,
    analysis: FrameAnalysis,
    result_caption: str,
) -> None:
    st.markdown(
        """
        <div class="section-heading">
            <h2>Kết Quả Phân Tích</h2>
            <p>So sánh ảnh đầu vào, ảnh đã phân tích và trạng thái nhận diện trong cùng một màn hình.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    image_cols = st.columns(2)
    image_cols[0].image(
        cv2.cvtColor(source_image, cv2.COLOR_BGR2RGB),
        caption="Ảnh gốc",
        use_container_width=True,
    )
    image_cols[1].image(
        cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB),
        caption=result_caption,
        use_container_width=True,
    )

    _render_analysis_metrics(analysis.counts, analysis.elapsed_seconds)
    _render_detection_summary(analysis.counts)
    _render_object_details(analysis)
    _render_warning_summary(analysis)

    with st.expander("Scene Context / ADAS Output", expanded=False):
        st.json(analysis.scene_context)
        st.json(analysis.adas_output)


_FONT_CACHE: Dict[int, Any] = {}


def _get_unicode_font(font_size: int) -> Optional[Any]:
    if font_size in _FONT_CACHE:
        return _FONT_CACHE[font_size]

    try:
        from PIL import ImageFont
    except ImportError:
        return None

    font_candidates = (
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
    )
    for font_path in font_candidates:
        if font_path.exists():
            font = ImageFont.truetype(str(font_path), font_size)
            _FONT_CACHE[font_size] = font
            return font

    font = ImageFont.load_default()
    _FONT_CACHE[font_size] = font
    return font


def _strip_accents(text: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _text_size(text: str, font_size: int = 18) -> Tuple[int, int]:
    font = _get_unicode_font(font_size)
    if font is None:
        size = cv2.getTextSize(_strip_accents(text), cv2.FONT_HERSHEY_SIMPLEX, font_size / 28, 1)[0]
        return int(size[0]), int(size[1])

    try:
        left, top, right, bottom = font.getbbox(text)
        return right - left, bottom - top
    except AttributeError:
        width, height = font.getsize(text)
        return int(width), int(height)


def _draw_text(
    frame: np.ndarray,
    text: str,
    position: Tuple[int, int],
    color: Tuple[int, int, int],
    font_size: int = 18,
    stroke_width: int = 2,
) -> None:
    x, y = position
    x = max(0, min(int(x), max(frame.shape[1] - 1, 0)))
    y = max(0, min(int(y), max(frame.shape[0] - 1, 0)))

    font = _get_unicode_font(font_size)
    if font is None:
        cv2.putText(
            frame,
            _strip_accents(text),
            (x, y + font_size),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_size / 28,
            color,
            max(1, stroke_width),
        )
        return

    from PIL import Image, ImageDraw

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image)
    rgb_color = (int(color[2]), int(color[1]), int(color[0]))
    draw.text(
        (x, y),
        text,
        font=font,
        fill=rgb_color,
        stroke_width=stroke_width,
        stroke_fill=(0, 0, 0),
    )
    frame[:, :, :] = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _translate_lane_label(value: Any) -> str:
    text = str(value or "Vạch làn").lower()
    mapping = {
        "broken_and_solid_lines_white_lane": "Vạch trắng đứt và liền",
        "broken_and_solid_lines_yellow_lane": "Vạch vàng đứt và liền",
        "broken_line_white_lane": "Vạch trắng đứt",
        "broken_line_yellow_lane": "Vạch vàng đứt",
        "double_solid_line_white_lane": "Hai vạch trắng liền",
        "double_solid_line_yellow_lane": "Hai vạch vàng liền",
        "left_turn": "Mũi tên rẽ trái",
        "right_turn": "Mũi tên rẽ phải",
        "solid_line_white_lane": "Vạch trắng liền",
        "solid_line_yellow_lane": "Vạch vàng liền",
        "straight_way": "Mũi tên đi thẳng",
        "lane": "Vạch làn",
    }
    return mapping.get(text, str(value or "Vạch làn").replace("_", " ").title())


def _draw_vehicle_detections(frame: np.ndarray, detections: Sequence[Dict[str, Any]]) -> None:
    colors = {
        "person": (40, 220, 40),
        "car": (255, 120, 40),
        "motorcycle": (40, 180, 255),
    }
    for detection in detections:
        bbox = detection.get("bbox", {})
        try:
            x1 = int(bbox["x1"])
            y1 = int(bbox["y1"])
            x2 = int(bbox["x2"])
            y2 = int(bbox["y2"])
        except (KeyError, TypeError, ValueError):
            continue

        class_name = str(detection.get("class_name", "vehicle"))
        confidence = float(detection.get("confidence", 0.0))
        color = colors.get(class_name, (255, 255, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        _draw_text(
            frame,
            f"{_object_type_vi(detection.get('label_vi', class_name))} {confidence:.2f}",
            (x1, max(y1 - 24, 2)),
            color,
            font_size=16,
            stroke_width=2,
        )


def _draw_traffic_sign_detections(frame: np.ndarray, detections: Sequence[Dict[str, Any]]) -> np.ndarray:
    output = frame.copy()
    color = MODULE_COLORS["traffic_sign"]
    for detection in detections:
        bbox = _bbox_from_value(detection)
        if bbox is None:
            continue
        x1, y1, x2, y2 = [int(value) for value in bbox]
        confidence = float(detection.get("confidence", 0.0))
        label = _translate_sign_text(detection.get("class", "Biển báo"))
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        _draw_text(
            output,
            f"{label} {confidence:.2f}",
            (x1, max(y1 - 24, 2)),
            color,
            font_size=16,
            stroke_width=2,
        )
    return output


def _lane_status_vi(status: Any) -> str:
    mapping = {
        "SAFE": "An toàn",
        "NEAR_BOUNDARY": "Gần vạch làn",
        "LEFT_LANE_DEPARTURE": "Lệch làn trái",
        "RIGHT_LANE_DEPARTURE": "Lệch làn phải",
        "LANE_DEPARTURE": "Lệch làn",
        "LANE_UNKNOWN": "Chưa rõ làn",
    }
    return mapping.get(str(status or "LANE_UNKNOWN"), "Chưa rõ làn")


def _draw_lane_departure_overlay_vi(frame: np.ndarray, results: Iterable[Dict[str, Any]]) -> np.ndarray:
    status_colors = {
        "SAFE": (0, 200, 0),
        "NEAR_BOUNDARY": (0, 220, 255),
        "LEFT_LANE_DEPARTURE": (0, 0, 255),
        "RIGHT_LANE_DEPARTURE": (0, 0, 255),
        "LANE_DEPARTURE": (0, 0, 255),
        "LANE_UNKNOWN": (180, 180, 180),
    }
    output = frame.copy()
    for result in results:
        center = result.get("vehicle_center")
        if isinstance(center, list) and len(center) >= 2:
            cx, cy = int(center[0]), int(center[1])
            status = str(result.get("status", "LANE_UNKNOWN"))
            color = status_colors.get(status, (255, 255, 255))
            cv2.circle(output, (cx, cy), 5, color, -1)
            _draw_text(
                output,
                f"LDW: {_lane_status_vi(status)}",
                (max(cx - 80, 5), max(cy - 28, 2)),
                color,
                font_size=16,
                stroke_width=2,
            )

        lane_center = result.get("lane_center")
        if lane_center is not None:
            x = int(lane_center)
            cv2.line(output, (x, 0), (x, output.shape[0] - 1), (255, 255, 255), 1)

    return output


def _draw_box(frame: np.ndarray, detection: Dict[str, Any], color: Tuple[int, int, int]) -> None:
    x1 = int(detection.get("x1", 0))
    y1 = int(detection.get("y1", 0))
    x2 = int(detection.get("x2", 0))
    y2 = int(detection.get("y2", 0))
    label = _object_type_vi(detection.get("label_vi", detection.get("class_name", "object")))
    confidence = float(detection.get("confidence", 0.0))
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    _draw_text(
        frame,
        f"{label} {confidence:.2f}",
        (x1, max(y1 - 24, 2)),
        color,
        font_size=16,
        stroke_width=2,
    )


def _draw_lane_detections(frame: np.ndarray, detections: Sequence[Dict[str, Any]]) -> None:
    """Vẽ lane detections: ưu tiên vẽ mask outline (polygon), fallback bbox nếu không có mask."""
    for detection in detections:
        mask = detection.get("mask")
        label = _translate_lane_label(detection.get("class_name", "lane"))
        confidence = float(detection.get("conf", detection.get("confidence", 0.0)))
        color = MODULE_COLORS["lane_detection"]
        text = f"{label} {confidence:.2f}"

        if mask is not None and int(np.count_nonzero(mask)) > 0:
            # Vẽ contour outline cho mask thay vì bbox (vì YOLO-seg bbox rất rộng)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(frame, contours, -1, color, 2)

            # Đặt label tại top của mask bounding region
            ys, xs = np.where(mask > 0)
            if len(xs) > 0:
                tx = int(np.min(xs))
                ty = int(np.min(ys))
                _draw_text(frame, text, (tx, max(ty - 22, 2)), color, font_size=15, stroke_width=2)
        else:
            # Fallback: vẽ bbox
            bbox = detection.get("bbox", [])
            if len(bbox) < 4:
                continue
            x1, y1, x2, y2 = [int(value) for value in bbox[:4]]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            _draw_text(frame, text, (x1, max(y1 - 22, 2)), color, font_size=15, stroke_width=2)


def _overlay_lane_mask(frame: np.ndarray, mask: Optional[np.ndarray], lane_color_bgr: Tuple[int, int, int] = (120, 120, 255)) -> np.ndarray:
    if mask is None or mask.size == 0 or int(np.count_nonzero(mask)) == 0:
        return frame
    overlay = frame.copy()
    color_layer = np.zeros_like(frame)
    color_layer[mask > 0] = lane_color_bgr
    cv2.addWeighted(color_layer, 0.45, overlay, 0.55, 0, overlay)
    return overlay


# Màu BGR cho từng class trong lane segmentation
# Phong cách ADAS phổ biến:
#   - lane_line: trắng nhạt (220, 220, 220) — outline trong suốt, mỏng, sát vạch
#   - road:      đỏ pastel (120, 130, 220) — nền đường xe đang đi (alpha thấp)
LANE_SEG_CLASS_COLORS = {
    "lane_line": (220, 220, 220),  # trắng nhạt
    "road": (120, 130, 220),      # đỏ pastel
}


def _overlay_lane_class_masks(
    frame: np.ndarray,
    class_masks: Optional[Dict[str, np.ndarray]],
    sky_top_fraction: float = 0.45,
    lane_band_horizontal: int = 90,
    lane_band_vertical: int = 200,
) -> np.ndarray:
    """Overlay từng class với màu riêng.

    Pipeline:
    1. lane_line mask thường phủ cả bầu trời / nhà / cây vì model yếu.
       Ta ép lane_mask chỉ giữ phần ở nửa dưới ảnh (vạch thật nằm ở mặt đất).
    2. Từ lane_mask thật, dilate ellipse nhỏ vừa đủ để ra "vùng lane xe đang đi".
    3. Vẽ MỘT lớp hồng phấn nhạt đồng nhất. Không chồng thêm lớp đậm nữa.
    """
    if not class_masks:
        return frame

    overlay = frame.copy()
    h = frame.shape[0]
    w = frame.shape[1]
    ground_cutoff = int(h * sky_top_fraction)

    lane_mask_raw = class_masks.get("lane_line")
    road_mask = class_masks.get("road")

    # Bước 1: lọc lane_mask - CHỈ giữ phần dưới ground_cutoff
    lane_mask_clean = np.zeros((h, w), dtype=np.uint8)
    if lane_mask_raw is not None and int(np.count_nonzero(lane_mask_raw)) > 0:
        ground_only = lane_mask_raw[ground_cutoff:, :].copy()
        if int(np.count_nonzero(ground_only)) > 0:
            lane_mask_clean[ground_cutoff:, :] = ground_only
        else:
            if road_mask is not None:
                ground_road = road_mask[ground_cutoff:, :].copy()
                if int(np.count_nonzero(ground_road)) > 0:
                    lane_mask_clean[ground_cutoff:, :] = ground_road

    if int(np.count_nonzero(lane_mask_clean)) == 0:
        return overlay

    has_road = road_mask is not None and int(np.count_nonzero(road_mask)) > 0

    # Bước 2: dilate thành lane band rồi close lỗ
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (lane_band_horizontal, lane_band_vertical)
    )
    lane_band = cv2.dilate(lane_mask_clean, kernel, iterations=1)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (60, 60))
    lane_band = cv2.morphologyEx(lane_band, cv2.MORPH_CLOSE, close_kernel)
    lane_band[:ground_cutoff, :] = 0  # giữ nửa dưới

    # Bước 3a: vẽ ROAD overlay (đỏ pastel) - alpha thấp → trong, không át cảnh
    if has_road:
        road_clean = np.zeros((h, w), dtype=np.uint8)
        ground_road = road_mask[ground_cutoff:, :]
        if int(np.count_nonzero(ground_road)) > 0:
            road_clean[ground_cutoff:, :] = ground_road
        color_layer = np.zeros_like(overlay)
        color_layer[road_clean > 0] = LANE_SEG_CLASS_COLORS["road"]
        cv2.addWeighted(color_layer, 0.18, overlay, 0.82, 0, overlay)
    elif int(np.count_nonzero(lane_band)) > 0:
        # Fallback: dùng lane_band nếu không có road mask riêng
        color_layer = np.zeros_like(overlay)
        color_layer[lane_band > 0] = LANE_SEG_CLASS_COLORS["road"]
        cv2.addWeighted(color_layer, 0.16, overlay, 0.84, 0, overlay)

    # Bước 3b: vẽ LANE_LINE outline (trắng nhạt, trong) - nét mỏng 1px
    contours, _ = cv2.findContours(
        lane_mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    cv2.drawContours(
        overlay, contours, -1, LANE_SEG_CLASS_COLORS["lane_line"], 1
    )

    return overlay



def _draw_tracks(frame: np.ndarray, tracks: Iterable[Any]) -> None:
    h = frame.shape[0]
    near_threshold_ratio = 0.55  # bbox_bottom > 55% chiều cao ảnh = vật gần
    for track in tracks:
        bbox = getattr(track, "bbox", None)
        if bbox is None or len(bbox) < 4:
            continue
        x1, y1, x2, y2 = [int(value) for value in bbox[:4]]
        track_id = getattr(track, "track_id", "?")
        class_name = getattr(track, "class_name", "object")
        class_vi = _object_type_vi(class_name)

        # Phân biệt vật gần / xa để ưu tiên hiển thị
        bbox_bottom_ratio = y2 / max(h, 1)
        is_near = bbox_bottom_ratio > near_threshold_ratio

        if is_near:
            color = (0, 255, 255)        # vàng cyan - vật gần
            label = f"ID {track_id} {class_vi}"
            font_size = 18
            stroke = 1
            bbox_thick = 2
        else:
            color = (0, 200, 0)          # xanh lá - vật xa
            label = class_vi             # chỉ tên class, bỏ ID cho gọn
            font_size = 14
            stroke = 1
            bbox_thick = 2

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, bbox_thick)
        _draw_text(
            frame,
            label,
            (x1, min(y2 + 4, frame.shape[0] - 28)),
            color,
            font_size=font_size,
            stroke_width=stroke,
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
        label = f"{_priority_vi(priority)}: {_translate_warning_message(warning)}"
        _draw_text(
            annotated,
            label,
            (10, y),
            (0, 0, 255) if priority in {"HIGH", "CRITICAL"} else (0, 255, 255),
            font_size=18,
            stroke_width=2,
        )
        y += 24
    return annotated


def _draw_traffic_sign_warnings(frame: np.ndarray, warnings: List[Dict[str, Any]]) -> np.ndarray:
    """Vẽ cảnh báo biển báo dưới ảnh"""
    if not warnings:
        return frame
    
    annotated = frame.copy()
    h, w = annotated.shape[:2]
    line_height = 30
    margin = 8
    text_color = (255, 255, 255)
    max_text_width = max(120, int(w * 0.56))
    
    def _fit_label(label: str) -> str:
        while len(label) > 12 and _text_size(label, font_size=18)[0] > max_text_width:
            label = label[:-4].rstrip() + "..."
        return label
    
    # Place warnings in the top-right to avoid ADAS/lane text below.
    y = 24
    max_items = min(5, max(1, (h - margin * 2) // line_height))
    
    for warning in warnings[:max_items]:  # Tối đa 5 warnings
        level = warning.get("level", "MEDIUM")
        msg = _translate_warning_message(warning)
        
        label = _fit_label(f"[{_priority_vi(level)}] {msg}")
        text_size = _text_size(label, font_size=18)
        x = max(margin, w - text_size[0] - margin)
        
        # Text
        _draw_text(
            annotated,
            label,
            (x, y),
            text_color,
            font_size=18,
            stroke_width=2,
        )
        y += line_height
    
    return annotated


def _select_ego_vehicle(
    vehicles: Sequence[Dict[str, Any]],
    image_width: int,
) -> List[Dict[str, Any]]:
    """Chọn xe 'ego' (xe mình) trong danh sách vehicles.

    Trong cam trước (front-facing ADAS), xe mình là:
      - Xe gần giữa ảnh nhất (gần image_width/2 theo phương ngang)
      - VÀ có bbox-bottom lớn nhất (gần camera nhất)
    Score = |vehicle_center.x - image_width/2| - vehicle_center.y
    (càng nhỏ càng tốt: gần center và xuống thấp = gần cam)

    Returns list chứa 0 hoặc 1 xe. Nếu vehicles rỗng, trả [].
    """
    if not vehicles:
        return []

    image_center_x = image_width / 2.0
    candidates = []

    for vehicle in vehicles:
        center = vehicle.get("center")
        if not center or len(center) < 2:
            continue
        try:
            cx = float(center[0])
            cy = float(center[1])
        except (TypeError, ValueError):
            continue
        # Score: khoảng cách ngang tới center, trừ đi y lớn (gần cam hơn)
        score = abs(cx - image_center_x) - cy * 0.5
        candidates.append((score, vehicle))

    if not candidates:
        return [vehicles[0]] if vehicles else []

    candidates.sort(key=lambda x: x[0])
    return [candidates[0][1]]


def _filter_lane_departure_for_ego(
    lane_departure_results: Sequence[Dict[str, Any]],
    image_width: int,
) -> List[Dict[str, Any]]:
    """Lọc lane_departure: chỉ giữ kết quả của xe ego (gần center + gần cam nhất)."""
    if not lane_departure_results:
        return list(lane_departure_results) if lane_departure_results else []

    # Nếu chỉ 1 kết quả thì giữ luôn
    if len(lane_departure_results) == 1:
        return list(lane_departure_results)

    image_center_x = image_width / 2.0
    candidates = []

    for result in lane_departure_results:
        center = result.get("vehicle_center")
        if not center or len(center) < 2:
            continue
        try:
            cx = float(center[0])
            cy = float(center[1])
        except (TypeError, ValueError):
            continue
        score = abs(cx - image_center_x) - cy * 0.5
        candidates.append((score, result))

    if not candidates:
        return list(lane_departure_results[:1])

    candidates.sort(key=lambda x: x[0])
    return [candidates[0][1]]


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
    vehicle_detections: List[Dict[str, Any]] = []
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
            vehicle_detections = vehicle_result.get("detections", []) if isinstance(vehicle_result, dict) else []
            counts["vehicle"] = len(vehicle_detections)
            _draw_vehicle_detections(output, vehicle_detections)
        elif module_name == "lane_detection":
            lane_detections, _lane_masks = models["lane_detection"].detect_with_masks(frame, debug=True)
            counts["lane_detection"] = len(lane_detections)
            _draw_lane_detections(output, lane_detections)
        elif module_name == "lane_segmentation":
            lane_class_masks = models["lane_segmentation"].get_all_class_masks(frame)
            lane_mask = lane_class_masks.get("lane_line")
            counts["lane_segmentation"] = int(np.count_nonzero(lane_mask)) if lane_mask is not None else 0
            output = _overlay_lane_class_masks(output, lane_class_masks)
        elif module_name == "traffic_sign":
            output, traffic_sign_detections = models["traffic_sign"].detect_with_detections(frame, draw_on=output)
            counts["traffic_sign"] = getattr(models["traffic_sign"], "last_count", 0)
            # Generate warnings từ traffic sign detections
            traffic_sign_warnings = _generate_traffic_sign_warnings(traffic_sign_detections)
            # Vẽ warnings lên ảnh
            output = _draw_traffic_sign_warnings(output, traffic_sign_warnings)

    tracks = []
    if vehicle_result is not None or pedestrian_detections:
        tracking_frame = _prepare_tracking_frame(
            frame,
            enable_preprocessing=bool(models.get("preprocessing_enabled", False)),
        )
        tracks = models["tracker"].update(
            vehicle_detections=vehicle_result,
            pedestrian_detections=pedestrian_detections,
            frame=tracking_frame,
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

    # Lane departure chỉ áp dụng cho xe ego (cam trước): gần center + gần nhất
    image_width = frame.shape[1]
    ego_lane_departure = _filter_lane_departure_for_ego(
        adas_output_dict.get("lane_departure", []), image_width=image_width
    )
    adas_output_dict["lane_departure"] = ego_lane_departure
    object_details = _build_object_details(
        vehicle_detections=vehicle_detections,
        pedestrian_detections=pedestrian_detections,
        lane_detections=lane_detections,
        traffic_sign_detections=traffic_sign_detections,
        tracks=tracks,
    )
    output = _draw_lane_departure_overlay_vi(output, adas_output_dict.get("lane_departure", []))
    output = _annotate_frame_with_warnings(output, adas_output_dict)

    elapsed = (cv2.getTickCount() - started) / cv2.getTickFrequency()
    frame_analysis = FrameAnalysis(
        image=output,
        counts=counts,
        elapsed_seconds=elapsed,
        scene_context=scene_context_dict,
        adas_output=adas_output_dict,
        object_details=object_details,
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
        label = MODULE_UI_LABELS.get(module_name, MODULE_LABELS.get(module_name, module_name))
        value = _module_count_value(module_name, int(counts.get(module_name, 0)))
        text_lines.append(f"{label}: {value}")

    y = 8
    for line in text_lines:
        _draw_text(
            annotated,
            line,
            (10, y),
            (255, 255, 255),
            font_size=18,
            stroke_width=2,
        )
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
) -> Tuple[str, float, Optional[np.ndarray], Optional[np.ndarray], Optional[FrameAnalysis]]:
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
    final_source_frame: Optional[np.ndarray] = None
    final_output_frame: Optional[np.ndarray] = None
    final_analysis: Optional[FrameAnalysis] = None
    progress_bar = st.progress(0)
    status = st.empty()

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            processed_frames += 1
            final_source_frame = frame.copy()
            analysis = process_image(frame, models, modules, frame_index=processed_frames, fps=fps)
            annotated = _annotate_frame_with_counts(
                analysis.image,
                analysis.counts,
                analysis.elapsed_seconds,
                modules,
            )
            final_analysis = analysis
            final_output_frame = annotated.copy()
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
    return str(output_path), avg_fps, final_source_frame, final_output_frame, final_analysis



def render_sidebar() -> StreamlitConfig:
    st.sidebar.title("ADAS Control")
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
        checked = st.sidebar.checkbox(MODULE_UI_LABELS.get(key, label), value=True, key=f"module_{key}")
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
    render_analysis_dashboard(image, output, analysis, "Ảnh đã phân tích")

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
    output_path, avg_fps, final_source_frame, final_output_frame, final_analysis = process_video(
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
    metric_cols = st.columns(2)
    metric_cols[0].metric("FPS trung bình", f"{avg_fps:.2f}")
    metric_cols[1].metric("Trạng thái", "Hoàn tất")
    st.caption(f"File kết quả: `{Path(output_path).name}`")

    if final_source_frame is not None and final_output_frame is not None and final_analysis is not None:
        st.markdown(
            """
            <div class="section-heading">
                <h2>Thống Kê Video</h2>
                <p>Thống kê chi tiết theo frame cuối cùng đã xử lý, gồm ID, loại đối tượng, lane, biển báo và cảnh báo.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_analysis_dashboard(final_source_frame, final_output_frame, final_analysis, "Frame video đã phân tích")
    else:
        st.warning("Video chưa có frame hợp lệ để hiển thị thống kê chi tiết.")

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
    render_analysis_dashboard(image, output, analysis, "Ảnh webcam đã phân tích")

    _, buffer = cv2.imencode(".png", output)
    st.download_button(
        "Tải ảnh webcam kết quả",
        data=buffer.tobytes(),
        file_name="webcam_annotated.png",
        mime="image/png",
    )



def main() -> None:
    st.set_page_config(page_title="ADAS Vietnam Vision Suite", layout="wide")
    inject_app_styles()
    render_app_header()

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
