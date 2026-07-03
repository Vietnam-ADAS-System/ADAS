# Phát hiện và cảnh báo xe lệch làn

**Ngày cập nhật:** 2026-07-03  
**Module:** Lane Departure Warning (LDW)  
**Phạm vi:** Nhận dữ liệu từ Fusion, validate dữ liệu, tính offset, phân loại trạng thái làn, sinh cảnh báo và hiển thị lên dashboard/video.

---

## 1. Mục tiêu

Module Lane Departure Warning được triển khai như một phần của tầng ADAS. Module này không trực tiếp chạy YOLO, DeepLab, Lane Segmentation hoặc DeepSORT. LDW chỉ đọc dữ liệu đã được chuẩn hóa bởi Fusion trong `SceneContext`.

Mục tiêu chính:

- Nhận `vehicle_center`, `lane_left`, `lane_right`, `lane_center`, `track_id` từ Fusion.
- Kiểm tra dữ liệu đầu vào để tránh crash khi thiếu lane/tracking/center.
- Tính `offset = vehicle_center_x - lane_center`.
- Tính `normalized_offset = offset / lane_width`.
- Xác định hướng lệch `LEFT`, `RIGHT`, `CENTER`.
- Phân loại trạng thái `SAFE`, `NEAR_BOUNDARY`, `LEFT_LANE_DEPARTURE`, `RIGHT_LANE_DEPARTURE`, `LANE_UNKNOWN`.
- Sinh cảnh báo ADAS và dữ liệu JSON cho dashboard.
- Vẽ trạng thái LDW lên ảnh/video trong Streamlit demo.

---

## 2. Đảm bảo sử dụng model best.pt

Pipeline demo trong `main.py` vẫn sử dụng đúng các file trọng số đã train sẵn:

```python
MODEL_PATHS = {
    "pedestrian": AI_SERVICE_ROOT / "ai_models" / "pedestrian_detection" / "pedestrian_runs" / "pedestrian" / "walking_v1" / "weights" / "best.pt",
    "vehicle": AI_SERVICE_ROOT / "ai_models" / "vehicle_detection" / "weights" / "best.pt",
    "lane_detection": AI_SERVICE_ROOT / "ai_models" / "lane_detection" / "weights" / "best.pt",
    "lane_segmentation": AI_SERVICE_ROOT / "ai_models" / "lane_segmentation" / "weights" / "best.pt",
    "traffic_sign": AI_SERVICE_ROOT / "ai_models" / "traffic_sign_detection" / "traffic_sign_runs_new" / "traffic_sign_52classes" / "weights" / "best.pt",
}
```

Đã kiểm tra các đường dẫn trên đều tồn tại trong workspace. LDW không tự load các model này; LDW nhận kết quả sau khi các model đã chạy qua pipeline AI và Fusion. Như vậy module tuân thủ đúng nguyên tắc:

- AI layer dùng model `best.pt`.
- Fusion chuẩn hóa dữ liệu.
- LDW/ADAS chỉ xử lý decision logic.

---

## 3. Luồng xử lý hiện tại

```text
Frame / Video
      |
      v
Vehicle Detection best.pt
Lane Detection best.pt
Lane Segmentation best.pt
DeepSORT Tracking
      |
      v
FusionEngine.build_scene_context()
      |
      v
SceneContext
      |
      v
LaneDepartureService
      |
      v
ADASDecisionEngine
      |
      v
Dashboard / Video Overlay
```

---

## 4. Dữ liệu Fusion cung cấp cho LDW

Fusion đã được bổ sung để mỗi vehicle trong `SceneContext` có thêm lane geometry:

```json
{
    "track_id": 5,
    "type": "car",
    "lane": "right",
    "lane_status": "inside_lane",
    "offset": 30,
    "center": [350, 420],
    "lane_left": 250,
    "lane_right": 450,
    "lane_center": 320,
    "speed": null,
    "tracking": true
}
```

Các trường LDW sử dụng:

