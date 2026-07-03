"""
TV4.1 - Warning Decision Engine
Quyết định có phát cảnh báo hay không dựa trên Driving Rule
"""

from typing import Optional, Dict, List, Any
from models import DrivingRuleData, SpeedLimitState, TrafficWarning, PriorityLevel
from priority_manager import PriorityManager
from datetime import datetime, timedelta
import uuid


class WarningDecisionEngine:
    """
    TV4 Decision Engine
    Phân tích DrivingRuleData và Context để quyết định warning
    
    Decision Rules:
    - NO_ENTRY: Warning HIGH
    - STOP: Warning HIGH + immediate stop
    - SPEED_LIMIT: No warning (chỉ cập nhật state)
    - PEDESTRIAN: Warning HIGH + reduce speed
    - SCHOOL_ZONE: Warning MEDIUM
    - BUS_STOP: Warning LOW
    """
    
    # Warning type mapping
    RULE_TO_WARNING_MAP = {
        "NO_ENTRY": "NO_ENTRY",
        "STOP": "STOP",
        "GIVE_WAY": "GIVE_WAY",
        "SPEED_LIMIT": None,  # Không sinh warning
        "PEDESTRIAN_CROSSING": "PEDESTRIAN_CROSSING",
        "SCHOOL_ZONE": "SCHOOL_ZONE",
        "BUS_STOP": "BUS_STOP",
        "ROUNDABOUT": "ROUNDABOUT",
        "PREPARE_TO_STOP": "PREPARE_TO_STOP",
    }
    
    def __init__(self):
        self.priority_manager = PriorityManager()
        self.last_warnings: Dict[str, TrafficWarning] = {}
    
    def make_decision(
        self,
        driving_rule: DrivingRuleData,
        speed_limit_state: Optional[SpeedLimitState] = None
    ) -> Optional[TrafficWarning]:
        """
        Quyết định có sinh warning hay không
        
        Args:
            driving_rule: DrivingRuleData từ TV2
            speed_limit_state: SpeedLimitState từ TV3 (context)
        
        Returns:
            TrafficWarning hoặc None nếu không sinh warning
        """
        # Step 1: Xác định loại warning
        warning_type = self.RULE_TO_WARNING_MAP.get(driving_rule.rule)
        
        if warning_type is None:
            # Không sinh warning cho rule này
            return None
        
        # Step 2: Lấy priority settings
        priority_settings = self.priority_manager.get_priority_for_warning_type(
            driving_rule.rule
        )
        
        # Step 3: Sinh warning
        warning = self._create_warning(
            driving_rule=driving_rule,
            warning_type=warning_type,
            priority_settings=priority_settings
        )
        
        return warning
    
    def _create_warning(
        self,
        driving_rule: DrivingRuleData,
        warning_type: str,
        priority_settings: Dict[str, Any]
    ) -> TrafficWarning:
        """
        Tạo TrafficWarning object
        
        Args:
            driving_rule: DrivingRuleData
            warning_type: Loại warning
            priority_settings: Priority settings từ config
        
        Returns:
            TrafficWarning object
        """
        warning_id = f"warn_{uuid.uuid4().hex[:12]}"
        priority_value = priority_settings['priority']
        level = self.priority_manager.assign_level(priority_value)
        duration = priority_settings['duration']
        
        expire_time = datetime.now() + timedelta(seconds=duration)
        
        warning = TrafficWarning(
            warning_id=warning_id,
            type=warning_type,
            level=level,
            message=driving_rule.message,
            priority=priority_value,
            duration=duration,
            timestamp=datetime.now(),
            expire_time=expire_time
        )
        
        # Lưu vào history
        self.last_warnings[warning_id] = warning
        
        return warning
    
    def evaluate_multiple_rules(
        self,
        driving_rules: List[DrivingRuleData],
        speed_limit_state: Optional[SpeedLimitState] = None
    ) -> List[TrafficWarning]:
        """
        Đánh giá nhiều driving rules
        
        Args:
            driving_rules: List DrivingRuleData
            speed_limit_state: SpeedLimitState (context)
        
        Returns:
            List TrafficWarnings (có thể rỗng)
        """
        warnings = []
        for rule in driving_rules:
            warning = self.make_decision(rule, speed_limit_state)
            if warning is not None:
                warnings.append(warning)
        
        # Sort by priority
        return self.priority_manager.sort_warnings_by_priority(warnings)
    
    def should_alert_driver(self, warning: TrafficWarning) -> bool:
        """
        Kiểm tra xem có nên alert driver không
        
        Args:
            warning: TrafficWarning object
        
        Returns:
            True nếu nên alert
        """
        # HIGH hoặc CRITICAL thì phải alert
        return warning.level in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """Lấy thống kê quyết định"""
        return {
            'total_warnings_created': len(self.last_warnings),
            'warning_types': len(set(w.type for w in self.last_warnings.values())),
            'priority_distribution': self._get_priority_distribution(),
            'rule_mapping': self.RULE_TO_WARNING_MAP
        }
    
    def _get_priority_distribution(self) -> Dict[str, int]:
        """Tính distribution của priority levels"""
        distribution = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }
        
        for warning in self.last_warnings.values():
            distribution[warning.level.value] += 1
        
        return distribution
