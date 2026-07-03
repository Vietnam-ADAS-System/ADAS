"""
Config loader cho Traffic Sign Warning Module
Đọc cấu hình từ YAML file
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


class TrafficSignConfig:
    """Configuration cho Traffic Sign Warning Module"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "traffic_sign_config.yaml"
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML config file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config if config else {}
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'tv1': {
                'confidence_threshold': 0.5,
                'max_class_id': 51,
                'min_class_id': 0,
            },
            'tv3': {
                'default_speed_limit': 40,
                'speed_limit_duration': 30,  # giây
            },
            'tv4': {
                'warning_priority_rules': {
                    'NO_ENTRY': {'level': 'HIGH', 'priority': 90, 'duration': 5},
                    'STOP': {'level': 'HIGH', 'priority': 95, 'duration': 3},
                    'SPEED_LIMIT': {'level': 'MEDIUM', 'priority': 60, 'duration': 10},
                    'PEDESTRIAN_CROSSING': {'level': 'HIGH', 'priority': 85, 'duration': 5},
                    'SCHOOL_ZONE': {'level': 'MEDIUM', 'priority': 65, 'duration': 8},
                },
                'warning_timeout': 30,  # giây
            },
            'tv5': {
                'warning_queue_size': 10,
                'duplicate_filter_time': 2,  # giây
                'history_max_records': 100,
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by key (dot notation)"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    # TV1 Config
    @property
    def tv1_confidence_threshold(self) -> float:
        return self.get('tv1.confidence_threshold', 0.5)
    
    @property
    def tv1_max_class_id(self) -> int:
        return self.get('tv1.max_class_id', 51)
    
    # TV3 Config
    @property
    def tv3_default_speed_limit(self) -> int:
        return self.get('tv3.default_speed_limit', 40)
    
    @property
    def tv3_speed_limit_duration(self) -> int:
        return self.get('tv3.speed_limit_duration', 30)
    
    # TV4 Config
    @property
    def tv4_warning_priority_rules(self) -> Dict[str, Dict]:
        return self.get('tv4.warning_priority_rules', {})
    
    @property
    def tv4_warning_timeout(self) -> int:
        return self.get('tv4.warning_timeout', 30)
    
    # TV5 Config
    @property
    def tv5_warning_queue_size(self) -> int:
        return self.get('tv5.warning_queue_size', 10)
    
    @property
    def tv5_duplicate_filter_time(self) -> int:
        return self.get('tv5.duplicate_filter_time', 2)
    
    @property
    def tv5_history_max_records(self) -> int:
        return self.get('tv5.history_max_records', 100)


# Global config instance
_config_instance = None

def get_config(config_path: str = None) -> TrafficSignConfig:
    """Get global config instance (singleton)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = TrafficSignConfig(config_path)
    return _config_instance