| Trường | Vai trò |
|---|---|
| `track_id` | ID theo dõi của xe |
| `center` | Tâm xe |
| `lane_left` | Biên trái làn |
| `lane_right` | Biên phải làn |
| `lane_center` | Tâm làn |
| `lane_status` | Trạng thái sơ bộ từ Fusion |

---

## 5. Kiến trúc module LDW

Module được đặt tại:

```text
backend/ai-service/adas/lane_departure/
```

Các file chính:

| File | Chức năng |
|---|---|
| `config.py` | Threshold SAFE/WARNING, min lane width |
| `models.py` | FrameData, ValidatedFrameData, OffsetData, LaneDepartureResult |
| `validator.py` | Điều phối validation |
| `vehicle_validator.py` | Kiểm tra vehicle center |
| `lane_validator.py` | Kiểm tra lane_left/right/center |
| `tracking_validator.py` | Kiểm tra tracking_id |
| `frame_validator.py` | Kiểm tra frame_id |
| `lane_width.py` | Tính lane width |
| `lane_center.py` | Tính lane center khi cần |
| `lane_offset.py` | Tính offset |
| `direction.py` | Xác định LEFT/RIGHT/CENTER |
| `normalize_offset.py` | Chuẩn hóa offset theo lane width |
| `offset_service.py` | Sinh OffsetData |
| `lane_status.py` | Phân loại SAFE/NEAR/DEPARTURE |
| `warning_engine.py` | Quyết định warning true/false |
| `lane_warning.py` | Sinh Warning object cho ADAS |
| `lane_visualizer.py` | Vẽ trạng thái LDW lên frame |
| `dashboard_sender.py` | Chuẩn bị payload dashboard |
| `lane_departure_service.py` | Controller chính của LDW |

---

## 6. Validation fail-safe

LDW không tính toán ngay khi nhận dữ liệu. Dữ liệu phải đi qua `LaneDepartureValidator`.

Các lỗi được xử lý an toàn:

- Thiếu `vehicle_center`.
- Tọa độ center nằm ngoài frame.
- Thiếu `lane_left` hoặc `lane_right`.
- `lane_left >= lane_right`.
- Lane width nhỏ hơn `min_lane_width_px`.
- Thiếu `lane_center`.
- `lane_center` nằm ngoài biên lane.
- Thiếu `tracking_id` nếu cấu hình yêu cầu tracking bắt buộc.

Nếu lỗi xảy ra, LDW trả:

```json
{
    "status": "LANE_UNKNOWN",
    "warning": false,
    "errors": [...]
}
```

Nhờ vậy pipeline không crash khi lane/tracking bị mất.

---

## 7. Logic tính toán

### 7.1 Lane width

```text
lane_width = lane_right - lane_left
```

### 7.2 Offset

```text
offset = vehicle_center_x - lane_center
```

### 7.3 Direction

| Điều kiện | Direction |
|---|---|
| `offset < 0` | `LEFT` |
| `offset = 0` | `CENTER` |
| `offset > 0` | `RIGHT` |

### 7.4 Normalized offset

```text
normalized_offset = offset / lane_width
```

Việc dùng normalized offset giúp LDW ổn định hơn khi độ phân giải video thay đổi.

---

## 8. Logic phân loại trạng thái

Cấu hình mặc định:

| Tham số | Giá trị |
|---|---|
| `safe_threshold_ratio` | `0.10` |
| `warning_threshold_ratio` | `0.22` |
| `fallback_warning_threshold_px` | `70 px` |
| `min_lane_width_px` | `40 px` |

Quy tắc:

| Điều kiện | Status | Warning |
|---|---|---|
| `abs(normalized_offset) < 0.10` | `SAFE` | `false` |
| `0.10 <= abs(normalized_offset) < 0.22` | `NEAR_BOUNDARY` | `false` |
| `abs(normalized_offset) >= 0.22` và direction LEFT | `LEFT_LANE_DEPARTURE` | `true` |
| `abs(normalized_offset) >= 0.22` và direction RIGHT | `RIGHT_LANE_DEPARTURE` | `true` |
| Lane invalid | `LANE_UNKNOWN` | `false` |

