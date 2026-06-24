# 3.3 Lane Departure Warning - Cảnh báo chệch làn

> **File:** `backend/ai-service/adas/departure_warning.py`
> **Class:** `LaneDepartureWarning`

---

## 3.3.1 Mục đích

Tính toán vị trí xe so với làn đường và đưa ra cảnh báo khi xe bắt đầu chệch khỏi làn, bao gồm:

- Xác định tâm xe và khoảng cách đến các biên làn
- Tính toán thời gian dự kiến chệch làn (Time-to-Lane-Crossing)
- Đưa ra cảnh báo phù hợp với mức độ nguy hiểm

---

## 3.3.2 Đầu vào (Input)

| Tham số | Kiểu | Mô tả | Ví dụ |
|---------|------|--------|-------|
| `frame` | `numpy.ndarray` | Frame hiện tại | Shape: (H, W, 3) |
| `lane_boundaries` | `dict` | Tọa độ biên làn từ detection/segmentation | `{"left": [...], "right": [...]}` |
| `vehicle_position` | `tuple` | Tọa độ tâm xe (x, y) trong ảnh | (640, 500) |
| `vehicle_width` | `float` | Chiều rộng xe (pixels) | 150 |

---

## 3.3.3 Đầu ra (Output)

```python
{
    "status": str,                    # "SAFE" | "WARNING" | "ALERT"
    "distance_to_left": float,        # Khoảng cách đến biên trái (pixels)
    "distance_to_right": float,      # Khoảng cách đến biên phải (pixels)
    "offset_from_center": float,      # Độ lệch tâm (-1 to 1, âm = trái, dương = phải)
    "ttlc": float,                    # Time-to-Lane-Crossing (seconds)
    "confidence": float,              # Độ tin cậy của prediction
    "warning_level": int,             # 0 (safe), 1 (warning), 2 (alert)
    "processing_time_ms": float
}
```

---

## 3.3.4 Điều kiện tiên quyết

- [ ] Lane boundaries đã được detect từ frame hiện tại
- [ ] Vehicle position đã được xác định
- [ ] Frame rate (FPS) đã được biết để tính TTC

---

## 3.3.5 Luồng xử lý

```
Bước 1: Validate inputs
    │
    ├─ Kiểm tra lane_boundaries không rỗng
    ├─ Kiểm tra vehicle_position trong frame
    └─ Fallback sang default nếu thiếu data
    │
    ▼
Bước 2: Tính toán khoảng cách đến làn đường
    │
    ├─ Xác định đường biên trái (y = f(x))
    ├─ Xác định đường biên phải (y = g(x))
    ├─ Tính khoảng cách từ vehicle_position đến mỗi biên
    │   ├─ Tìm y tương ứng trên đường biên
    │   └─ Tính Euclidean distance
    └─ Tính độ lệch tâm (offset_from_center)
    │
    ▼
Bước 3: Tính Time-to-Lane-Crossing (TTLC)
    │
    ├─ Tính lateral velocity (vận tốc ngang)
    │   └─ = (current_offset - prev_offset) / dt
    ├─ Ước tính TTC = remaining_distance / lateral_velocity
    ├─ Xử lý trường hợp velocity = 0
    └─ Clamp TTC: 0.0 - 10.0 seconds
    │
    ▼
Bước 4: Xác định mức cảnh báo
    │
    ├─ SAFE (level 0):
    │   ├─ offset < threshold_safe (e.g., 0.15)
    │   └─ OR distance > threshold_safe_distance
    │
    ├─ WARNING (level 1):
    │   ├─ offset >= threshold_safe AND offset < threshold_alert
    │   └─ OR TTC < 3.0 seconds
    │
    └─ ALERT (level 2):
        ├─ offset >= threshold_alert (e.g., 0.25)
        ├─ OR TTC < 1.5 seconds
        └─ OR vehicle_position outside lane boundaries
    │
    ▼
Bước 5: Tạo thông báo
    │
    ├─ Tạo warning message dựa trên level
    ├─ Gửi event đến ADAS decision module
    └─ Log warning cho evaluation
```

---

## 3.3.6 Threshold Configuration

