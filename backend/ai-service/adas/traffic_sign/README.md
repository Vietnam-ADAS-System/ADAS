# Traffic Sign Warning Module - Implementation Guide

## 📁 Cấu trúc Thư Mục

```
adas/traffic_sign/
├── __init__.py                  # Module exports
├── config.py                    # Config loader (YAML + Python)
├── models.py                    # Pydantic models cho tất cả modules
├── traffic_sign_config.yaml     # Configuration file
│
├── # TV1 - Traffic Sign Recognition Input (Đọc detection)
├── class_mapper.py              # Mapping 52 classes
├── sign_reader.py               # Đọc raw detection từ YOLO
├── confidence_filter.py          # Lọc confidence threshold
├── bbox_parser.py               # Parse bounding box
├── sign_input_service.py        # TV1 Main service (điều phối)
│
├── # TV3 - Speed Limit State Management (Quản lý tốc độ)
├── speed_rule_parser.py         # Parse DrivingRuleData
├── speed_limit_manager.py       # Quản lý current speed limit
├── dashboard_sender.py          # Đồng bộ dashboard
├── speed_limit_service.py       # TV3 Main service
│
├── # TV4 - Traffic Warning Decision (Quyết định cảnh báo)
├── warning_decision.py          # Decision engine
├── priority_manager.py          # Xếp mức ưu tiên
├── warning_timer.py             # Quản lý timer/timeout
├── warning_service.py           # TV4 Main service
│
└── # TV5 - Warning Manager (Quản lý cảnh báo)
    ├── warning_queue.py         # Quản lý queue
    ├── warning_history.py       # Lưu lịch sử
    └── warning_manager.py       # TV5 Main service
```

---

## 🔄 Luồng Xử Lý (Pipeline)

### TV1: Traffic Sign Recognition Input
```
Raw YOLO Detection
    ↓ (sign_reader.py)
Validate & Parse Detection
    ↓ (confidence_filter.py)
Filter by Confidence (0.5 default)
    ↓ (class_mapper.py)
Map Class ID → Class Name
    ↓ (bbox_parser.py)
Parse & Validate Bounding Box
    ↓ (sign_input_service.py)
StandardTrafficSignData
    ↓ → TV2 (Rule Engine)
```

**Input:**
```python
{
    "class_id": 38,
    "confidence": 0.95,
    "bbox": [150, 80, 240, 190]
}
```

**Output:**
```python
StandardTrafficSignData(
    frame_id=120,
    tracking_id=5,
    class_id=38,
    class_name="Gioi han toc do 50kmh",
    confidence=0.95,
    bbox=BoundingBox(x1=150, y1=80, x2=240, y2=190)
)
```

---

### TV3: Speed Limit State Management
```
DrivingRuleData (from TV2)
    ↓ (speed_rule_parser.py)
Extract Speed Limit Value
    ↓ (speed_limit_manager.py)
Update Current Speed Limit
    ↓ (dashboard_sender.py)
Send to Dashboard
    ↓
SpeedLimitState
    ├── → Dashboard (display)
    └── → TV4 (context)
```

**Config:**
```yaml
tv3:
  default_speed_limit: 40
  speed_limit_duration: 30
```

---

### TV4: Traffic Warning Decision Engine
```
DrivingRuleData (from TV2) + SpeedLimitState (from TV3)
    ↓ (warning_decision.py)
Evaluate Rule → Decision
    ↓ (priority_manager.py)
Assign Priority (1-100) & Level
    ↓ (warning_timer.py)
Start Timer (duration from config)
    ↓
TrafficWarning
    ↓ → TV5 (Warning Manager)
```

**Priority Rules (from config):**
- NO_ENTRY: HIGH (90)
- STOP: HIGH (95)
- SPEED_LIMIT: No warning
- PEDESTRIAN_CROSSING: HIGH (85)
- SCHOOL_ZONE: MEDIUM (65)

---

### TV5: Warning Manager
```
TrafficWarning (from TV4)
    ↓ (warning_manager.py)
Duplicate Filter (2s window)
    ↓ (warning_queue.py)
Enqueue to Warning Queue
    ↓
Get Next Warning
    ↓ (warning_history.py)
Log to History
    ↓
Display on Dashboard / Voice Alert
    ↓
Dismiss / Expire
    ↓ (warning_history.py)
Record in History
```

