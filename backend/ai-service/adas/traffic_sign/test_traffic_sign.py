"""
Unit Tests cho Traffic Sign Warning Module
"""

import pytest
from datetime import datetime, timedelta
from models import (
    DetectionResult, StandardTrafficSignData, BoundingBox,
    DrivingRuleData, SpeedLimitState, TrafficWarning, PriorityLevel,
    WarningEvent
)
from sign_input_service import SignInputService
from class_mapper import TrafficSignClassMapper
from confidence_filter import ConfidenceFilter
from bbox_parser import BboxParser
from speed_limit_service import SpeedLimitService
from warning_service import WarningDecisionService
from warning_manager import WarningManager


# ============================================================================
# TV1 TESTS
# ============================================================================

class TestTV1SignInputService:
    """Test TV1 - Traffic Sign Recognition Input"""
    
    def test_process_single_detection_valid(self):
        """Test xử lý một detection hợp lệ"""
        service = SignInputService(confidence_threshold=0.5)
        
        raw_detection = {
            "class_id": 38,
            "confidence": 0.95,
            "bbox": [150, 80, 240, 190]
        }
        
        result = service.process_detection(
            raw_detection=raw_detection,
            frame_id=120,
            tracking_id=5
        )
        
        assert result is not None
        assert result.class_id == 38
        assert result.class_name == "Gioi han toc do 50kmh"
        assert result.confidence == 0.95
        assert result.frame_id == 120
        assert result.tracking_id == 5
    
    def test_process_detection_low_confidence(self):
        """Test detection bị lọc vì confidence thấp"""
        service = SignInputService(confidence_threshold=0.5)
        
        raw_detection = {
            "class_id": 38,
            "confidence": 0.3,  # < 0.5
            "bbox": [150, 80, 240, 190]
        }
        
        result = service.process_detection(
            raw_detection=raw_detection,
            frame_id=120,
            tracking_id=5
        )
        
        assert result is None
    
    def test_process_batch_detections(self):
        """Test xử lý batch detections"""
        service = SignInputService(confidence_threshold=0.5)
        
        raw_detections = [
            {"class_id": 38, "confidence": 0.95, "bbox": [150, 80, 240, 190]},
            {"class_id": 2, "confidence": 0.92, "bbox": [200, 100, 300, 220]},
            {"class_id": 38, "confidence": 0.3, "bbox": [120, 150, 180, 240]},
        ]
        
        results = service.process_batch_detections(
            raw_detections=raw_detections,
            frame_id=120
        )
        
        # Should filter out low confidence
        assert len(results) == 2


class TestClassMapper:
    """Test Class Mapper"""
    
    def test_valid_class_id(self):
        """Test mapping class ID hợp lệ"""
        class_name = TrafficSignClassMapper.get_class_name(38)
        assert class_name == "Gioi han toc do 50kmh"
    
    def test_invalid_class_id(self):
        """Test mapping class ID không hợp lệ"""
        with pytest.raises(ValueError):
            TrafficSignClassMapper.get_class_name(99)
    
    def test_validate_class_id(self):
        """Test validate class ID"""
        assert TrafficSignClassMapper.validate_class_id(38) is True
        assert TrafficSignClassMapper.validate_class_id(99) is False


class TestConfidenceFilter:
    """Test Confidence Filter"""
    
    def test_filter_detection_pass(self):
        """Test detection pass filter"""
        filter = ConfidenceFilter(threshold=0.5)
        detection = DetectionResult(
            class_id=38,
            confidence=0.95,
            bbox=[150, 80, 240, 190]
        )
        assert filter.filter_detection(detection) is True
    
    def test_filter_detection_fail(self):
        """Test detection fail filter"""
        filter = ConfidenceFilter(threshold=0.5)
        detection = DetectionResult(
            class_id=38,
            confidence=0.3,
            bbox=[150, 80, 240, 190]
        )
        assert filter.filter_detection(detection) is False


class TestBboxParser:
    """Test Bbox Parser"""
    
    def test_parse_bbox_list_valid(self):
        """Test parse bbox list hợp lệ"""
        bbox = BboxParser.parse_bbox_list_to_object([150, 80, 240, 190])
        assert bbox is not None
        assert bbox.x1 == 150
        assert bbox.y1 == 80
        assert bbox.x2 == 240
        assert bbox.y2 == 190
    
    def test_parse_bbox_list_invalid(self):
        """Test parse bbox list không hợp lệ"""
        bbox = BboxParser.parse_bbox_list_to_object([150, 80])  # Thiếu tọa độ
        assert bbox is None
    
    def test_get_bbox_center(self):
        """Test tính tâm bbox"""
        bbox = BoundingBox(x1=150, y1=80, x2=240, y2=190)
        center_x, center_y = BboxParser.get_bbox_center(bbox)
        assert center_x == 195
        assert center_y == 135


# ============================================================================
# TV3 TESTS
# ============================================================================

