"""
TV1.0 - Sign Input Service
Điều phối toàn bộ TV1 - Traffic Sign Recognition Input
Nhận detection result từ YOLO và sinh StandardTrafficSignData
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from models import StandardTrafficSignData, DetectionResult
from sign_reader import SignReader
from confidence_filter import ConfidenceFilter
from class_mapper import TrafficSignClassMapper
from bbox_parser import BboxParser


class SignInputService:
    """
    TV1 Service - Điều phối toàn bộ luồng Traffic Sign Recognition Input
    
    Pipeline:
    1. Nhận raw detection result từ YOLO
    2. Đọc class_id, confidence, bbox
    3. Lọc theo confidence threshold
    4. Mapping class_id -> class_name
    5. Parse bbox
    6. Sinh StandardTrafficSignData
    """
    
    def __init__(self, confidence_threshold: Optional[float] = None):
        self.sign_reader = SignReader()
        self.confidence_filter = ConfidenceFilter(confidence_threshold)
        self.bbox_parser = BboxParser()
        self.processed_detections: List[StandardTrafficSignData] = []
    
    def process_detection(
        self,
        raw_detection: Dict[str, Any],
        frame_id: int,
        tracking_id: int
    ) -> Optional[StandardTrafficSignData]:
        """
        Xử lý một detection result
        
        Args:
            raw_detection: Raw detection từ YOLO
                {
                    "class_id": 38,
                    "confidence": 0.95,
                    "bbox": [150, 80, 240, 190]
                }
            frame_id: ID của frame hiện tại
            tracking_id: ID của tracking object
        
        Returns:
            StandardTrafficSignData hoặc None nếu lọc bỏ
        
        Raises:
            ValueError: Nếu dữ liệu không hợp lệ
        """
        # Step 1: Đọc detection result
        detection = self.sign_reader.read_raw_detection(raw_detection)
        if detection is None:
            return None
        
        # Step 2: Lọc confidence
        if not self.confidence_filter.filter_detection(detection):
            return None
        
        # Step 3: Mapping class_id -> class_name
        try:
            class_name = TrafficSignClassMapper.get_class_name(detection.class_id)
        except ValueError as e:
            print(f"Error mapping class: {str(e)}")
            return None
        
        # Step 4: Parse bbox
        bbox = self.bbox_parser.parse_detection_bbox(detection)
        if bbox is None:
            return None
        
        # Step 5: Sinh StandardTrafficSignData
        standard_data = StandardTrafficSignData(
            frame_id=frame_id,
            tracking_id=tracking_id,
            class_id=detection.class_id,
            class_name=class_name,
            confidence=detection.confidence,
            bbox=bbox,
            timestamp=datetime.now()
        )
        
        self.processed_detections.append(standard_data)
        return standard_data
    
    def process_batch_detections(
        self,
        raw_detections: List[Dict[str, Any]],
        frame_id: int,
        tracking_ids: Optional[List[int]] = None
    ) -> List[StandardTrafficSignData]:
        """
        Xử lý batch detection results
        
        Args:
            raw_detections: List raw detections từ YOLO
            frame_id: ID của frame
            tracking_ids: List tracking IDs tương ứng
                         Nếu None, sử dụng range(len(detections))
        
        Returns:
            List StandardTrafficSignData (có thể rỗng nếu tất cả bị lọc)
        """
        if tracking_ids is None:
            tracking_ids = list(range(len(raw_detections)))
        
        results = []
        for detection, tracking_id in zip(raw_detections, tracking_ids):
            standard_data = self.process_detection(detection, frame_id, tracking_id)
            if standard_data is not None:
                results.append(standard_data)
        
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê xử lý
        
        Returns:
            Dict với statistics
        """
        return {
            'total_processed': len(self.processed_detections),
            'confidence_threshold': self.confidence_filter.get_threshold(),
            'last_10_detections': [
                {
                    'frame_id': d.frame_id,
                    'class_id': d.class_id,
                    'class_name': d.class_name,
                    'confidence': d.confidence,
                    'timestamp': d.timestamp.isoformat()
                }
                for d in self.processed_detections[-10:]
            ]
        }
    
    def reset_history(self):
        """Reset lịch sử xử lý"""
        self.processed_detections.clear()
