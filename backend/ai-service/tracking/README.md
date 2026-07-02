# Tracking Module — DeepSORT Implementation

## Mục Đích

Module này triển khai **DeepSORT** (Deep Simple Online and Realtime Tracking) để theo dõi các đối tượng (xe, người đi bộ) qua nhiều frame video, gán ID ổn định cho mỗi đối tượng.

**Nhu cầu**: Module Fusion cần biết "cùng 1 xe/người ở frame N và frame N+1 có phải là object giống nhau không" — nếu chỉ chạy detection độc lập mỗi frame, ID sẽ nhảy liên tục. Tracking giải quyết vấn đề này.

---

## Kiến Trúc

### Classes

#### **`Track` (Dataclass)**

Đại diện cho một track (đối tượng đã xác nhận theo dõi).

```python
@dataclass
class Track:
    track_id: int                # ID duy nhất (ổn định qua các frame)
    class_name: str              # "vehicle" hoặc "pedestrian"
    bbox: List[float]            # [x1, y1, x2, y2]
    confidence: float            # Confidence score từ detection
    frame_count: int             # Số frame track này đã xuất hiện
    time_since_update: int       # Frame kể từ lần cuối update
    
    def to_dict(self) -> Dict:
        # Chuyển thành dict format (for JSON/API)
        return {
            "track_id": ...,
            "class_name": ...,
            "bbox": {"x1": ..., "y1": ..., "x2": ..., "y2": ..., "width": ..., "height": ...},
            "confidence": ...,
            "frame_count": ...,
            "time_since_update": ...,
        }
```

#### **`TrackerConfig` (Dataclass)**

Cấu hình cho tracker.

```python
@dataclass
class TrackerConfig:
    max_age: int = 30                        # Số frame giữ track khi mất detection
    n_init: int = 3                          # Số frame liên tiếp cần detect để confirm track mới
    max_cosine_distance: float = 0.5         # Ngưỡng matching appearance (feature similarity)
    use_separate_trackers: bool = True       # Dùng tracker riêng cho vehicle vs pedestrian
    min_confidence: float = 0.3              # Ngưỡng confidence tối thiểu để track
```

#### **`ObjectTracker` (Main Class)**

Tracker chính — quản lý toàn bộ tracking logic.

**Constructor:**
```python
tracker = ObjectTracker(config=TrackerConfig(max_age=30, n_init=3))
```

**Main Method — `update()`:**
```python
tracks = tracker.update(
    vehicle_detections=vehicle_detector_output,  # Dict từ VehicleObjectDetector.detect_frame()
    pedestrian_detections=pedestrian_detector_output,  # List[Dict] từ PedestrianDetector.detect()
    frame=frame  # np.ndarray (BGR), optional
)
# Returns: List[Track]
```

**Các method khác:**
- `get_active_tracks()` → List[Track] của toàn bộ active tracks hiện tại
- `reset()` → Xoá toàn bộ active tracks (khi chuyển video mới)
- `get_stats()` → Dict với thống kê (frame_count, active_track_count, ...)

---

## Cách Sử Dụng

### 1. Import và Khởi Tạo

```python
from tracking import ObjectTracker, TrackerConfig

# Cấu hình (tuỳ chọn)
config = TrackerConfig(
    max_age=30,           # Giữ track 30 frame nếu mất detection
    n_init=3,             # Cần 3 frame liên tiếp detect mới confirm
    max_cosine_distance=0.5,  # Ngưỡng feature similarity
)

# Khởi tạo tracker
tracker = ObjectTracker(config=config)
```

### 2. Trong vòng lặp xử lý video

```python
import cv2
from ai_models.vehicle_detection.vehicle_detector import VehicleObjectDetector
from ai_models.pedestrian_detection.detector import PedestrianDetector

# Khởi tạo detectors
vehicle_detector = VehicleObjectDetector()
pedestrian_detector = PedestrianDetector()

# Đọc video
cap = cv2.VideoCapture("input_video.mp4")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 1. Detection
    vehicle_dets = vehicle_detector.detect_frame(frame)
    pedestrian_dets = pedestrian_detector.detect(frame)
    
    # 2. Tracking
    tracks = tracker.update(
        vehicle_detections=vehicle_dets,
        pedestrian_detections=pedestrian_dets,
        frame=frame
    )
    
    # 3. Sử dụng tracks (vẽ, xử lý, gửi đến Fusion, ...)
    for track in tracks:
        print(f"ID {track.track_id}: {track.class_name} @ {track.bbox}")
        
        # Vẽ lên frame
        x1, y1, x2, y2 = int(track.bbox[0]), int(track.bbox[1]), int(track.bbox[2]), int(track.bbox[3])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"ID:{track.track_id}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

cap.release()
```

### 3. Các điểm quan trọng

**Normalize Detector Output:**
- Tracker tự động normalize 2 format detection khác nhau (vehicle vs pedestrian) — không cần xử lý trước.

**Tracker độc lập với detector:**
- Có thể gọi `tracker.update()` với chỉ vehicle hoặc chỉ pedestrian detections (không bắt buộc cả 2).
- Có thể gọi với `frame=None` (sẽ dùng IoU matching thay vì appearance matching, nhưng performance kém hơn).