class TestSpeedLimitService:
    """Test TV3 - Speed Limit State Management"""
    
    def test_process_speed_rule(self):
        """Test xử lý speed limit rule"""
        service = SpeedLimitService()
        
        driving_rule = DrivingRuleData(
            frame_id=120,
            tracking_id=5,
            rule="SET_SPEED_LIMIT",
            speed_limit=50,
            message="Gioi han toc do 50kmh"
        )
        
        state = service.process_driving_rule(driving_rule)
        
        assert state is not None
        assert state.speed_limit == 50
        assert state.status == "ACTIVE"
    
    def test_process_non_speed_rule(self):
        """Test rule không phải speed rule"""
        service = SpeedLimitService()
        
        driving_rule = DrivingRuleData(
            frame_id=120,
            tracking_id=5,
            rule="STOP",
            message="Stop sign"
        )
        
        state = service.process_driving_rule(driving_rule)
        
        # Non-speed rule returns None
        assert state is None


# ============================================================================
# TV4 TESTS
# ============================================================================

class TestWarningDecisionService:
    """Test TV4 - Traffic Warning Decision"""
    
    def test_process_no_entry_rule(self):
        """Test quyết định NO_ENTRY rule"""
        service = WarningDecisionService()
        
        driving_rule = DrivingRuleData(
            frame_id=120,
            tracking_id=5,
            rule="NO_ENTRY",
            message="Cam di nguoc chieu"
        )
        
        warning = service.process_driving_rule(driving_rule)
        
        assert warning is not None
        assert warning.type == "NO_ENTRY"
        assert warning.level == PriorityLevel.HIGH
        assert warning.priority == 90
    
    def test_process_speed_limit_rule(self):
        """Test speed limit rule (không sinh warning)"""
        service = WarningDecisionService()
        
        driving_rule = DrivingRuleData(
            frame_id=120,
            tracking_id=5,
            rule="SET_SPEED_LIMIT",
            speed_limit=50,
            message="Gioi han toc do 50kmh"
        )
        
        warning = service.process_driving_rule(driving_rule)
        
        # Speed limit rule should not generate warning
        assert warning is None


# ============================================================================
# TV5 TESTS
# ============================================================================

class TestWarningManager:
    """Test TV5 - Warning Manager"""
    
    def test_enqueue_warning(self):
        """Test thêm warning vào queue"""
        manager = WarningManager()
        
        warning = TrafficWarning(
            warning_id="test_001",
            type="NO_ENTRY",
            level=PriorityLevel.HIGH,
            message="Cam di nguoc chieu",
            priority=90,
            duration=5
        )
        
        event = manager.process_warning(warning)
        
        assert event is not None
        assert event.status == "PENDING"
    
    def test_duplicate_filter(self):
        """Test duplicate filter"""
        manager = WarningManager()
        
        warning = TrafficWarning(
            warning_id="test_001",
            type="NO_ENTRY",
            level=PriorityLevel.HIGH,
            message="Cam di nguoc chieu",
            priority=90,
            duration=5
        )
        
        # First warning accepted
        event1 = manager.process_warning(warning)
        assert event1 is not None
        
        # Immediate duplicate rejected
        event2 = manager.process_warning(warning)
        assert event2 is None  # Duplicate filtered
    
    def test_get_next_warning(self):
        """Test lấy warning tiếp theo"""
        manager = WarningManager()
        
        warning = TrafficWarning(
            warning_id="test_001",
            type="NO_ENTRY",
            level=PriorityLevel.HIGH,
            message="Cam di nguoc chieu",
            priority=90,
            duration=5
        )
        
        manager.process_warning(warning)
        event = manager.get_next_warning()
        
        assert event is not None
        assert event.status == "ACTIVE"


# ============================================================================
# Integration Tests
# ============================================================================

class TestFullPipeline:
    """Test toàn bộ pipeline TV1 → TV5"""
    
    def test_full_pipeline(self):
        """Test toàn bộ pipeline"""
        # TV1
        tv1_service = SignInputService(confidence_threshold=0.5)
        raw_detection = {
            "class_id": 38,
            "confidence": 0.95,
            "bbox": [150, 80, 240, 190]
        }
        tv1_result = tv1_service.process_detection(raw_detection, 120, 5)
        assert tv1_result is not None
        
        # TV2 (simulated)
        tv2_rule = DrivingRuleData(
            frame_id=120,
            tracking_id=5,
            rule="NO_ENTRY",
            message="Cam di nguoc chieu"
        )
        
        # TV3
        tv3_service = SpeedLimitService()
        tv3_state = tv3_service.get_current_state()
        
        # TV4
        tv4_service = WarningDecisionService()
        tv4_warning = tv4_service.process_driving_rule(tv2_rule, tv3_state)
        assert tv4_warning is not None
        
        # TV5
        tv5_manager = WarningManager()
        tv5_event = tv5_manager.process_warning(tv4_warning)
        assert tv5_event is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
