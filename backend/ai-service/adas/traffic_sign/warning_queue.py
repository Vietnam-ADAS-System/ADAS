"""
TV5.1 - Warning Queue
Quản lý hàng đợi cảnh báo
"""

from typing import List, Optional, Dict, Any
from collections import deque
from models import WarningEvent, TrafficWarning
from datetime import datetime
from config import get_config
import uuid


class WarningQueue:
    """
    Quản lý queue các warning events
    
    Features:
    - FIFO queue
    - Size limit (từ config)
    - Enqueue/Dequeue
    - Peek
    """
    
    def __init__(self, max_size: Optional[int] = None):
        if max_size is None:
            config = get_config()
            max_size = config.tv5_warning_queue_size
        
        self.max_size = max_size
        self.queue: deque = deque(maxlen=max_size)
        self.enqueued_count = 0  # Tổng số items đã được enqueue
    
    def enqueue(self, warning: TrafficWarning) -> WarningEvent:
        """
        Thêm warning vào queue
        
        Args:
            warning: TrafficWarning object
        
        Returns:
            WarningEvent object
        """
        event = WarningEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            warning=warning,
            status="PENDING",
            created_at=datetime.now()
        )
        
        self.queue.append(event)
        self.enqueued_count += 1
        
        return event
    
    def dequeue(self) -> Optional[WarningEvent]:
        """
        Lấy warning từ queue
        
        Returns:
            WarningEvent hoặc None nếu queue rỗng
        """
        if len(self.queue) == 0:
            return None
        
        return self.queue.popleft()
    
    def peek(self) -> Optional[WarningEvent]:
        """
        Xem warning đầu tiên mà không lấy ra
        
        Returns:
            WarningEvent hoặc None
        """
        if len(self.queue) == 0:
            return None
        
        return self.queue[0]
    
    def peek_all(self) -> List[WarningEvent]:
        """Xem tất cả warnings trong queue"""
        return list(self.queue)
    
    def size(self) -> int:
        """Lấy kích thước queue hiện tại"""
        return len(self.queue)
    
    def is_empty(self) -> bool:
        """Kiểm tra queue có rỗng không"""
        return len(self.queue) == 0
    
    def is_full(self) -> bool:
        """Kiểm tra queue có đầy không"""
        return len(self.queue) == self.max_size
    
    def clear(self):
        """Xóa toàn bộ queue"""
        self.queue.clear()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Lấy thông tin trạng thái queue"""
        return {
            'size': self.size(),
            'max_size': self.max_size,
            'is_empty': self.is_empty(),
            'is_full': self.is_full(),
            'total_enqueued': self.enqueued_count,
            'warnings': [
                {
                    'event_id': e.event_id,
                    'type': e.warning.type,
                    'level': e.warning.level,
                    'status': e.status,
                    'created_at': e.created_at.isoformat()
                }
                for e in self.queue
            ]
        }
