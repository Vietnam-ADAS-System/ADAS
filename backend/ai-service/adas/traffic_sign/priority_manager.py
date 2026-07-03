"""
TV4.2 - Priority Manager
Xếp mức ưu tiên cho cảnh báo
"""

from typing import Dict, List, Optional
from enum import Enum
from models import PriorityLevel, TrafficWarning
from config import get_config


class PriorityManager:
    """
    Quản lý mức ưu tiên cảnh báo
    
    Priority levels:
    - CRITICAL (95-100): Nguy hiểm cực cao
    - HIGH (70-94): Nguy hiểm cao
    - MEDIUM (40-69): Nguy hiểm trung bình
    - LOW (1-39): Nguy hiểm thấp
    """
    
    PRIORITY_RANGES = {
        PriorityLevel.CRITICAL: (95, 100),
        PriorityLevel.HIGH: (70, 94),
        PriorityLevel.MEDIUM: (40, 69),
        PriorityLevel.LOW: (1, 39),
    }
    
    def __init__(self):
        config = get_config()
        self.priority_rules = config.tv4_warning_priority_rules
    
    def get_priority_for_warning_type(self, warning_type: str) -> Dict[str, any]:
        """
        Lấy priority settings cho một loại warning
        
        Args:
            warning_type: Loại warning (NO_ENTRY, STOP, ...)
        
        Returns:
            Dict với level, priority, duration
            {
                'level': 'HIGH',
                'priority': 90,
                'duration': 5
            }
        """
        if warning_type not in self.priority_rules:
            # Default priority nếu không tìm thấy
            return {
                'level': 'LOW',
                'priority': 30,
                'duration': 5
            }
        
        return self.priority_rules[warning_type].copy()
    
    def assign_priority(
        self,
        warning_type: str,
        base_priority: Optional[int] = None
    ) -> int:
        """
        Gán priority number cho warning
        
        Args:
            warning_type: Loại warning
            base_priority: Base priority (nếu None, dùng từ config)
        
        Returns:
            Priority number (1-100)
        """
        if base_priority is not None:
            return max(1, min(100, base_priority))
        
        settings = self.get_priority_for_warning_type(warning_type)
        return settings['priority']
    
    def assign_level(self, priority_value: int) -> PriorityLevel:
        """
        Gán priority level dựa trên priority value
        
        Args:
            priority_value: Priority number (1-100)
        
        Returns:
            PriorityLevel
        """
        if priority_value >= 95:
            return PriorityLevel.CRITICAL
        elif priority_value >= 70:
            return PriorityLevel.HIGH
        elif priority_value >= 40:
            return PriorityLevel.MEDIUM
        else:
            return PriorityLevel.LOW
    
    def sort_warnings_by_priority(
        self,
        warnings: List[TrafficWarning]
    ) -> List[TrafficWarning]:
        """
        Sắp xếp warnings theo priority (cao nhất trước)
        
        Args:
            warnings: List warnings
        
        Returns:
            Sorted list
        """
        return sorted(warnings, key=lambda w: w.priority, reverse=True)
    
    def get_highest_priority_warning(
        self,
        warnings: List[TrafficWarning]
    ) -> Optional[TrafficWarning]:
        """
        Lấy warning có priority cao nhất
        
        Args:
            warnings: List warnings
        
        Returns:
            Warning với priority cao nhất hoặc None
        """
        if not warnings:
            return None
        
        sorted_warnings = self.sort_warnings_by_priority(warnings)
        return sorted_warnings[0]
    
    def compare_warnings(self, w1: TrafficWarning, w2: TrafficWarning) -> int:
        """
        So sánh 2 warnings
        
        Args:
            w1, w2: Warnings
        
        Returns:
            1 nếu w1 > w2, -1 nếu w1 < w2, 0 nếu bằng
        """
        if w1.priority > w2.priority:
            return 1
        elif w1.priority < w2.priority:
            return -1
        else:
            return 0
    
    def get_priority_stats(self) -> Dict:
        """Lấy thống kê priority rules"""
        return {
            'total_rules': len(self.priority_rules),
            'priority_ranges': self.PRIORITY_RANGES.copy(),
            'rules': {
                k: v for k, v in self.priority_rules.items()
            }
        }
