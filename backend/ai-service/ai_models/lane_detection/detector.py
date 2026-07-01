"""
YOLOv11 Lane Detection Inference Script
Detection model cho phát hiện các loại vạch kẻ đường
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path


class LaneDetector:
    """YOLOv11 Lane Detection model wrapper."""

    CLASS_NAMES = {
        0: 'broken_and_solid_lines_white_lane',
        1: 'broken_and_solid_lines_yellow_lane',
        2: 'broken_line_white_lane',
        3: 'broken_line_yellow_lane',
        4: 'double_solid_line_white_lane',
        5: 'double_solid_line_yellow_lane',
        6: 'left_turn',
        7: 'right_turn',
        8: 'solid_line_white_lane',
        9: 'solid_line_yellow_lane',
        10: 'straight_way'
    }

    # Màu cho mỗi class - phân biệt rõ từng loại lane
    CLASS_COLORS = {
        0: (255, 255, 0),    # Vàng - broken_and_solid white
        1: (0, 255, 255),    # Cyan - broken_and_solid yellow
        2: (255, 0, 255),    # Tím - broken white
        3: (0, 255, 0),      # Xanh lá - broken yellow
        4: (255, 128, 0),    # Cam - double solid white
        5: (0, 0, 255),      # Đỏ - double solid yellow
        6: (128, 0, 255),    # Tím đậm - left turn
        7: (255, 0, 128),    # Hồng đậm - right turn
        8: (255, 255, 255),  # Trắng - solid white
        9: (0, 128, 255),    # Xanh dương đậm - solid yellow
        10: (128, 255, 0),   # Xanh vàng - straight way
    }

    def __init__(self, weights_path: str, conf: float = 0.25, iou: float = 0.5):
        """
        Initialize lane detector.

        Args:
            weights_path: Path đến trained weights (.pt)
            conf: Confidence threshold
            iou: IOU threshold for NMS
        """
        self.model = YOLO(weights_path)
        self.conf = conf
        self.iou = iou

    def predict(self, image, imgsz: int = 640):
        """
        Predict lane detection on image.

        Args:
            image: Input image (numpy array or path)
            imgsz: Inference image size

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

    def get_detections(self, image, imgsz: int = 640) -> list:
        """
        Get list of detections with bounding boxes and classes.

        Returns:
            List of dicts with keys: class_id, class_name, conf, bbox
        """
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))

        results = self.predict(image, imgsz=imgsz)

        detections = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                detections.append({
                    'class_id': int(boxes.cls[i].item()),
                    'class_name': self.CLASS_NAMES.get(int(boxes.cls[i].item()), 'unknown'),
                    'conf': float(boxes.conf[i].item()),
                    'bbox': boxes.xyxy[i].cpu().numpy().tolist()
                })

        return detections

    def visualize(self, image, show_labels: bool = True, show_conf: bool = True):
        """
        Visualize detection on image.

        Args:
            image: Input image
            show_labels: Show class names
            show_conf: Show confidence scores

        Returns:
            Image with detection boxes
        """
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))

        results = self.predict(image)

        # Draw custom boxes with better visibility
        annotated = image.copy()
        h, w = image.shape[:2]

        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                conf = float(boxes.conf[i].item())
                x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()

                color = self.CLASS_COLORS.get(cls_id, (255, 255, 255))

                # Draw box
                cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

                # Create label
                label = self.CLASS_NAMES.get(cls_id, 'unknown')
                if show_conf:
                    label += f" {conf:.2f}"

                # Draw label background
                (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10), (int(x1) + label_w, int(y1)), color, -1)

                # Draw label text
                cv2.putText(annotated, label, (int(x1), int(y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        return annotated

    def get_lane_lines(self, image, imgsz: int = 640) -> dict:
        """
        Get lane lines grouped by type.

        Returns:
            Dict với keys: white_lines, yellow_lines, turns, others
        """
        detections = self.get_detections(image, imgsz)

        result = {
            'white_lines': [],
            'yellow_lines': [],
            'turns': [],
            'others': []
        }

        for det in detections:
            name = det['class_name'].lower()

            if 'white' in name:
                result['white_lines'].append(det)
            elif 'yellow' in name:
                result['yellow_lines'].append(det)
            elif 'turn' in name:
                result['turns'].append(det)
            else:
                result['others'].append(det)

        return result


def detect_from_video(video_path: str, weights_path: str, output_path: str = None):
    """
    Process video with lane detection.

    Args:
        video_path: Path đến input video
        weights_path: Path đến trained weights
        output_path: Path đến output video (optional)
    """
    detector = LaneDetector(weights_path)

    cap = cv2.VideoCapture(video_path)

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

        result = detector.visualize(frame)

        if output_path:
            out.write(result)

        cv2.imshow("Lane Detection", result)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    if output_path:
        out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YOLOv11 Lane Detection Inference")
    parser.add_argument("--weights", type=str, required=True, help="Path to trained weights")
    parser.add_argument("--source", type=str, required=True, help="Image/Video/Directory path")
    parser.add_argument("--output", type=str, default=None, help="Output path")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.5, help="IOU threshold")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")

    args = parser.parse_args()

    detector = LaneDetector(args.weights, conf=args.conf, iou=args.iou)

    source = Path(args.source)
    if source.is_file():
        if source.suffix.lower() in [".mp4", ".avi", ".mov"]:
            detect_from_video(str(source), args.weights, args.output)
        else:
            img = cv2.imread(str(source))
            result = detector.visualize(img)
            if args.output:
                cv2.imwrite(args.output, result)
            else:
                cv2.imshow("Result", result)
                cv2.waitKey(0)
    else:
        print("Directory prediction not implemented yet")
