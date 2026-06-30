"""
Convert VIA Lane Segmentation Dataset to YOLO Segmentation Format

VIA Dataset format:
- Segmentation_Dataset.zip contains:
    - train_frames/train/train_XXXXXX.png
    - train_masks/train/train_XXXXXX.png
    - val_frames/val/val_XXXXXX.png
    - val_masks/val/val_XXXXXX.png

YOLO Segmentation format:
- images/train/ and images/val/
- labels/train/ and labels/val/
- Each label is a .txt file with polygon coordinates
"""

import os
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
import shutil


class VIAToYOLOConverter:
    """Convert VIA Lane Segmentation Dataset to YOLO format."""

    # Class mapping: VIA uses RGB colors, we map to YOLO class IDs
    # VIA label_colors.txt:
    # 0: (0, 0, 0) - Background (black)
    # 1: (128, 0, 0) - Road (dark red)
    # 2: (255, 255, 255) - Lane line (white)
    COLOR_TO_CLASS = {
        (0, 0, 0): 0,       # Background (ignored in YOLO)
        (128, 0, 0): 1,     # Road
        (255, 255, 255): 0, # Lane line
    }

    def __init__(self, via_dataset_path: str, output_path: str):
        """
        Initialize converter.

        Args:
            via_dataset_path: Path to extracted VIA dataset
            output_path: Output directory for YOLO format
        """
        self.via_path = Path(via_dataset_path)
        self.output_path = Path(output_path)

    def create_directory_structure(self):
        """Create YOLO directory structure."""
        dirs = [
            self.output_path / "images" / "train",
            self.output_path / "images" / "val",
            self.output_path / "labels" / "train",
            self.output_path / "labels" / "val",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        return dirs

    def mask_to_polygons(self, mask: np.ndarray, class_id: int = 0):
        """
        Convert binary mask to polygon coordinates.

        Args:
            mask: Binary mask (H, W)
            class_id: Class ID for this mask

        Returns:
            List of polygons, each polygon is a list of [x1, y1, x2, y2, ...]
        """
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        polygons = []
        for contour in contours:
            if len(contour) < 3:
                continue

            # Simplify contour
            epsilon = 0.005 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) < 3:
                continue

            # Flatten to (N, 2) and convert to normalized coordinates
            polygon = approx.reshape(-1, 2)
            polygons.append((class_id, polygon))

        return polygons

    def mask_to_yolo_segmentation(self, mask: np.ndarray, road_only: bool = True):
        """
        Convert colored mask to YOLO segmentation format.

        Args:
            mask: RGB mask image (H, W, 3)
            road_only: If True, only process road class

        Returns:
            List of YOLO format polygons
        """
        h, w = mask.shape[:2]
        polygons = []

        # Unique colors in mask
        unique_colors = np.unique(mask.reshape(-1, 3), axis=0)

        for color in unique_colors:
            color_tuple = tuple(color.astype(int))
            if color_tuple not in self.COLOR_TO_CLASS:
                continue

            class_id = self.COLOR_TO_CLASS[color_tuple]

            # Create binary mask for this color
            binary_mask = np.all(mask == color, axis=2).astype(np.uint8) * 255

            # Get polygons
            polys = self.mask_to_polygons(binary_mask, class_id)
            polygons.extend(polys)

        return polygons

    def save_yolo_label(self, polygons, img_shape, output_file: Path):
        """
        Save polygons in YOLO segmentation format.

        Args:
            polygons: List of (class_id, polygon_points)
            img_shape: Image shape (H, W, C)
            output_file: Output .txt file path
        """
        h, w = img_shape[:2]

        with open(output_file, "w") as f:
            for class_id, points in polygons:
                # Normalize coordinates
                normalized = []
                for x, y in points:
                    normalized.extend([x / w, y / h])

                line = f"{class_id} " + " ".join([f"{p:.6f}" for p in normalized])
                f.write(line + "\n")

    def convert_split(self, split: str = "train"):
        """
        Convert a dataset split to YOLO format.

        Args:
            split: 'train' or 'val'
        """
        frames_dir = self.via_path / f"{split}_frames" / split
        masks_dir = self.via_path / f"{split}_masks" / split

        if not frames_dir.exists() or not masks_dir.exists():
            print(f"Split '{split}' not found, skipping...")
            return 0

        images_out = self.output_path / "images" / split
        labels_out = self.output_path / "labels" / split

        count = 0
        for img_file in tqdm(list(frames_dir.glob("*.png")), desc=f"Converting {split}"):
            # Read image and mask
            img = cv2.imread(str(img_file))
            mask_file = masks_dir / img_file.name
            mask = cv2.imread(str(mask_file))

            if img is None or mask is None:
                print(f"Skipping {img_file.name} - could not read")
                continue

            # Convert mask to YOLO format
            polygons = self.mask_to_yolo_segmentation(mask)

            # Save image
            output_img = images_out / f"{img_file.stem}.jpg"
            cv2.imwrite(str(output_img), img)

            # Save label
            output_label = labels_out / f"{img_file.stem}.txt"
            self.save_yolo_label(polygons, img.shape, output_label)

            count += 1

        print(f"Converted {count} images for {split}")
        return count

    def convert(self):
        """Convert entire dataset."""
        print("Creating directory structure...")
        self.create_directory_structure()

        print("Converting dataset...")
        train_count = self.convert_split("train")
        val_count = self.convert_split("val")

        # Create dataset YAML
        yaml_content = f"""# VIA Lane Segmentation Dataset - YOLO Format

path: {self.output_path.absolute()}
train: images/train
val: images/val

# Classes
names:
  0: lane_line
  1: road

nc: 2
"""
        yaml_path = self.output_path / "dataset.yaml"
        with open(yaml_path, "w") as f:
            f.write(yaml_content)

        print(f"\nConversion complete!")
        print(f"  Train: {train_count} images")
        print(f"  Val: {val_count} images")
        print(f"  Output: {self.output_path.absolute()}")
        print(f"  Config: {yaml_path}")

        return {"train": train_count, "val": val_count}


def download_via_dataset(output_dir: str):
    """
    Download VIA Lane Segmentation Dataset.
    Kaggle competition: https://www.kaggle.com/competitions/ai-challenge-2024
    """
    print("To download VIA Dataset:")
    print("1. Go to: https://github.com/makerhanoi/via-dataset/releases/tag/v1.0")
    print("2. Download Segmentation_Dataset.zip")
    print("3. Extract to:", output_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert VIA Dataset to YOLO Format")
    parser.add_argument(
        "--via-path",
        type=str,
        required=True,
        help="Path to extracted VIA dataset",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="datasets/via_lane_seg_yolo",
        help="Output directory for YOLO format",
    )

    args = parser.parse_args()

    converter = VIAToYOLOConverter(args.via_path, args.output)
    converter.convert()
