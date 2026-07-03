"""
TV1.4 - Confidence Filter
Lọc detection result dựa trên confidence threshold
"""

from typing import List, Optional
from models import DetectionResult
from config import get_config


class ConfidenceFilter:
    """
    Lọc detection result dựa trên ngưỡng độ tin cậy
    Chỉ chấp nhận detection có confidence >= threshold
    """
    
    def __init__(self, threshold: Optional[float] = None):
        """
        Khởi tạo ConfidenceFilter
        
        Args:
            threshold: Ngưỡng độ tin cậy (0-1)
                      Nếu None, dùng giá trị từ config
        """
        if threshold is None:
            config = get_config()
            self.threshold = config.tv1_confidence_threshold
        else:
            self.threshold = threshold
        
        if not 0 <= self.threshold <= 1:
            raise ValueError("Threshold phải nằm trong khoảng 0-1")
    
    def filter_detection(self, detection: DetectionResult) -> bool:
        """
        Kiểm tra xem detection có pass filter không
        
        Args:
            detection: DetectionResult object
        
        Returns:
            True nếu confidence >= threshold, False nếu không
        """
        return detection.confidence >= self.threshold
    
    def filter_batch(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        Lọc batch detection
        
        Args:
            detections: List DetectionResult objects
        
        Returns:
            List các detection đã lọc (giữ lại những có confidence >= threshold)
        """
        filtered = [d for d in detections if self.filter_detection(d)]
        return filtered
    
    def get_confidence_stats(self, detections: List[DetectionResult]) -> dict:
        """
        Lấy thống kê về confidence
        
        Args:
            detections: List DetectionResult objects
        
        Returns:
            Dict với min, max, avg confidence
        """
        if not detections:
            return {'min': 0, 'max': 0, 'avg': 0, 'count': 0}
        
        confidences = [d.confidence for d in detections]
        return {
            'min': min(confidences),
            'max': max(confidences),
            'avg': sum(confidences) / len(confidences),
            'count': len(confidences),
            'threshold': self.threshold,
            'passed': sum(1 for d in detections if self.filter_detection(d))
        }
    
    def set_threshold(self, threshold: float):
        """Đặt ngưỡng mới"""
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold phải nằm trong khoảng 0-1")
        self.threshold = threshold
    
    def get_threshold(self) -> float:
        """Lấy ngưỡng hiện tại"""
        return self.threshold
