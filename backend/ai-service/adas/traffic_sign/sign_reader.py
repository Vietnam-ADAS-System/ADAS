"""
TV1.1 - Sign Reader
Đọc kết quả detection từ YOLO
"""

from typing import List, Optional, Dict, Any
from models import DetectionResult, BoundingBox
from class_mapper import TrafficSignClassMapper


class SignReader:
    """
    Đọc raw detection result từ YOLO model
    Chuyển đổi sang DetectionResult model cho validation
    """
    
    def __init__(self):
        self.last_detection_results: List[DetectionResult] = []
    
    def read_raw_detection(self, raw_data: Dict[str, Any]) -> Optional[DetectionResult]:
        """
        Đọc một kết quả detection từ YOLO
        
        Args:
            raw_data: Raw detection data từ YOLO model
                Expected format:
                {
                    "class_id": 38,
                    "confidence": 0.96,
                    "bbox": [120, 80, 200, 180]
                }
        
        Returns:
            DetectionResult object hoặc None nếu invalid
        
        Raises:
            ValueError: Nếu dữ liệu không hợp lệ
        """
        try:
            # Validate class_id
            class_id = raw_data.get('class_id')
            if class_id is None:
                raise ValueError("Missing 'class_id' in detection result")
            
            if not TrafficSignClassMapper.validate_class_id(class_id):
                raise ValueError(f"Invalid class_id: {class_id}")
            
            # Create DetectionResult (Pydantic will validate)
            detection = DetectionResult(
                class_id=class_id,
                confidence=raw_data.get('confidence', 0),
                bbox=raw_data.get('bbox', [])
            )
            
            return detection
            
        except Exception as e:
            print(f"Error reading detection: {str(e)}")
            return None
    
    def read_batch_detections(self, batch_data: List[Dict[str, Any]]) -> List[DetectionResult]:
        """
        Đọc nhiều detection result cùng lúc
        
        Args:
            batch_data: List các raw detection data
        
        Returns:
            List DetectionResult objects (lọc bỏ invalid items)
        """
        results = []
        for raw_item in batch_data:
            detection = self.read_raw_detection(raw_item)
            if detection is not None:
                results.append(detection)
        
        self.last_detection_results = results
        return results
    
    def get_last_detections(self) -> List[DetectionResult]:
        """Lấy batch detection gần nhất"""
        return self.last_detection_results.copy()
    
    @staticmethod
    def parse_bbox_list(bbox: List[float]) -> Optional[Dict[str, float]]:
        """
        Parse bbox từ list [x1, y1, x2, y2] sang dict
        
        Args:
            bbox: List [x1, y1, x2, y2]
        
        Returns:
            Dict {x1, y1, x2, y2} hoặc None nếu invalid
        """
        if not isinstance(bbox, list) or len(bbox) != 4:
            return None
        
        try:
            return {
                'x1': float(bbox[0]),
                'y1': float(bbox[1]),
                'x2': float(bbox[2]),
                'y2': float(bbox[3])
            }
        except (ValueError, TypeError):
            return None
