"""
TV3.0 - Speed Limit Service
Điều phối toàn bộ TV3 - Speed Limit State Management & Dashboard Synchronization
"""

from typing import Optional, Dict, Any
from models import DrivingRuleData, SpeedLimitState
from speed_rule_parser import SpeedRuleParser
from speed_limit_manager import SpeedLimitManager
from dashboard_sender import DashboardSender


class SpeedLimitService:
    """
    TV3 Service - Quản lý trạng thái giới hạn tốc độ
    
    Pipeline:
    1. Nhận DrivingRuleData từ TV2
    2. Parse để lấy speed limit value
    3. Cập nhật Current Speed Limit
    4. Sinh SpeedLimitState
    5. Đồng bộ Dashboard
    6. Publish cho TV4
    """
    
    def __init__(self):
        self.rule_parser = SpeedRuleParser()
        self.speed_manager = SpeedLimitManager()
        self.dashboard = DashboardSender()
        self.state_history: Dict[int, SpeedLimitState] = {}
    
    def process_driving_rule(
        self,
        driving_rule: DrivingRuleData
    ) -> Optional[SpeedLimitState]:
        """
        Xử lý DrivingRuleData từ TV2
        
        Args:
            driving_rule: DrivingRuleData object từ TV2
        
        Returns:
            SpeedLimitState hoặc None nếu rule không phải speed-related
        """
        # Step 1: Parse driving rule
        parsed = self.rule_parser.parse_driving_rule(driving_rule)
        
        if parsed is None:
            # Không phải speed rule, skip
            return None
        
        # Step 2: Extract speed_limit
        speed_limit = parsed.get('speed_limit')
        if speed_limit is None:
            return None
        
        # Step 3: Cập nhật Current Speed Limit
        state = self.speed_manager.update_speed_limit(
            speed_limit=speed_limit,
            frame_id=driving_rule.frame_id,
            source="Traffic Sign"
        )
        
        # Step 4: Lưu vào history
        self.state_history[driving_rule.frame_id] = state
        
        # Step 5: Đồng bộ Dashboard
        self.dashboard.send_speed_limit_state(state)
        
        return state
    
    def get_current_state(self) -> SpeedLimitState:
        """
        Lấy Current Speed Limit State
        
        Returns:
            SpeedLimitState object
        """
        return self.speed_manager.get_state()
    
    def check_expiration(self, frame_id: int) -> Optional[SpeedLimitState]:
        """
        Kiểm tra xem speed limit đã hết hạn không
        
        Args:
            frame_id: Frame ID hiện tại
        
        Returns:
            Updated SpeedLimitState hoặc None
        """
        self.speed_manager.check_and_update_status()
        
        if self.speed_manager.status == "EXPIRED":
            # Reset về default
            self.speed_manager.reset_to_default(frame_id)
            state = self.speed_manager.get_state()
            self.dashboard.send_speed_limit_state(state)
            return state
        
        return None
    
    def publish_state_for_tv4(self) -> SpeedLimitState:
        """
        Publish SpeedLimitState cho TV4
        
        Returns:
            SpeedLimitState để TV4 sử dụng
        """
        return self.speed_manager.get_state()
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Lấy trạng thái dịch vụ
        
        Returns:
            Dict với thông tin trạng thái
        """
        current_state = self.speed_manager.get_current_speed_limit()
        dashboard_data = self.dashboard.get_dashboard_display_data()
        
        return {
            'current_speed_limit': current_state['speed_limit'],
            'status': current_state['status'],
            'source': current_state['source'],
            'updated_at': current_state['updated_at'].isoformat() if current_state['updated_at'] else None,
            'dashboard_display': dashboard_data,
            'history_count': len(self.state_history),
            'is_expired': self.speed_manager.is_speed_limit_expired()
        }
    
    def reset(self, frame_id: int):
        """
        Reset toàn bộ service về default state
        
        Args:
            frame_id: Frame ID hiện tại
        """
        self.speed_manager.reset_to_default(frame_id)
        self.state_history.clear()
        self.dashboard.reset_history()
