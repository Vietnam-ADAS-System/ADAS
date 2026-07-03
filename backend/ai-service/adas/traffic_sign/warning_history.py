"""
TV5.3 - Warning History
Lưu lịch sử cảnh báo để phân tích và debugging
"""

from typing import List, Dict, Any, Optional
from collections import deque
from models import WarningHistory, WarningEvent, PriorityLevel
from datetime import datetime
from config import get_config


class WarningHistoryManager:
    """
    Quản lý lịch sử warnings
    
    Features:
    - Lưu lịch sử mỗi warning
    - Query theo thời gian
    - Thống kê
    - Size limit
    """
    
    def __init__(self, max_records: Optional[int] = None):
        if max_records is None:
            config = get_config()
            max_records = config.tv5_history_max_records
        
        self.max_records = max_records
        self.history: deque = deque(maxlen=max_records)
    
    def add_entry(
        self,
        event: WarningEvent,
        display_duration: int
    ) -> WarningHistory:
        """
        Thêm entry vào history
        
        Args:
            event: WarningEvent object
            display_duration: Thời gian hiển thị thực tế (giây)
        
        Returns:
            WarningHistory object
        """
        history_entry = WarningHistory(
            event_id=event.event_id,
            warning_type=event.warning.type,
            level=event.warning.level,
            message=event.warning.message,
            created_at=event.created_at,
            dismissed_at=event.dismissed_at,
            display_duration=display_duration
        )
        
        self.history.append(history_entry)
        return history_entry
    
    def get_all_history(self) -> List[WarningHistory]:
        """Lấy toàn bộ lịch sử"""
        return list(self.history)
    
    def get_recent_history(self, limit: int = 10) -> List[WarningHistory]:
        """
        Lấy N entries gần nhất
        
        Args:
            limit: Số entries
        
        Returns:
            List WarningHistory
        """
        history_list = list(self.history)
        return history_list[-limit:]
    
    def get_history_by_type(self, warning_type: str) -> List[WarningHistory]:
        """
        Lấy lịch sử theo loại warning
        
        Args:
            warning_type: Loại warning
        
        Returns:
            List WarningHistory
        """
        return [h for h in self.history if h.warning_type == warning_type]
    
    def get_history_by_level(self, level: PriorityLevel) -> List[WarningHistory]:
        """
        Lấy lịch sử theo priority level
        
        Args:
            level: PriorityLevel
        
        Returns:
            List WarningHistory
        """
        return [h for h in self.history if h.level == level]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Lấy thống kê lịch sử
        
        Returns:
            Dict với thống kê
        """
        if not self.history:
            return {
                'total_warnings': 0,
                'by_type': {},
                'by_level': {},
                'avg_display_duration': 0
            }
        
        # Thống kê theo loại
        by_type = {}
        for entry in self.history:
            by_type[entry.warning_type] = by_type.get(entry.warning_type, 0) + 1
        
        # Thống kê theo level
        by_level = {}
        for entry in self.history:
            level_name = entry.level.value
            by_level[level_name] = by_level.get(level_name, 0) + 1
        
        # Average display duration
        total_duration = sum(h.display_duration for h in self.history)
        avg_duration = total_duration / len(self.history) if self.history else 0
        
        return {
            'total_warnings': len(self.history),
            'by_type': by_type,
            'by_level': by_level,
            'avg_display_duration': round(avg_duration, 2),
            'capacity_used': f"{len(self.history)}/{self.max_records}"
        }
    
    def clear_history(self):
        """Xóa toàn bộ history"""
        self.history.clear()
    
    def export_to_dict(self) -> List[Dict[str, Any]]:
        """
        Export history sang list dict
        
        Returns:
            List dict
        """
        result = []
        for entry in self.history:
            result.append({
                'event_id': entry.event_id,
                'type': entry.warning_type,
                'level': entry.level.value,
                'message': entry.message,
                'created_at': entry.created_at.isoformat(),
                'dismissed_at': entry.dismissed_at.isoformat() if entry.dismissed_at else None,
                'display_duration': entry.display_duration
            })
        return result
