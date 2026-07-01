import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2


CLASS_MAP = {
    "pedestrian": 0,
    "person": 0,
    "car": 1,
    "motor": 2,
    "motorcycle": 2,
    "motorbike": 2,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert BDD100K detection labels to YOLO format for car, motorcycle and pedestrian only."
    )
    parser.add_argument(
        "--bdd-root",
        required=True,
        help="BDD100K root folder containing images/100k and labels/det_20.",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[4] / "datasets" / "vehicle_detection"),
        help="Output YOLO dataset folder.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val"],
        choices=["train", "val"],
        help="BDD100K splits to convert.",
    )
    parser.add_argument(
        "--copy-images",
        action="store_true",
        help="Copy images into the YOLO dataset. Without this flag only labels are written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bdd_root = Path(args.bdd_root)
    output_root = Path(args.output)

    for split in args.splits:
        labels_path = _find_labels_file(bdd_root, split)
        image_root = bdd_root / "images" / "100k" / split
        if not labels_path.exists():
            raise FileNotFoundError(f"Missing labels file: {labels_path}")
        if not image_root.exists():
            raise FileNotFoundError(f"Missing image folder: {image_root}")

        converted, skipped = convert_split(
            labels_path=labels_path,
            image_root=image_root,
            output_root=output_root,
            split=split,
            copy_images=args.copy_images,
        )
        print(f"{split}: wrote {converted} labels, skipped {skipped} objects outside target classes")


def convert_split(
    labels_path: Path,
    image_root: Path,
    output_root: Path,
    split: str,
    copy_images: bool,
) -> Tuple[int, int]:
    image_out = output_root / "images" / split
    label_out = output_root / "labels" / split
    image_out.mkdir(parents=True, exist_ok=True)
    label_out.mkdir(parents=True, exist_ok=True)

    records = json.loads(labels_path.read_text(encoding="utf-8"))
    converted = 0
    skipped = 0

    for record in records:
        image_name = record.get("name")
        if not image_name:
            continue

        image_path = image_root / image_name
        width, height = _image_size(image_path)
        yolo_rows = []

        for label in record.get("labels", []):
            class_id = CLASS_MAP.get(str(label.get("category", "")).lower())
            box = label.get("box2d")
            if class_id is None or not box:
                skipped += 1
                continue

            yolo_box = _box_to_yolo(box, width, height)
            if yolo_box is None:
                skipped += 1
                continue

            x_center, y_center, box_width, box_height = yolo_box
            yolo_rows.append(
                f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"
            )

        if yolo_rows:
            (label_out / f"{Path(image_name).stem}.txt").write_text(
                "\n".join(yolo_rows) + "\n",
                encoding="utf-8",
            )
            converted += len(yolo_rows)

            if copy_images:
                shutil.copy2(image_path, image_out / image_name)

    return converted, skipped


def _find_labels_file(bdd_root: Path, split: str) -> Path:
    candidates = [
        bdd_root / "labels" / "det_20" / f"det_{split}.json",
        bdd_root / "labels" / f"bdd100k_labels_images_det_{split}.json",
        bdd_root / f"det_{split}.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _image_size(image_path: Path) -> Tuple[int, int]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    height, width = image.shape[:2]
    return width, height


def _box_to_yolo(box: Dict, width: int, height: int) -> Optional[Tuple[float, float, float, float]]:
    x1 = _clip(float(box["x1"]), 0, width)
    y1 = _clip(float(box["y1"]), 0, height)
    x2 = _clip(float(box["x2"]), 0, width)
    y2 = _clip(float(box["y2"]), 0, height)

    box_width = x2 - x1
    box_height = y2 - y1
    if box_width <= 1 or box_height <= 1:
        return None

    return (
        ((x1 + x2) / 2) / width,
        ((y1 + y2) / 2) / height,
        box_width / width,
        box_height / height,
    )


def _clip(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


if __name__ == "__main__":
    main()
