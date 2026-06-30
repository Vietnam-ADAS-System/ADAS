"""
YOLOv11 Lane Segmentation Training Script
Train trên local hoặc Kaggle
"""

from ultralytics import YOLO
import os
from pathlib import Path


def train_lane_segmentation(
    data_yaml: str = None,
    model_name: str = "yolo11n-seg.pt",
    epochs: int = 100,
    batch: int = 8,
    imgsz: int = 640,
    device: str = "0",
    project: str = "lane_detection",
    name: str = "yolo11_seg",
    resume: bool = False,
    pretrained_path: str = None,
):
    """
    Train YOLOv11 segmentation model cho lane detection.

    Args:
        data_yaml: Path to dataset config YAML
        model_name: Tên model pretrained (yolo11n-seg.pt, yolo11s-seg.pt, etc.)
        epochs: Số epochs train
        batch: Batch size
        imgsz: Image size
        device: Device ('0' for GPU, 'mps' for Apple Silicon, 'cpu')
        project: Tên project
        name: Tên experiment
        resume: Tiếp tục training từ checkpoint
        pretrained_path: Path đến pretrained weights
    """
    # Load model
    if pretrained_path and os.path.exists(pretrained_path):
        print(f"Loading model from: {pretrained_path}")
        model = YOLO(pretrained_path)
    else:
        print(f"Loading pretrained model: {model_name}")
        model = YOLO(model_name)

    # Dataset config
    if data_yaml is None:
        data_yaml = Path(__file__).parent / "lane_yolo.yaml"

    # Training results
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=project,
        name=name,
        resume=resume,
        # Augmentation
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=5.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        # Optimizer
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        # Save & Early stopping
        save=True,
        save_period=10,
        patience=30,
        verbose=True,
        # Other
        pretrained=True,
        workers=4,
        close_mosaic=10,
    )

    return results


def export_model(weights_path: str, format: str = "onnx"):
    """
    Export trained model sang format khác.

    Args:
        weights_path: Path đến trained weights
        format: Export format ('onnx', 'torchscript', 'openvino', etc.)
    """
    model = YOLO(weights_path)
    export_path = model.export(format=format)
    print(f"Model exported to: {export_path}")
    return export_path


def validate_model(weights_path: str, data_yaml: str):
    """
    Validate trained model.

    Args:
        weights_path: Path đến trained weights
        data_yaml: Path đến dataset config
    """
    model = YOLO(weights_path)
    metrics = model.val(data=data_yaml)
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    print(f"Seg mAP50: {metrics.seg.map50:.4f}")
    print(f"Seg mAP50-95: {metrics.seg.map:.4f}")
    return metrics


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train YOLOv11 Lane Segmentation")
    parser.add_argument("--data", type=str, help="Path to dataset YAML")
    parser.add_argument("--model", type=str, default="yolo11n-seg.pt", help="Model name")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--batch", type=int, default=8, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--device", type=str, default="0", help="Device")
    parser.add_argument("--project", type=str, default="lane_detection", help="Project name")
    parser.add_argument("--name", type=str, default="yolo11_seg", help="Experiment name")
    parser.add_argument("--resume", action="store_true", help="Resume training")

    args = parser.parse_args()

    train_lane_segmentation(
        data_yaml=args.data,
        model_name=args.model,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        project=args.project,
        name=args.name,
        resume=args.resume,
    )
