"""
YOLOv11 Lane Segmentation Inference Script
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np
from ultralytics import YOLO

AI_SERVICE_ROOT = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_ROOT))

from preprocessing.image_processor import ImageProcessor


class LaneSegmenter:
    """YOLOv11 Lane Segmentation model wrapper."""

    def __init__(
        self,
        weights_path: str,
        conf: float = 0.15,
        iou: float = 0.5,
        enable_preprocessing: bool = True,
        preprocessing_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize lane segmenter.

        Args:
            weights_path: Path đến trained weights (.pt)
            conf: Confidence threshold (giảm xuống 0.15 để detect nhiều hơn)
            iou: IOU threshold for NMS
            enable_preprocessing: Bật/tắt preprocessing
            preprocessing_config: Cấu hình preprocessing theo module
        """
        self.model = YOLO(weights_path)
        self.conf = conf
        self.iou = iou
        self.enable_preprocessing = enable_preprocessing
        self.preprocessing_config = preprocessing_config or {}
        self.class_names = {0: "lane_line", 1: "road"}

    def predict(self, image, imgsz: int = 640, return_mask: bool = True):
        """
        Predict lane segmentation on image.

        Args:
            image: Input image (numpy array or path)
            imgsz: Inference image size
            return_mask: Return segmentation mask

        Returns:
            Results object from YOLO
        """
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))

        image = self._prepare_image(image)

        results = self.model.predict(
            image,
            conf=self.conf,
            iou=self.iou,
            imgsz=imgsz,
            verbose=False,
        )
        return results

    def _prepare_image(self, image):
        if image is None or image.size == 0 or not self.enable_preprocessing:
            return image

        processor = ImageProcessor(target_size=(image.shape[1], image.shape[0]))
        return processor.apply_module_preprocessing(
            image,
            module_name="lane_segmentation",
            config=self.preprocessing_config,
        )

    def get_lane_mask(self, image, imgsz: int = 640, class_id: int = 1) -> np.ndarray:
        """Trả về mask nhị phân của class chỉ định (mặc định class 1 = road)."""
        return self.segment(image, imgsz, class_id=class_id)

    def get_all_class_masks(self, image, imgsz: int = 640) -> Dict[str, np.ndarray]:
        """
        Trả về dict mask nhị phân cho từng class.

        Returns:
            Dict với key là tên class ('lane_line', 'road') và value là mask uint8 (0/255).
        """
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))

        results = self.predict(image, imgsz=imgsz)
        h, w = image.shape[:2]

        output_masks: Dict[str, np.ndarray] = {
            name: np.zeros((h, w), dtype=np.uint8) for name in self.class_names.values()
        }

        if len(results) > 0 and results[0].masks is not None:
            masks = results[0].masks.data.cpu().numpy()

            if results[0].boxes is not None and len(results[0].boxes) > 0:
                classes = results[0].boxes.cls.cpu().numpy().astype(int)
                for mask, cls in zip(masks, classes):
                    cls_name = self.class_names.get(int(cls))
                    if cls_name is None:
                        continue
                    resized = cv2.resize(mask, (w, h))
                    binary = (resized * 255).astype(np.uint8)
                    output_masks[cls_name] = np.maximum(output_masks[cls_name], binary)

        return output_masks

    def segment(self, image, imgsz: int = 640, class_id: int = 0):
        """Get segmentation mask only."""
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))

        results = self.predict(image, imgsz=imgsz)

        h, w = image.shape[:2]
        lane_mask = np.zeros((h, w), dtype=np.uint8)

        if len(results) > 0 and results[0].masks is not None:
            masks = results[0].masks.data.cpu().numpy()

            # Kiểm tra nếu có boxes để lấy class
            if results[0].boxes is not None and len(results[0].boxes) > 0:
                classes = results[0].boxes.cls.cpu().numpy()
                for i, (mask, cls) in enumerate(zip(masks, classes)):
                    if int(cls) == class_id:
                        resized_mask = cv2.resize(mask, (w, h))
                        lane_mask = np.maximum(lane_mask, (resized_mask * 255).astype(np.uint8))
            else:
                # Nếu không có class info, lấy mask đầu tiên hoặc mask lớn nhất
                for mask in masks:
                    resized_mask = cv2.resize(mask, (w, h))
                    lane_mask = np.maximum(lane_mask, (resized_mask * 255).astype(np.uint8))

        return lane_mask

    def visualize(self, image, alpha: float = 0.5):
        """
        Visualize segmentation on image.

        Args:
            image: Input image
            alpha: Overlay transparency

        Returns:
            Image with segmentation overlay
        """
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))

        results = self.predict(image)

        return self._overlay_masks(image, results[0])

    def _overlay_masks(self, image: np.ndarray, result) -> np.ndarray:
        """Overlay segmentation masks with custom colors per class.

        class 0 = lane_line  -> light red
        class 1 = road       -> hidden (no overlay, only the lane is drawn)
        """
        if result.masks is None or result.boxes is None or len(result.boxes) == 0:
            return image

        overlay = image.copy()
        h, w = image.shape[:2]
        masks = result.masks.data.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)

        # BGR color (OpenCV uses BGR, not RGB)
        lane_color_bgr = (120, 120, 255)  # light red in BGR
        road_color_bgr = None  # road is hidden per user request

        for mask, cls in zip(masks, classes):
            color = lane_color_bgr if int(cls) == 0 else road_color_bgr
            if color is None:
                continue  # skip this class (e.g. road hidden)

            resized = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
            color_layer = np.zeros_like(image, dtype=np.uint8)
            color_layer[resized > 0] = color
            overlay = cv2.addWeighted(overlay, 1.0, color_layer, 0.45, 0)

        return cv2.addWeighted(image, 1.0 - 0.45, overlay, 0.45, 0)


def predict_from_video(video_path: str, weights_path: str, output_path: str = None):
    """
    Process video with lane segmentation.

    Args:
        video_path: Path đến input video
        weights_path: Path đến trained weights
        output_path: Path đến output video (optional)
    """
    segmenter = LaneSegmenter(weights_path)

    cap = cv2.VideoCapture(video_path)

    # Video writer
    if output_path:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Predict
        result = segmenter.visualize(frame)

        if output_path:
            out.write(result)

        # Display
        cv2.imshow("Lane Segmentation", result)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    if output_path:
        out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YOLOv11 Lane Segmentation Inference")
    parser.add_argument("--weights", type=str, required=True, help="Path to trained weights")
    parser.add_argument("--source", type=str, required=True, help="Image/Video/Directory path")
    parser.add_argument("--output", type=str, default=None, help="Output path")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.5, help="IOU threshold")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")

    args = parser.parse_args()

    segmenter = LaneSegmenter(args.weights, conf=args.conf, iou=args.iou)

    source = Path(args.source)
    if source.is_file():
        if source.suffix.lower() in [".mp4", ".avi", ".mov"]:
            predict_from_video(str(source), args.weights, args.output)
        else:
            # Single image
            img = cv2.imread(str(source))
            result = segmenter.visualize(img)
            if args.output:
                cv2.imwrite(args.output, result)
            else:
                cv2.imshow("Result", result)
                cv2.waitKey(0)
    else:
        print("Directory prediction not implemented yet")