**Active Tracks:**
- `tracks` được return chỉ gồm **confirmed tracks** (đã xuất hiện ≥ n_init frame).
- Nếu cần toàn bộ tracks (kể cả tentative), dùng `tracker.get_active_tracks()`.

**Reset khi video mới:**
```python
tracker.reset()  # Xoá toàn bộ active tracks khi chuyển video khác
```

---

## Output Format

Mỗi `Track` được return có structure:

```python
Track(
    track_id=1,                          # ID duy nhất
    class_name="vehicle",                # hoặc "pedestrian"
    bbox=[x1, y1, x2, y2],              # Tọa độ (pixel)
    confidence=0.85,
    frame_count=10,                      # Đã track 10 frame
    time_since_update=0                  # Vừa được update
)

# Hoặc convert thành dict (for JSON)
track.to_dict()
# {
#     "track_id": 1,
#     "class_name": "vehicle",
#     "bbox": {"x1": ..., "y1": ..., "x2": ..., "y2": ..., "width": ..., "height": ...},
#     "confidence": 0.85,
#     "frame_count": 10,
#     "time_since_update": 0
# }
```

---

## Dependencies

- `deep-sort-realtime>=1.3.0` (sẽ tự động download pre-trained feature extractor)
- `opencv-python>=4.10.0`
- `numpy>=1.24.0`
- `torch` (từ ultralytics, nếu dùng GPU)

**Cài đặt:**
```bash
pip install -r backend/ai-service/requirements.txt
```

---

## Configuration Examples

### Example 1: Tracking ổn định cho video độ phân giải cao (nhiều chi tiết)

```python
config = TrackerConfig(
    max_age=50,                # Giữ lâu hơn (có thể che khuất lâu)
    n_init=5,                  # Confirm chậm hơn (tránh false track)
    max_cosine_distance=0.6,   # Flexible hơn (màn chắn tạm thời)
)
```

### Example 2: Tracking nhanh cho video thấp (real-time webcam)

```python
config = TrackerConfig(
    max_age=15,                # Xoá track nhanh
    n_init=2,                  # Confirm nhanh
    max_cosine_distance=0.4,   # Strict (ít nhầm lẫn ID)
)
```

---

## Performance Notes

- **Latency**: Tracking thêm ~10-30ms per frame (so với detection thuần) tùy vào số object.
- **FPS**: Nếu detection là 30 FPS, tracking thêm → ~25-28 FPS tùy cấu hình.
- **Memory**: Giữ feature vectors → ~100MB cho ~100 active tracks.

---

## Known Limitations

1. **Feature Extractor Pre-trained trên COCO**: DeepSORT dùng OSNet pre-trained trên COCO — performance tốt cho vehicle/pedestrian chung, nhưng có thể không tối ưu nếu style đối tượng rất khác (ví dụ xe màu rất sáng, người mặc quần áo có pattern).
2. **Tracking Loss khi object che khuất**: Nếu object bị che khuất lâu hơn `max_age` frame, sẽ bị xoá track.
3. **Identity Switch**: Khi 2 object gần nhau / chuyển động cắt ngang nhau, có thể bị swap ID tạm thời.

---

## Testing

Chạy demo script để test:

```bash
cd backend/ai-service
python tracking/demo.py
```

Kết quả:
- Xuất video output: `outputs/videos/demo_tracked.mp4`
- In ra FPS, số unique tracks, ...
- Có thể kiểm tra bằng mắt ID có ổn định không qua các frame.

---

## Integration with Fusion

**Fusion Module** sẽ tiêu thụ output tracking:

```python
# Input từ tracking
tracks = [
    Track(track_id=1, class_name="vehicle", bbox=[...], ...),
    Track(track_id=2, class_name="pedestrian", bbox=[...], ...),
]

# Fusion có thể:
# - Kết hợp vehicle + pedestrian tracks theo logic spatial/temporal
# - Detect collision/intersection giữa các track
# - Gửi alert đến Dashboard
```

Output format của tracking được thiết kế để dễ tiêu thụ bởi Fusion → không cần chuyển đổi format khác.

---

## Troubleshooting

### Q: Tracker không load model
```
RuntimeError: DeepSORT not installed...
```
**A**: Cài đặt deep-sort-realtime: `pip install deep-sort-realtime`

### Q: Identity Switch quá nhiều
**A**: Tăng `max_cosine_distance` (flexible hơn) hoặc giảm `n_init` (confirm nhanh hơn, nhưng risk false tracking).

### Q: Tracking quá chậm
**A**: Giảm độ phân giải video hoặc tăng `max_age` nếu có thể.

### Q: Track bị xoá quá nhanh (object mất ID sau vài frame)
**A**: Tăng `max_age` (ví dụ từ 30 → 50).

---

## Future Improvements

- [ ] Multi-class tracking (vehicle, pedestrian, traffic_sign, ...)
- [ ] Kalman filter tuning cho motion prediction (hiện DeepSORT đã có built-in)
- [ ] Custom feature extractor re-trained trên ADAS dataset
- [ ] Tracking loss detection & auto-alert
