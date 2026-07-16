"""Traffic-sign inference for images and videos."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from tkinter import Tk, filedialog
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

AI_SERVICE_ROOT = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_ROOT))

from ai_models.traffic_sign_detection.digit_recognizer import (
    DigitRecognition,
    DigitRecognizer,
    crop_bbox,
)
from preprocessing.image_processor import ImageProcessor
from preprocessing.utils.visualizer import save_comparison


SPEED_LIMIT_PREFIX = "Gioi han toc do"


def apply_preprocessing(
    frame: np.ndarray,
    enable_preprocessing: bool = True,
    preprocessing_config: Optional[Dict[str, Any]] = None,
    visualize: bool = False,
    output_dir: str = "",
) -> np.ndarray:
    """Apply traffic-sign preprocessing without changing frame dimensions."""
    if not enable_preprocessing or frame is None or frame.size == 0:
        return frame

    original = frame.copy()
    config = preprocessing_config or {"enable_preprocessing": True}
    processor = ImageProcessor(target_size=(frame.shape[1], frame.shape[0]))
    processed = processor.apply_module_preprocessing(
        frame,
        module_name="traffic_sign",
        config=config,
    )

    if visualize and output_dir:
        os.makedirs(output_dir, exist_ok=True)
        comparison_path = os.path.join(
            output_dir,
            "preprocessing_comparison.jpg",
        )
        save_comparison(
            original,
            processed,
            comparison_path,
            title="Traffic Sign Preprocessing",
        )

    return processed


def is_speed_limit_label(label: str) -> bool:
    normalized = str(label).lower()
    return (
        SPEED_LIMIT_PREFIX.lower() in normalized
        or "speed limit" in normalized
    )


def refine_detection_label(
    frame: np.ndarray,
    bbox: Sequence[float],
    model_text: str,
    mapping_fix: Optional[Mapping[str, str]] = None,
    digit_recognizer: Optional[DigitRecognizer] = None,
) -> Tuple[str, Optional[DigitRecognition]]:
    """Replace a speed-limit class using digits read from the sign crop."""
    final_text = (mapping_fix or {}).get(model_text, model_text)

    if digit_recognizer is None or not is_speed_limit_label(model_text):
        return final_text, None

    sign_crop = crop_bbox(frame, bbox)
    recognition = digit_recognizer.recognize(sign_crop)

    # YOLO only locates/classifies the speed-sign group. The speed value comes
    # exclusively from OCR, so never retain the numeric YOLO class as fallback.
    final_text = SPEED_LIMIT_PREFIX
    if recognition.succeeded:
        final_text = f"{SPEED_LIMIT_PREFIX} {recognition.value}kmh"

    return final_text, recognition


def parse_detections(
    frame: np.ndarray,
    results: Any,
    model_names: Any,
    mapping_fix: Optional[Mapping[str, str]] = None,
    digit_recognizer: Optional[DigitRecognizer] = None,
) -> List[Dict[str, Any]]:
    """Convert YOLO results into normalized traffic-sign detections."""
    detections: List[Dict[str, Any]] = []

    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue

        for index, box in enumerate(boxes, start=1):
            bbox = [
                float(value)
                for value in box.xyxy[0].tolist()
            ]
            class_id = int(box.cls[0])
            model_text = str(model_names[class_id])
            confidence = float(box.conf[0].item())

            final_text, recognition = refine_detection_label(
                frame=frame,
                bbox=bbox,
                model_text=model_text,
                mapping_fix=mapping_fix,
                digit_recognizer=digit_recognizer,
            )

            detections.append(
                {
                    "id": index,
                    "class_id": class_id,
                    "class": final_text,
                    "model_class": model_text,
                    "bbox": bbox,
                    "confidence": confidence,
                    "digit_value": (
                        recognition.value
                        if recognition is not None
                        else None
                    ),
                    "digit_confidence": (
                        recognition.confidence
                        if recognition is not None
                        else None
                    ),
                }
            )

    return detections


def draw_detections(
    frame: np.ndarray,
    detections: Sequence[Dict[str, Any]],
) -> np.ndarray:
    """Draw parsed traffic-sign detections on a frame."""
    output = frame.copy()

    for detection in detections:
        x1, y1, x2, y2 = [
            int(value)
            for value in detection["bbox"]
        ]
        confidence = detection.get("confidence", 0.0)
        if detection.get("digit_value") is not None:
            confidence = detection.get("digit_confidence", confidence)
        label = (
            f"{detection['class']} "
            f"{float(confidence):.2f}"
        )

        cv2.rectangle(
            output,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),
            3,
        )
        cv2.putText(
            output,
            label,
            (x1, max(y1 - 10, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    return output


def process_frame(
    frame: np.ndarray,
    results: Any,
    model_names: Any,
    mapping_fix: Optional[Mapping[str, str]] = None,
    digit_recognizer: Optional[DigitRecognizer] = None,
) -> np.ndarray:
    """Parse and draw YOLO traffic-sign results."""
    detections = parse_detections(
        frame=frame,
        results=results,
        model_names=model_names,
        mapping_fix=mapping_fix,
        digit_recognizer=digit_recognizer,
    )
    return draw_detections(frame, detections)


def infer_traffic_sign(
    model: YOLO,
    frame: np.ndarray,
    preprocessing_config: Optional[Dict[str, Any]] = None,
) -> Any:
    """Run traffic-sign inference."""
    config = preprocessing_config or {}

    return model.predict(
        source=frame,
        imgsz=int(config.get("imgsz", 960)),
        conf=float(config.get("conf", 0.15)),
        iou=float(config.get("iou", 0.45)),
        agnostic_nms=bool(config.get("agnostic_nms", True)),
        verbose=False,
    )


def choose_input_file() -> str:
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        return filedialog.askopenfilename(
            title="Chon anh hoac video bien bao giao thong",
            filetypes=[
                ("All files", "*.*"),
                ("Video files", "*.mp4;*.avi;*.mov;*.mkv"),
                ("Image files", "*.jpg;*.jpeg;*.png;*.webp;*.bmp"),
            ],
        )
    finally:
        root.destroy()


def print_detections(
    detections: Sequence[Dict[str, Any]],
) -> None:
    print("\n--- KET QUA PHAN TICH BIEN BAO ---")

    if not detections:
        print("Khong phat hien bien bao.")
        return

    for detection in detections:
        message = (
            f"Phat hien: {detection['class']} "
            f"({float(detection['confidence']) * 100:.1f}%)"
        )
        digit_confidence = detection.get("digit_confidence")
        if detection.get("digit_value") is not None:
            message += f" | Digit OCR: {digit_confidence:.2f}"
        print(message)


def process_image(
    input_path: Path,
    output_dir: Path,
    model: YOLO,
    mapping_fix: Mapping[str, str],
    digit_recognizer: DigitRecognizer,
) -> Path:
    frame = cv2.imread(str(input_path))
    if frame is None:
        raise ValueError(f"Khong the doc anh: {input_path}")

    inference_frame = apply_preprocessing(
        frame,
        enable_preprocessing=True,
        preprocessing_config={
            "enable_preprocessing": True,
            "apply_resize": False,
        },
        visualize=True,
        output_dir=str(output_dir),
    )
    results = infer_traffic_sign(model, inference_frame)
    detections = parse_detections(
        frame=frame,
        results=results,
        model_names=model.names,
        mapping_fix=mapping_fix,
        digit_recognizer=digit_recognizer,
    )

    print_detections(detections)
    annotated = draw_detections(frame, detections)
    output_path = output_dir / input_path.name

    if not cv2.imwrite(str(output_path), annotated):
        raise RuntimeError(f"Khong the ghi anh: {output_path}")

    return output_path


def process_video(
    input_path: Path,
    output_dir: Path,
    model: YOLO,
    mapping_fix: Mapping[str, str],
    digit_recognizer: DigitRecognizer,
) -> Path:
    capture = cv2.VideoCapture(str(input_path))
    if not capture.isOpened():
        raise ValueError(f"Khong the mo video: {input_path}")

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(capture.get(cv2.CAP_PROP_FPS)) or 25.0
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    output_path = output_dir / f"result_{input_path.stem}.mp4"
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"Khong the tao video: {output_path}")

    frame_count = 0
    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            frame_count += 1
            inference_frame = apply_preprocessing(
                frame,
                enable_preprocessing=True,
                preprocessing_config={
                    "enable_preprocessing": True,
                    "apply_resize": False,
                },
            )
            results = infer_traffic_sign(model, inference_frame)
            detections = parse_detections(
                frame=frame,
                results=results,
                model_names=model.names,
                mapping_fix=mapping_fix,
                digit_recognizer=digit_recognizer,
            )
            writer.write(draw_detections(frame, detections))

            if frame_count % 30 == 0:
                print(
                    f"Dang xu ly frame "
                    f"{frame_count}/{total_frames}"
                )
    finally:
        capture.release()
        writer.release()

    return output_path


def main() -> None:
    selected_file = choose_input_file()
    if not selected_file:
        print("Da huy chon file.")
        return

    base_dir = Path(__file__).resolve().parent
    model_path = (
        base_dir
        / "traffic_sign_runs_new"
        / "traffic_sign_52classes"
        / "weights"
        / "best.pt"
    )
    output_dir = (
        base_dir
        / "inference_outputs"
        / "prediction_results"
    )

    if not model_path.exists():
        print(f"Khong tim thay model: {model_path}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(model_path))
    digit_recognizer = DigitRecognizer(
        allowed_values=(40, 50, 60, 80),
        min_confidence=0.0,
    )

    # Khong ep cac bien 40/60 thanh 50 nua.
    mapping_fix = {
        "Cam re phai": "Cam quay dau",
    }

    input_path = Path(selected_file)
    is_video = input_path.suffix.lower() in {
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
    }

    if is_video:
        output_path = process_video(
            input_path,
            output_dir,
            model,
            mapping_fix,
            digit_recognizer,
        )
    else:
        output_path = process_image(
            input_path,
            output_dir,
            model,
            mapping_fix,
            digit_recognizer,
        )

    print(f"Da luu ket qua tai: {output_path}")


if __name__ == "__main__":
    main()
