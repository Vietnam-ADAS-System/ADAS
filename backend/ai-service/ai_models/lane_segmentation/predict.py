"""
YOLOv11 Lane Segmentation Inference Script
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path


class LaneSegmenter:
    """YOLOv11 Lane Segmentation model wrapper."""

    def __init__(self, weights_path: str, conf: float = 0.15, iou: float = 0.5):
        """
        Initialize lane segmenter.

        Args:
            weights_path: Path đến trained weights (.pt)
            conf: Confidence threshold (giảm xuống 0.15 để detect nhiều hơn)
            iou: IOU threshold for NMS
        """
        self.model = YOLO(weights_path)
        self.conf = conf
        self.iou = iou
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

        results = self.model.predict(
            image,
            conf=self.conf,
            iou=self.iou,
            imgsz=imgsz,
            verbose=False,
        )
        return results

    def get_lane_mask(self, image, imgsz: int = 640, class_id: int = 0) -> np.ndarray:
        """Trả về mask nhị phân của class chỉ định (mặc định class 0 = lane_line)."""
        return self.segment(image, imgsz, class_id=class_id)

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

        # Draw masks
        annotated = results[0].plot()

        return annotated


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
