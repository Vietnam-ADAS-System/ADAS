"""
TV4.3 - Warning Timer
Quản lý thời gian hiển thị warning (timeout)
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from models import TrafficWarning
import uuid


class WarningTimer:
    """
    Quản lý timer cho warnings
    Theo dõi thời gian hiển thị và hết hạn
    """
    
    def __init__(self):
        # warning_id -> {start_time, expire_time}
        self.active_timers: Dict[str, Dict] = {}
    
    def start_timer(
        self,
        warning_id: str,
        duration: int
    ) -> Dict[str, any]:
        """
        Bắt đầu timer cho warning
        
        Args:
            warning_id: ID của warning
            duration: Thời gian hiển thị (giây)
        
        Returns:
            Dict với thông tin timer
            {
                'warning_id': str,
                'start_time': datetime,
                'expire_time': datetime,
                'remaining': int (giây)
            }
        """
        start_time = datetime.now()
        expire_time = start_time + timedelta(seconds=duration)
        
        self.active_timers[warning_id] = {
            'start_time': start_time,
            'expire_time': expire_time,
            'duration': duration
        }
        
        return {
            'warning_id': warning_id,
            'start_time': start_time,
            'expire_time': expire_time,
            'remaining': duration
        }
    
    def is_warning_expired(self, warning_id: str) -> bool:
        """
        Kiểm tra xem warning đã hết hạn không
        
        Args:
            warning_id: ID của warning
        
        Returns:
            True nếu hết hạn, False nếu vẫn active
        """
        if warning_id not in self.active_timers:
            return True  # Không có timer = expired
        
        timer = self.active_timers[warning_id]
        return datetime.now() >= timer['expire_time']
    
    def get_remaining_time(self, warning_id: str) -> Optional[int]:
        """
        Lấy thời gian còn lại (giây)
        
        Args:
            warning_id: ID của warning
        
        Returns:
            Số giây còn lại hoặc None nếu expired
        """
        if warning_id not in self.active_timers:
            return None
        
        if self.is_warning_expired(warning_id):
            return 0
        
        timer = self.active_timers[warning_id]
        remaining = (timer['expire_time'] - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def stop_timer(self, warning_id: str) -> bool:
        """
        Dừng timer (hủy warning)
        
        Args:
            warning_id: ID của warning
        
        Returns:
            True nếu thành công, False nếu warning không tồn tại
        """
        if warning_id in self.active_timers:
            del self.active_timers[warning_id]
            return True
        return False
    
    def get_expired_warnings(self) -> List[str]:
        """
        Lấy danh sách các warning đã hết hạn
        
        Returns:
            List warning IDs
        """
        expired = []
        for warning_id in list(self.active_timers.keys()):
            if self.is_warning_expired(warning_id):
                expired.append(warning_id)
        return expired
    
    def cleanup_expired(self) -> List[str]:
        """
        Xóa tất cả expired warnings khỏi timer
        
        Returns:
            List warning IDs đã bị xóa
        """
        expired = self.get_expired_warnings()
        for warning_id in expired:
            del self.active_timers[warning_id]
        return expired
    
    def get_active_warnings_count(self) -> int:
        """Đếm số warning đang active"""
        # Clean up expired first
        self.cleanup_expired()
        return len(self.active_timers)
    
    def get_timers_info(self) -> Dict:
        """Lấy thông tin tất cả timers"""
        info = {}
        for warning_id, timer in self.active_timers.items():
            remaining = self.get_remaining_time(warning_id)
            if remaining is not None:
                info[warning_id] = {
                    'remaining': remaining,
                    'expire_time': timer['expire_time'].isoformat(),
                    'duration': timer['duration']
                }
        return info
