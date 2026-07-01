import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune YOLO for car, motorcycle and pedestrian detection."
    )
    parser.add_argument(
        "--data",
        default=str(Path(__file__).with_name("vehicle_detection.yaml")),
        help="YOLO dataset yaml.",
    )
    parser.add_argument(
        "--model",
        default="yolo26x.pt",
        help="Base model or checkpoint. Use yolo11x.pt if YOLO11 is required.",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="0")
    parser.add_argument("--project", default="runs/vehicle_detection")
    parser.add_argument("--name", default="yolo_vehicle")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        patience=20,
        pretrained=True,
        cache=True,
        cos_lr=True,
        close_mosaic=10,
    )


if __name__ == "__main__":
    main()
