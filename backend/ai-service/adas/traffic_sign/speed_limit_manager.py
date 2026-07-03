"""
TV3.2 - Speed Limit Manager
Quản lý Current Speed Limit hiện hành
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from models import SpeedLimitState
from config import get_config


class SpeedLimitManager:
    """
    Quản lý trạng thái giới hạn tốc độ hiện hành
    
    Features:
    - Cập nhật Current Speed Limit
    - Kiểm tra hết hạn
    - Duy trì trạng thái
    """
    
    def __init__(self):
        config = get_config()
        self.current_speed_limit: Optional[int] = config.tv3_default_speed_limit
        self.current_frame_id: int = 0
        self.last_update_time: Optional[datetime] = None
        self.speed_limit_duration = config.tv3_speed_limit_duration
        self.status: str = "INACTIVE"
        self.source: str = "Default"
    
    def update_speed_limit(self, speed_limit: int, frame_id: int, source: str = "Traffic Sign") -> SpeedLimitState:
        """
        Cập nhật Current Speed Limit
        
        Args:
            speed_limit: Giới hạn tốc độ mới (km/h)
            frame_id: Frame ID
            source: Nguồn cập nhật (Traffic Sign, Default, ...)
        
        Returns:
            SpeedLimitState object
        
        Raises:
            ValueError: Nếu speed_limit không hợp lệ
        """
        if not 0 <= speed_limit <= 200:
            raise ValueError(f"Invalid speed_limit: {speed_limit}")
        
        self.current_speed_limit = speed_limit
        self.current_frame_id = frame_id
        self.last_update_time = datetime.now()
        self.status = "ACTIVE"
        self.source = source
        
        return SpeedLimitState(
            frame_id=frame_id,
            speed_limit=speed_limit,
            status=self.status,
            source=source,
            updated_at=self.last_update_time
        )
    
    def get_current_speed_limit(self) -> Dict[str, Any]:
        """
        Lấy Current Speed Limit
        
        Returns:
            Dict với thông tin speed limit hiện hành
            {
                'speed_limit': int,
                'frame_id': int,
                'status': str,
                'source': str,
                'updated_at': datetime
            }
        """
        return {
            'speed_limit': self.current_speed_limit,
            'frame_id': self.current_frame_id,
            'status': self.status,
            'source': self.source,
            'updated_at': self.last_update_time
        }
    
    def get_state(self) -> SpeedLimitState:
        """
        Lấy SpeedLimitState hiện tại
        
        Returns:
            SpeedLimitState object
        """
        return SpeedLimitState(
            frame_id=self.current_frame_id,
            speed_limit=self.current_speed_limit,
            status=self.status,
            source=self.source,
            updated_at=self.last_update_time or datetime.now()
        )
    
    def is_speed_limit_expired(self) -> bool:
        """
        Kiểm tra xem Current Speed Limit đã hết hạn không
        
        Returns:
            True nếu hết hạn, False nếu vẫn active
        """
        if self.last_update_time is None:
            return False
        
        elapsed_time = datetime.now() - self.last_update_time
        duration = timedelta(seconds=self.speed_limit_duration)
        
        return elapsed_time > duration
    
    def check_and_update_status(self):
        """
        Kiểm tra và cập nhật status dựa trên thời gian
        Nếu hết hạn, chuyển sang INACTIVE
        """
        if self.status == "ACTIVE" and self.is_speed_limit_expired():
            self.status = "EXPIRED"
    
    def reset_to_default(self, frame_id: int):
        """
        Reset về default speed limit
        
        Args:
            frame_id: Frame ID
        """
        config = get_config()
        self.current_speed_limit = config.tv3_default_speed_limit
        self.current_frame_id = frame_id
        self.last_update_time = datetime.now()
        self.status = "INACTIVE"
        self.source = "Default"
    
    def get_history_entry(self) -> Dict[str, Any]:
        """
        Lấy entry cho history logging
        
        Returns:
            Dict với thông tin cho logging
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'speed_limit': self.current_speed_limit,
            'frame_id': self.current_frame_id,
            'status': self.status,
            'source': self.source,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None
        }
