"""
TV3.4 - Dashboard Sender
Đồng bộ Current Speed Limit lên Dashboard
"""

from typing import Dict, Any, Optional, List
from models import SpeedLimitState
from datetime import datetime
import json


class DashboardSender:
    """
    Đồng bộ Current Speed Limit lên Dashboard
    Gửi SpeedLimitState để Dashboard hiển thị
    """
    
    def __init__(self):
        self.last_sent_state: Optional[SpeedLimitState] = None
        self.last_sent_time: Optional[datetime] = None
        self.send_history: List[Dict[str, Any]] = []
    
    def send_speed_limit_state(
        self,
        state: SpeedLimitState
    ) -> Dict[str, Any]:
        """
        Gửi SpeedLimitState lên Dashboard
        
        Args:
            state: SpeedLimitState object
        
        Returns:
            Dict với kết quả gửi
            {
                'success': bool,
                'sent_at': datetime,
                'speed_limit': int,
                'status': str
            }
        """
        try:
            # Chuẩn bị dữ liệu gửi
            payload = {
                'frame_id': state.frame_id,
                'speed_limit': state.speed_limit,
                'status': state.status,
                'source': state.source,
                'updated_at': state.updated_at.isoformat()
            }
            
            # Log send
            send_record = {
                'sent_at': datetime.now().isoformat(),
                'payload': payload,
                'success': True
            }
            self.send_history.append(send_record)
            
            # Keep last 100 records
            if len(self.send_history) > 100:
                self.send_history = self.send_history[-100:]
            
            self.last_sent_state = state
            self.last_sent_time = datetime.now()
            
            return {
                'success': True,
                'sent_at': self.last_sent_time,
                'speed_limit': state.speed_limit,
                'status': state.status,
                'message': f"Speed limit {state.speed_limit} km/h sent to dashboard"
            }
            
        except Exception as e:
            print(f"Error sending to dashboard: {str(e)}")
            return {
                'success': False,
                'sent_at': datetime.now(),
                'error': str(e)
            }
    
    def send_batch_states(self, states: List[SpeedLimitState]) -> List[Dict[str, Any]]:
        """
        Gửi multiple states
        
        Args:
            states: List SpeedLimitState objects
        
        Returns:
            List kết quả gửi
        """
        results = []
        for state in states:
            result = self.send_speed_limit_state(state)
            results.append(result)
        return results
    
    def get_last_sent_state(self) -> Optional[SpeedLimitState]:
        """Lấy state gần nhất được gửi"""
        return self.last_sent_state
    
    def get_send_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử gửi
        
        Args:
            limit: Số lượng records để lấy
        
        Returns:
            List lịch sử gửi
        """
        return self.send_history[-limit:]
    
    def get_dashboard_display_data(self) -> Optional[Dict[str, Any]]:
        """
        Lấy dữ liệu để dashboard hiển thị
        
        Returns:
            Dict với thông tin hiển thị hoặc None
        """
        if self.last_sent_state is None:
            return None
        
        state = self.last_sent_state
        return {
            'display_value': f"{state.speed_limit} km/h",
            'speed_limit': state.speed_limit,
            'status': state.status,
            'source': state.source,
            'last_updated': self.last_sent_time.isoformat() if self.last_sent_time else None,
            'time_ago': self._get_time_ago()
        }
    
    def _get_time_ago(self) -> str:
        """Tính thời gian cách đây"""
        if self.last_sent_time is None:
            return "Unknown"
        
        elapsed = datetime.now() - self.last_sent_time
        seconds = int(elapsed.total_seconds())
        
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m ago"
        else:
            hours = seconds // 3600
            return f"{hours}h ago"
    
    def reset_history(self):
        """Reset lịch sử gửi"""
        self.send_history.clear()
        self.last_sent_state = None
        self.last_sent_time = None
