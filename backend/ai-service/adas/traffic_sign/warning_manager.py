"""
TV5.0 - Warning Manager
Điều phối toàn bộ TV5 - Quản lý cảnh báo
Quản lý queue, filter duplicate, lưu history, đồng bộ dashboard, voice alert, logging
"""

from typing import List, Optional, Dict, Any, Set
from models import TrafficWarning, WarningEvent
from warning_queue import WarningQueue
from warning_history import WarningHistoryManager
from datetime import datetime, timedelta
from config import get_config


class WarningManager:
    """
    TV5 Service - Điều phối toàn bộ quản lý cảnh báo
    
    Chức năng:
    - Warning Queue: Quản lý hàng đợi cảnh báo
    - Duplicate Filter: Lọc cảnh báo trùng lặp
    - Warning History: Lưu lịch sử
    - Dashboard: Đồng bộ dashboard
    - Voice Alert: Phát cảnh báo giọng nói
    - Logging: Ghi log
    """
    
    def __init__(self):
        self.warning_queue = WarningQueue()
        self.history_manager = WarningHistoryManager()
        self.duplicate_filter_time = get_config().tv5_duplicate_filter_time
        
        # Duplicate tracking
        self.last_warnings: Dict[str, datetime] = {}  # type -> last_time
        self.current_displaying: Optional[WarningEvent] = None
        
        # Logging
        self.event_log: List[Dict[str, Any]] = []
    
    def process_warning(self, warning: TrafficWarning) -> Optional[WarningEvent]:
        """
        Xử lý warning từ TV4
        
        Args:
            warning: TrafficWarning object từ TV4
        
        Returns:
            WarningEvent nếu được thêm vào queue, None nếu bị lọc
        """
        # Step 1: Duplicate filter
        if self._is_duplicate(warning):
            self._log_event("duplicate_filtered", warning.type, warning.warning_id)
            return None
        
        # Step 2: Enqueue
        event = self.warning_queue.enqueue(warning)
        self._log_event("enqueued", warning.type, event.event_id)
        
        return event
    
    def process_batch_warnings(
        self,
        warnings: List[TrafficWarning]
    ) -> List[WarningEvent]:
        """
        Xử lý batch warnings từ TV4
        
        Args:
            warnings: List TrafficWarning
        
        Returns:
            List WarningEvents
        """
        events = []
        for warning in warnings:
            event = self.process_warning(warning)
            if event is not None:
                events.append(event)
        
        return events
    
    def get_next_warning(self) -> Optional[WarningEvent]:
        """
        Lấy warning tiếp theo từ queue để hiển thị
        
        Returns:
            WarningEvent hoặc None nếu queue rỗng
        """
        event = self.warning_queue.dequeue()
        
        if event is not None:
            event.status = "ACTIVE"
            self.current_displaying = event
            self._log_event("displayed", event.warning.type, event.event_id)
        
        return event
    
    def dismiss_current_warning(self) -> bool:
        """Hủy cảnh báo đang hiển thị"""
        if self.current_displaying is None:
            return False
        
        self.current_displaying.status = "DISMISSED"
        self.current_displaying.dismissed_at = datetime.now()
        
        # Add to history
        display_duration = int(
            (datetime.now() - self.current_displaying.created_at).total_seconds()
        )
        self.history_manager.add_entry(
            self.current_displaying,
            display_duration
        )
        
        self._log_event(
            "dismissed",
            self.current_displaying.warning.type,
            self.current_displaying.event_id
        )
        
        self.current_displaying = None
        return True
    
    def mark_warning_expired(self, event: WarningEvent) -> bool:
        """
        Mark warning là hết hạn (timeout)
        
        Args:
            event: WarningEvent
        
        Returns:
            True nếu thành công
        """
        event.status = "EXPIRED"
        event.dismissed_at = datetime.now()
        
        # Add to history
        display_duration = int(
            (datetime.now() - event.created_at).total_seconds()
        )
        self.history_manager.add_entry(event, display_duration)
        
        self._log_event("expired", event.warning.type, event.event_id)
        
        if event == self.current_displaying:
            self.current_displaying = None
        
        return True
    
    def _is_duplicate(self, warning: TrafficWarning) -> bool:
        """
        Kiểm tra warning có phải duplicate không
        
        Args:
            warning: TrafficWarning
        
        Returns:
            True nếu là duplicate, False nếu không
        """
        warning_type = warning.type
        
        if warning_type not in self.last_warnings:
            self.last_warnings[warning_type] = datetime.now()
            return False
        
        last_time = self.last_warnings[warning_type]
        time_diff = (datetime.now() - last_time).total_seconds()
        
        # Nếu cách nhau < duplicate_filter_time thì là duplicate
        if time_diff < self.duplicate_filter_time:
            return True
        
        # Update last time
        self.last_warnings[warning_type] = datetime.now()
        return False
    
    def get_current_warning(self) -> Optional[WarningEvent]:
        """Lấy warning đang hiển thị"""
        return self.current_displaying
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Lấy trạng thái queue"""
        return self.warning_queue.get_queue_status()
    
    def get_history_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê lịch sử"""
        return self.history_manager.get_statistics()
    
    def get_manager_status(self) -> Dict[str, Any]:
        """Lấy trạng thái quản lý"""
        return {
            'current_warning': {
                'event_id': self.current_displaying.event_id if self.current_displaying else None,
                'type': self.current_displaying.warning.type if self.current_displaying else None,
                'level': self.current_displaying.warning.level if self.current_displaying else None,
            } if self.current_displaying else None,
            'queue': self.get_queue_status(),
            'history': self.get_history_statistics(),
            'total_events_logged': len(self.event_log)
        }
    
    def _log_event(self, event_type: str, warning_type: str, event_id: str):
        """
        Ghi log sự kiện
        
        Args:
            event_type: Loại event (enqueued, displayed, dismissed, ...)
            warning_type: Loại warning
            event_id: Event ID
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'warning_type': warning_type,
            'event_id': event_id
        }
        
        self.event_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-1000:]
    
    def get_event_log(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Lấy event log"""
        return self.event_log[-limit:]
    
    def export_all_data(self) -> Dict[str, Any]:
        """
        Export toàn bộ dữ liệu
        
        Returns:
            Dict với tất cả dữ liệu
        """
        return {
            'manager_status': self.get_manager_status(),
            'queue_status': self.get_queue_status(),
            'history': self.history_manager.export_to_dict(),
            'event_log': self.get_event_log(limit=100)
        }
    
    def reset(self):
        """Reset toàn bộ manager"""
        self.warning_queue.clear()
        self.history_manager.clear_history()
        self.event_log.clear()
        self.last_warnings.clear()
        self.current_displaying = None