Nếu Fusion đã xác định `lane_status` là `crossing_lane` hoặc `outside_lane`, LDW ưu tiên phân loại thành lane departure theo hướng offset.

---

## 9. Output JSON

`ADASDecisionEngine.evaluate()` hiện trả thêm trường `lane_departure`:

```json
{
    "frame": 152,
    "warnings": [
        {
            "type": "Right Lane Departure",
            "priority": "HIGH",
            "message": "Vehicle is departing to the right lane boundary",
            "track_id": 5
        }
    ],
    "lane_departure": [
        {
            "vehicle_id": 5,
            "tracking_id": 5,
            "frame_id": 152,
            "offset": 80,
            "normalized_offset": 0.4,
            "direction": "RIGHT",
            "status": "RIGHT_LANE_DEPARTURE",
            "warning": true
        }
    ]
}
```

---

## 10. Tích hợp Dashboard / Video

Trong `main.py`, sau khi ADAS tạo output:

```python
output = draw_lane_departure_overlay(
    output,
    adas_output_dict.get("lane_departure", []),
)
```

Hàm này vẽ:

- Tâm xe.
- Đường lane center.
- Nhãn `LDW: SAFE`, `LDW: NEAR_BOUNDARY`, `LDW: LEFT_LANE_DEPARTURE`, `LDW: RIGHT_LANE_DEPARTURE`.
- Cảnh báo đỏ khi xe lệch làn.

Streamlit cũng hiển thị JSON trong expander:

```text
Scene Context / ADAS Output
```

---

## 11. File đã thay đổi / thêm mới

### Fusion

- `backend/ai-service/fusion/data_models.py`
- `backend/ai-service/fusion/vehicle_lane_fusion.py`
- `backend/ai-service/fusion/scene_understanding.py`

### ADAS LDW

- `backend/ai-service/adas/lane_departure/`
- `backend/ai-service/adas/config.py`
- `backend/ai-service/adas/data_models.py`
- `backend/ai-service/adas/decision_engine.py`

### Demo

- `main.py`

---

## 12. Kết quả hiện tại

| Tiêu chí | Trạng thái |
|---|---|
| Dùng đúng model `best.pt` trong `MODEL_PATHS` | Hoàn thành |
| LDW chỉ nhận dữ liệu từ Fusion | Hoàn thành |
| Validate input | Hoàn thành |
| Tính lane width | Hoàn thành |
| Tính offset | Hoàn thành |
| Tính normalized offset | Hoàn thành |
| Xác định direction | Hoàn thành |
| Phân loại SAFE / NEAR / DEPARTURE | Hoàn thành |
| Sinh cảnh báo | Hoàn thành |
| Output JSON dashboard | Hoàn thành |
| Vẽ lên video/frame | Hoàn thành |
| Không crash khi thiếu lane/tracking | Hoàn thành theo logic fail-safe |

Kiểm tra kỹ thuật đã chạy:

- `python -m py_compile` cho `main.py`, Fusion và toàn bộ package `adas/lane_departure/`: đạt.
- Test logic LDW mẫu: `SAFE`, `NEAR_BOUNDARY`, `LEFT_LANE_DEPARTURE`, `RIGHT_LANE_DEPARTURE`, `LANE_UNKNOWN`: đạt.
- Test tích hợp `FusionEngine -> ADASDecisionEngine`: sinh `SceneContext` có lane geometry và output `RIGHT_LANE_DEPARTURE` đúng logic.

---

## 13. Ghi chú còn cần kiểm thử thêm

Phần code đã hoàn thành theo kiến trúc, nhưng để kết luận chất lượng thực tế cần chạy thêm:

- Video nhiều làn.
- Video đường cong.
- Video ban đêm.
- Video mất lane mask tạm thời.
- Video nhiều xe chồng lấp.
- Đo FPS thực tế khi bật đủ module.

Các bài test này phụ thuộc vào dữ liệu đầu vào và phần cứng chạy demo.
