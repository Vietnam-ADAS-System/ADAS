"""
Data Models cho toàn bộ Traffic Sign Warning Module
Sử dụng Pydantic để validate tất cả dữ liệu
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Literal
from enum import Enum


# ============================================================================
# TV1 - TRAFFIC SIGN RECOGNITION INPUT MODELS
# ============================================================================

class BoundingBox(BaseModel):
    """Bounding Box của biển báo trên frame"""
    x1: float = Field(..., description="Top-left x coordinate")
    y1: float = Field(..., description="Top-left y coordinate")
    x2: float = Field(..., description="Bottom-right x coordinate")
    y2: float = Field(..., description="Bottom-right y coordinate")
    
    @validator('x1', 'y1', 'x2', 'y2')
    def validate_coordinates(cls, v):
        if v < 0:
            raise ValueError("Coordinates phải >= 0")
        return v


class DetectionResult(BaseModel):
    """Raw detection result từ YOLO"""
    class_id: int = Field(..., description="Traffic sign class ID (0-51)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    
    @validator('class_id')
    def validate_class_id(cls, v):
        if not 0 <= v <= 51:
            raise ValueError("class_id phải nằm trong khoảng 0-51")
        return v


class StandardTrafficSignData(BaseModel):
    """
    TV1 Output - Dữ liệu biển báo giao thông đã chuẩn hóa
    Truyền sang TV2 Rule Engine
    """
    frame_id: int = Field(..., description="Frame ID hiện tại")
    tracking_id: int = Field(..., description="Tracking ID của biển báo")
    class_id: int = Field(..., ge=0, le=51, description="Traffic sign class ID")
    class_name: str = Field(..., description="Tên biển báo (tiếng Việt không dấu)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    bbox: BoundingBox = Field(..., description="Vị trí biển báo trên frame")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "frame_id": 120,
                "tracking_id": 5,
                "class_id": 38,
                "class_name": "Gioi han toc do 50kmh",
                "confidence": 0.95,
                "bbox": {"x1": 150, "y1": 80, "x2": 240, "y2": 190},
                "timestamp": "2026-07-03T10:35:25"
            }
        }


# ============================================================================
# TV2 - RULE ENGINE OUTPUT MODEL
# ============================================================================

class DrivingRuleData(BaseModel):
    """TV2 Output - Luật lái xe được sinh ra từ Rule Engine"""
    frame_id: int = Field(..., description="Frame ID")
    tracking_id: int = Field(..., description="Tracking ID")
    rule: Literal[
        "SET_SPEED_LIMIT",
        "NO_ENTRY",
        "STOP",
        "GIVE_WAY",
        "PEDESTRIAN_CROSSING",
        "SCHOOL_ZONE",
        "BUS_STOP",
        "ROUNDABOUT",
        "PREPARE_TO_STOP"
    ] = Field(..., description="Loại luật lái xe")
    speed_limit: Optional[int] = Field(None, ge=0, le=100, description="Giới hạn tốc độ (km/h)")
    message: str = Field(..., description="Mô tả luật")
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# TV3 - SPEED LIMIT STATE MANAGEMENT MODELS
# ============================================================================

class SpeedLimitState(BaseModel):
    """
    TV3 Output - Trạng thái giới hạn tốc độ hiện hành
    Được đồng bộ lên Dashboard và gửi cho TV4
    """
    frame_id: int = Field(..., description="Frame ID")
    speed_limit: int = Field(..., ge=0, le=100, description="Giới hạn tốc độ hiện hành (km/h)")
    status: Literal["ACTIVE", "INACTIVE", "EXPIRED"] = Field(
        default="ACTIVE", 
        description="Trạng thái của Speed Limit"
    )
    source: str = Field(..., description="Nguồn dữ liệu (Traffic Sign, Default, ...)")
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "frame_id": 120,
                "speed_limit": 50,
                "status": "ACTIVE",
                "source": "Traffic Sign",
                "updated_at": "2026-07-03T10:35:25"
            }
        }


# ============================================================================
# TV4 - TRAFFIC WARNING DECISION MODELS
# ============================================================================

class PriorityLevel(str, Enum):
    """Mức ưu tiên cảnh báo"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TrafficWarning(BaseModel):
    """
    TV4 Output - Cảnh báo giao thông được sinh ra từ Decision Engine
    Truyền sang TV5 Warning Manager
    """
    warning_id: str = Field(..., description="ID duy nhất của cảnh báo")
    type: str = Field(..., description="Loại cảnh báo (NO_ENTRY, STOP, SPEED_LIMIT, ...)")
    level: PriorityLevel = Field(..., description="Mức ưu tiên cảnh báo")
    message: str = Field(..., description="Thông báo cảnh báo (tiếng Việt không dấu)")
    priority: int = Field(..., ge=1, le=100, description="Mức ưu tiên số (1-100)")
    duration: int = Field(..., ge=1, description="Thời gian hiển thị (giây)")
    timestamp: datetime = Field(default_factory=datetime.now)
    expire_time: Optional[datetime] = Field(None, description="Thời gian hết hạn cảnh báo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "warning_id": "warn_001_no_entry",
                "type": "NO_ENTRY",
                "level": "HIGH",
                "message": "Cam di nguoc chieu",
                "priority": 90,
                "duration": 5,
                "timestamp": "2026-07-03T10:35:25",
                "expire_time": "2026-07-03T10:35:30"
            }
        }


# ============================================================================
# TV5 - WARNING MANAGER MODELS
# ============================================================================

class WarningEvent(BaseModel):
    """Sự kiện cảnh báo - dùng để theo dõi lịch sử"""
    event_id: str = Field(..., description="ID sự kiện duy nhất")
    warning: TrafficWarning = Field(..., description="Thông tin cảnh báo")
    status: Literal["PENDING", "ACTIVE", "DISMISSED", "EXPIRED"] = Field(
        default="PENDING",
        description="Trạng thái sự kiện"
    )
    dismissed_at: Optional[datetime] = Field(None, description="Thời gian hủy bỏ")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_001",
                "warning": {},
                "status": "ACTIVE",
                "dismissed_at": None,
                "created_at": "2026-07-03T10:35:25"
            }
        }


class WarningQueueItem(BaseModel):
    """Item trong Warning Queue của Warning Manager"""
    event: WarningEvent
    queued_at: datetime = Field(default_factory=datetime.now)
    is_duplicate: bool = Field(default=False)


class WarningHistory(BaseModel):
    """Lịch sử cảnh báo - dùng để phân tích và debugging"""
    event_id: str
    warning_type: str
    level: PriorityLevel
    message: str
    created_at: datetime
    dismissed_at: Optional[datetime]
    display_duration: int = Field(..., description="Thời gian hiển thị thực tế (giây)")