---

## 📦 Sử Dụng Module

### TV1 - Nhận Detection
```python
from adas.traffic_sign import SignInputService

service = SignInputService(confidence_threshold=0.5)

# Xử lý một detection
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
# result: StandardTrafficSignData
```

### TV3 - Quản Lý Speed Limit
```python
from adas.traffic_sign import SpeedLimitService
from models import DrivingRuleData

service = SpeedLimitService()

# Xử lý driving rule từ TV2
driving_rule = DrivingRuleData(
    frame_id=120,
    tracking_id=5,
    rule="SET_SPEED_LIMIT",
    speed_limit=50,
    message="Gioi han toc do 50kmh"
)

state = service.process_driving_rule(driving_rule)
# state: SpeedLimitState
```

### TV4 - Quyết Định Warning
```python
from adas.traffic_sign import WarningDecisionService

service = WarningDecisionService()

# Xử lý driving rule
warning = service.process_driving_rule(
    driving_rule=driving_rule,
    speed_limit_state=speed_state  # từ TV3
)
# warning: TrafficWarning
```

### TV5 - Quản Lý Warning
```python
from adas.traffic_sign import WarningManager

manager = WarningManager()

# Thêm warning vào queue
event = manager.process_warning(warning)

# Lấy warning tiếp theo để hiển thị
current_event = manager.get_next_warning()

# Hủy warning hiện tại
manager.dismiss_current_warning()

# Lấy thống kê
status = manager.get_manager_status()
```

---

## ⚙️ Configuration (traffic_sign_config.yaml)

```yaml
tv1:
  confidence_threshold: 0.5
  max_class_id: 51

tv3:
  default_speed_limit: 40
  speed_limit_duration: 30

tv4:
  warning_priority_rules:
    NO_ENTRY:
      level: "HIGH"
      priority: 90
      duration: 5
    STOP:
      level: "HIGH"
      priority: 95
      duration: 3

tv5:
  warning_queue_size: 10
  duplicate_filter_time: 2
  history_max_records: 100
```

---

## 📊 Data Models (Pydantic)

### Toàn bộ models được định nghĩa trong `models.py`:

1. **TV1**: `StandardTrafficSignData`, `DetectionResult`, `BoundingBox`
2. **TV2**: `DrivingRuleData` (được định nghĩa trong `models.py`)
3. **TV3**: `SpeedLimitState`
4. **TV4**: `TrafficWarning`, `PriorityLevel`
5. **TV5**: `WarningEvent`, `WarningQueueItem`, `WarningHistory`

Tất cả models đều sử dụng **Pydantic** để validate dữ liệu.

---

## ✅ Testing & Verification

Mỗi module đều có:
- Input validation
- Error handling
- Status tracking
- History logging
- Statistics gathering

Ví dụ:
```python
# TV1 stats
stats = sign_service.get_processing_stats()

# TV3 status
status = speed_service.get_service_status()

# TV4 status
status = warning_service.get_service_status()

# TV5 status
status = manager.get_manager_status()
```

---

## 🎯 Key Features

✅ **TV1**: Đọc detection, lọc confidence, mapping class, chuẩn hóa data  
✅ **TV3**: Quản lý speed limit, đồng bộ dashboard, timeout handling  
✅ **TV4**: Decision engine, priority management, warning timer  
✅ **TV5**: Queue management, duplicate filtering, history logging  

📝 Tất cả file đều có docstring chi tiết  
🔧 Configuration qua YAML  
✔️ Type hints & Pydantic validation  
📊 Statistics & logging cho mỗi module  

---

## 📌 Bước Tiếp Theo

1. **Unit Tests**: Viết test cho mỗi module
2. **Integration Tests**: Test luồng TV1 → TV2 → TV3 → TV4 → TV5
3. **API Layer**: Tạo FastAPI endpoints
4. **Dashboard Integration**: Kết nối với dashboard
5. **Voice Alert**: Implement phát cảnh báo giọng nói
