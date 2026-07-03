"""
TV4.0 - Warning Service
Điều phối toàn bộ TV4 - Traffic Warning Decision Engine
"""

from typing import List, Optional, Dict, Any
from models import DrivingRuleData, SpeedLimitState, TrafficWarning
from warning_decision import WarningDecisionEngine
from priority_manager import PriorityManager
from warning_timer import WarningTimer


class WarningDecisionService:
    """
    TV4 Service - Decision Engine cho Traffic Warning
    
    Pipeline:
    1. Nhận DrivingRuleData từ TV2
    2. Nhận SpeedLimitState từ TV3 (context)
    3. Evaluate rule → Decision
    4. Assign priority & duration
    5. Sinh TrafficWarning
    6. Publish sang TV5
    """
    
    def __init__(self):
        self.decision_engine = WarningDecisionEngine()
        self.priority_manager = PriorityManager()
        self.timer_manager = WarningTimer()
        self.active_warnings: List[TrafficWarning] = []
    
    def process_driving_rule(
        self,
        driving_rule: DrivingRuleData,
        speed_limit_state: Optional[SpeedLimitState] = None
    ) -> Optional[TrafficWarning]:
        """
        Xử lý DrivingRuleData từ TV2
        
        Args:
            driving_rule: DrivingRuleData từ TV2
            speed_limit_state: SpeedLimitState từ TV3 (optional)
        
        Returns:
            TrafficWarning hoặc None
        """
        # Step 1: Decision
        warning = self.decision_engine.make_decision(
            driving_rule=driving_rule,
            speed_limit_state=speed_limit_state
        )
        
        if warning is None:
            return None
        
        # Step 2: Start timer
        self.timer_manager.start_timer(
            warning_id=warning.warning_id,
            duration=warning.duration
        )
        
        # Step 3: Add to active warnings
        self.active_warnings.append(warning)
        
        return warning
    
    def process_batch_rules(
        self,
        driving_rules: List[DrivingRuleData],
        speed_limit_state: Optional[SpeedLimitState] = None
    ) -> List[TrafficWarning]:
        """
        Xử lý batch driving rules
        
        Args:
            driving_rules: List DrivingRuleData
            speed_limit_state: SpeedLimitState
        
        Returns:
            List TrafficWarnings
        """
        warnings = self.decision_engine.evaluate_multiple_rules(
            driving_rules=driving_rules,
            speed_limit_state=speed_limit_state
        )
        
        for warning in warnings:
            # Start timer
            self.timer_manager.start_timer(
                warning_id=warning.warning_id,
                duration=warning.duration
            )
            # Add to active
            self.active_warnings.append(warning)
        
        return warnings
    
    def cleanup_expired_warnings(self) -> List[str]:
        """
        Xóa expired warnings
        
        Returns:
            List IDs của expired warnings
        """
        expired_ids = self.timer_manager.cleanup_expired()
        
        # Remove from active_warnings
        self.active_warnings = [
            w for w in self.active_warnings
            if w.warning_id not in expired_ids
        ]
        
        return expired_ids
    
    def dismiss_warning(self, warning_id: str) -> bool:
        """
        Hủy cảnh báo manually
        
        Args:
            warning_id: ID của warning
        
        Returns:
            True nếu thành công
        """
        # Stop timer
        self.timer_manager.stop_timer(warning_id)
        
        # Remove from active
        self.active_warnings = [
            w for w in self.active_warnings
            if w.warning_id != warning_id
        ]
        
        return True
    
    def get_active_warnings(self) -> List[TrafficWarning]:
        """Lấy danh sách warning đang active"""
        # Clean up expired first
        self.cleanup_expired_warnings()
        return self.active_warnings.copy()
    
    def get_highest_priority_warning(self) -> Optional[TrafficWarning]:
        """
        Lấy warning có priority cao nhất hiện hành
        
        Returns:
            TrafficWarning hoặc None
        """
        active = self.get_active_warnings()
        if not active:
            return None
        
        return self.priority_manager.get_highest_priority_warning(active)
    
    def publish_warnings_for_tv5(self) -> List[TrafficWarning]:
        """
        Publish warnings cho TV5
        
        Returns:
            List warnings sorted by priority
        """
        active = self.get_active_warnings()
        return self.priority_manager.sort_warnings_by_priority(active)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Lấy trạng thái dịch vụ"""
        active = self.get_active_warnings()
        
        return {
            'active_warnings_count': len(active),
            'active_warnings': [
                {
                    'warning_id': w.warning_id,
                    'type': w.type,
                    'level': w.level,
                    'priority': w.priority,
                    'remaining_time': self.timer_manager.get_remaining_time(w.warning_id)
                }
                for w in active
            ],
            'decision_stats': self.decision_engine.get_decision_stats(),
            'priority_stats': self.priority_manager.get_priority_stats()
        }
    
    def reset(self):
        """Reset toàn bộ service"""
        self.active_warnings.clear()
        self.timer_manager.active_timers.clear()
