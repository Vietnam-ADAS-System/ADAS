"""
TV1.5 - Bbox Parser
Parse và chuẩn hóa bounding box
"""

from typing import List, Tuple, Optional
from models import DetectionResult, BoundingBox


class BboxParser:
    """
    Parse và chuẩn hóa bounding box từ detection result
    Hỗ trợ nhiều định dạng khác nhau
    """
    
    @staticmethod
    def parse_bbox_list_to_object(bbox_list: List[float]) -> Optional[BoundingBox]:
        """
        Convert list [x1, y1, x2, y2] thành BoundingBox object
        
        Args:
            bbox_list: [x1, y1, x2, y2]
        
        Returns:
            BoundingBox object hoặc None nếu invalid
        """
        if not isinstance(bbox_list, list) or len(bbox_list) != 4:
            return None
        
        try:
            x1, y1, x2, y2 = map(float, bbox_list)
            
            # Validate: x1 < x2, y1 < y2
            if x1 >= x2 or y1 >= y2:
                print(f"Invalid bbox: x1={x1} >= x2={x2} or y1={y1} >= y2={y2}")
                return None
            
            return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def parse_detection_bbox(detection: DetectionResult) -> Optional[BoundingBox]:
        """
        Extract và parse bbox từ DetectionResult
        
        Args:
            detection: DetectionResult object
        
        Returns:
            BoundingBox object
        """
        return BboxParser.parse_bbox_list_to_object(detection.bbox)
    
    @staticmethod
    def get_bbox_center(bbox: BoundingBox) -> Tuple[float, float]:
        """
        Tính tọa độ tâm của bounding box
        
        Args:
            bbox: BoundingBox object
        
        Returns:
            (center_x, center_y)
        """
        center_x = (bbox.x1 + bbox.x2) / 2
        center_y = (bbox.y1 + bbox.y2) / 2
        return center_x, center_y
    
    @staticmethod
    def get_bbox_dimensions(bbox: BoundingBox) -> Tuple[float, float]:
        """
        Tính kích thước của bounding box
        
        Args:
            bbox: BoundingBox object
        
        Returns:
            (width, height)
        """
        width = bbox.x2 - bbox.x1
        height = bbox.y2 - bbox.y1
        return width, height
    
    @staticmethod
    def get_bbox_area(bbox: BoundingBox) -> float:
        """
        Tính diện tích của bounding box
        
        Args:
            bbox: BoundingBox object
        
        Returns:
            Diện tích (width * height)
        """
        width, height = BboxParser.get_bbox_dimensions(bbox)
        return width * height
    
    @staticmethod
    def validate_bbox(bbox: BoundingBox, frame_width: int, frame_height: int) -> bool:
        """
        Kiểm tra bbox có nằm trong frame không
        
        Args:
            bbox: BoundingBox object
            frame_width: Chiều rộng frame
            frame_height: Chiều cao frame
        
        Returns:
            True nếu bbox hợp lệ, False nếu không
        """
        if bbox.x1 < 0 or bbox.y1 < 0:
            return False
        if bbox.x2 > frame_width or bbox.y2 > frame_height:
            return False
        return True
    
    @staticmethod
    def clip_bbox(bbox: BoundingBox, frame_width: int, frame_height: int) -> BoundingBox:
        """
        Cắt bbox để nằm trong frame
        
        Args:
            bbox: BoundingBox object
            frame_width: Chiều rộng frame
            frame_height: Chiều cao frame
        
        Returns:
            Clipped BoundingBox
        """
        x1 = max(0, min(bbox.x1, frame_width))
        y1 = max(0, min(bbox.y1, frame_height))
        x2 = max(0, min(bbox.x2, frame_width))
        y2 = max(0, min(bbox.y2, frame_height))
        
        return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
    
    @staticmethod
    def bbox_to_list(bbox: BoundingBox) -> List[float]:
        """Convert BoundingBox object thành list"""
        return [bbox.x1, bbox.y1, bbox.x2, bbox.y2]
    
    @staticmethod
    def bbox_to_dict(bbox: BoundingBox) -> dict:
        """Convert BoundingBox object thành dict"""
        return {
            'x1': bbox.x1,
            'y1': bbox.y1,
            'x2': bbox.x2,
            'y2': bbox.y2
        }
