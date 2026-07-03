"""
TV3.1 - Speed Rule Parser
Nhận DrivingRuleData từ TV2 và extract thông tin speed limit
"""

from typing import Optional, Dict, Any
from models import DrivingRuleData


class SpeedRuleParser:
    """
    Parse DrivingRuleData từ TV2
    Extract thông tin liên quan tới giới hạn tốc độ
    """
    
    # Speed-related rules
    SPEED_RULES = {
        "SET_SPEED_LIMIT"
    }
    
    @staticmethod
    def is_speed_rule(driving_rule: DrivingRuleData) -> bool:
        """
        Kiểm tra xem rule có phải là speed-related rule không
        
        Args:
            driving_rule: DrivingRuleData object
        
        Returns:
            True nếu rule liên quan tới tốc độ, False nếu không
        """
        return driving_rule.rule in SpeedRuleParser.SPEED_RULES
    
    @staticmethod
    def extract_speed_limit(driving_rule: DrivingRuleData) -> Optional[int]:
        """
        Extract giới hạn tốc độ từ DrivingRuleData
        
        Args:
            driving_rule: DrivingRuleData object
        
        Returns:
            Giới hạn tốc độ (int) hoặc None nếu không có
        
        Raises:
            ValueError: Nếu speed_limit không hợp lệ
        """
        if not SpeedRuleParser.is_speed_rule(driving_rule):
            return None
        
        if driving_rule.speed_limit is None:
            raise ValueError(f"Speed rule '{driving_rule.rule}' không có speed_limit value")
        
        # Validate speed_limit
        if not 0 <= driving_rule.speed_limit <= 200:
            raise ValueError(f"Invalid speed_limit: {driving_rule.speed_limit}")
        
        return driving_rule.speed_limit
    
    @staticmethod
    def parse_driving_rule(
        driving_rule: DrivingRuleData
    ) -> Optional[Dict[str, Any]]:
        """
        Parse DrivingRuleData để extract speed information
        
        Args:
            driving_rule: DrivingRuleData object
        
        Returns:
            Dict với thông tin speed hoặc None nếu không phải speed rule
            {
                'is_speed_rule': bool,
                'speed_limit': int (nếu có),
                'frame_id': int,
                'timestamp': datetime
            }
        """
        if not SpeedRuleParser.is_speed_rule(driving_rule):
            return None
        
        try:
            speed_limit = SpeedRuleParser.extract_speed_limit(driving_rule)
            
            return {
                'is_speed_rule': True,
                'speed_limit': speed_limit,
                'frame_id': driving_rule.frame_id,
                'rule': driving_rule.rule,
                'message': driving_rule.message,
                'timestamp': driving_rule.timestamp
            }
        except ValueError as e:
            print(f"Error parsing speed rule: {str(e)}")
            return None
    
    @staticmethod
    def validate_speed_value(speed: int) -> bool:
        """
        Kiểm tra speed value có hợp lệ không
        
        Args:
            speed: Giá trị tốc độ
        
        Returns:
            True nếu hợp lệ (0-200), False nếu không
        """
        return 0 <= speed <= 200