```python
THRESHOLDS = {
    "safe_offset": 0.15,           # Độ lệch tâm an toàn (% của lane width)
    "alert_offset": 0.25,          # Độ lệch tâm cảnh báo khẩn
    "safe_distance": 50,           # Khoảng cách an toàn tối thiểu (pixels)
    "warning_ttlc": 3.0,           # TTC để bắt đầu warning (seconds)
    "alert_ttlc": 1.5,             # TTC để alert (seconds)
    "confidence_threshold": 0.6   # Confidence tối thiểu để đưa ra warning
}
```

---

## 3.3.7 Các trường hợp đặc biệt

| Trường hợp | Xử lý |
|------------|-------|
| Không có lane boundaries | Trả về SAFE, log warning |
| Vehicle ở rìa frame | Sử dụng boundary gần nhất |
| TTC âm hoặc vô cùng | Set TTC = 10.0 (max) |
| Confidence thấp | Giảm sensitivity, chỉ alert khi chắc chắn |
| Xe đang đỗ (offset không đổi) | Không tính TTC, chỉ dùng offset |

---

## 3.3.8 Thông báo/Kết quả trả về

| Trạng thái | Mã | Message | Chiến lược |
|------------|-----|---------|-----------|
| SAFE | `200` | "Lane keeping OK" | Không hành động |
| WARNING | `201` | "Approaching lane boundary" | Visual alert + Sound nhẹ |
| ALERT | `202` | "LANE DEPARTURE!" | Visual alert + Sound khẩn + Haptic |

---

## 3.3.9 Hàm/Module liên quan

| Module | Đường dẫn | Mô tả |
|--------|-----------|-------|
| `LaneDetector` | `traditional_cv/lane_detection/` | Cung cấp lane boundaries |
| `LaneSegmenter` | `ai_models/lane_segmentation/` | Cung cấp lane mask |
| `ADASAlertManager` | `adas/alert_manager.py` | Quản lý và phát alert |
| `PositionTracker` | `tracking/vehicle_tracker.py` | Theo dõi vị trí xe |

---

## 3.3.10 Ví dụ

**Input:**
```python
frame = cv2.imread("frame.jpg")
lane_boundaries = {
    "left": [(250, 720), (280, 600), (320, 480)],
    "right": [(1030, 720), (1000, 600), (960, 480)]
}
vehicle_position = (640, 500)  # Tâm xe
vehicle_width = 150
prev_offset = 0.02
current_offset = 0.18  # Độ lệch 18%
dt = 1/30  # 30 FPS
```

**Output:**
```python
{
    "status": "WARNING",
    "distance_to_left": 35.2,
    "distance_to_right": 365.8,
    "offset_from_center": 0.18,
    "ttlc": 2.8,
    "confidence": 0.87,
    "warning_level": 1,
    "processing_time_ms": 2.3
}
```

---

## 3.3.11 Ghi chú

- **TTLC sensitivity:** Nên có config cho driver adjust (conservative/normal/aggressive)
- **False positive:** Cần tuning threshold để tránh quá nhiều cảnh báo giả
- **Cross-market:** Các thị trường có luật giao thông khác nhau về làn đường

---

## 3.3.12 Checklist

```markdown
## Core Logic
- [ ] Tạo class `LaneDepartureWarning`
- [ ] Implement `calculate_distance_to_boundaries()` method
- [ ] Implement `calculate_offset_from_center()` method
- [ ] Implement `calculate_ttlc()` method
- [ ] Implement `determine_warning_level()` method

## Alert System
- [ ] Implement `generate_warning_message()` method
- [ ] Implement `get_alert_strategy(level)` method
- [ ] Kết nối với `ADASAlertManager`

## Configuration
- [ ] Tạo config file cho thresholds
- [ ] Implement config validation
- [ ] Support runtime threshold adjustment

## State Management
- [ ] Lưu trữ previous offset cho TTC calculation
- [ ] Implement moving average cho offset smoothing
- [ ] Handle state reset khi restart

## Testing
- [ ] Unit tests cho từng calculation method
- [ ] Test với các edge cases
- [ ] Test với synthetic video (đường thẳng, cong, giao lộ)
- [ ] User acceptance test (tuning thresholds)
```

---

## Related

- [1-overview.md](./1-overview.md) - Tổng quan
- [8-checklist.md](./8-checklist.md) - Checklist tổng hợp

---

**Section:** 3.3. Lane Departure Warning
