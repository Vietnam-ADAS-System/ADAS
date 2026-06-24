# 3.1 Lane Detection - Nhận diện làn đường

> **File:** `backend/ai-service/traditional_cv/lane_detection/detector.py`
> **Class:** `LaneDetector`

---

## 3.1.1 Mục đích

Phát hiện đường biên làn đường sử dụng các phương pháp xử lý ảnh truyền thống (Traditional Computer Vision), bao gồm:

- Canny Edge Detection để tìm các cạnh trong ảnh
- Hough Transform để phát hiện các đường thẳng
- Kết hợp để xác định vị trí làn đường

---

## 3.1.2 Đầu vào (Input)

| Tham số | Kiểu | Mô tả | Ví dụ |
|---------|------|--------|-------|
| `frame` | `numpy.ndarray` | Frame video (BGR) | Shape: (H, W, 3) |
| `roi_vertices` | `list[tuple]` | Tọa độ vùng quan tâm | `[(0, H), (W, H), ...]` |
| `kernel_size` | `int` | Kernel cho Gaussian blur | 5 |
| `canny_low` | `int` | Ngưỡng thấp Canny | 50 |
| `canny_high` | `int` | Ngưỡng cao Canny | 150 |
| `hough_threshold` | `int` | Ngưỡng Hough Transform | 100 |

---

## 3.1.3 Đầu ra (Output)

```python
{
    "left_lane": {
        "start": (x1, y1),      # Điểm bắt đầu
        "end": (x2, y2),         # Điểm kết thúc
        "slope": float,          # Độ dốc đường
        "confidence": float      # Độ tin cậy (0-1)
    },
    "right_lane": {
        "start": (x1, y1),
        "end": (x2, y2),
        "slope": float,
        "confidence": float
    },
    "all_lines": [(x1, y1, x2, y2), ...],  # Tất cả lines phát hiện được
    "processing_time_ms": float
}
```

---

## 3.1.4 Điều kiện tiên quyết

- [ ] Frame đầu vào không rỗng
- [ ] Frame có shape hợp lệ (H > 0, W > 0)
- [ ] Camera đã được calibrate (intrinsic parameters)
- [ ] Vùng quan tâm (ROI) đã được định nghĩa

---

## 3.1.5 Luồng xử lý

```
Bước 1: Đọc và tiền xử lý frame
    │
    ├─ Chuyển sang ảnh xám (grayscale)
    ├─ Áp dụng Gaussian Blur (kernel_size=5)
    └─ Resize về kích thước chuẩn (640x384)
    │
    ▼
Bước 2: Áp dụng Canny Edge Detection
    │
    ├─ Xác định vùng quan tâm (ROI mask)
    ├─ Nhân mask với ảnh đã làm mượt
    ├─ Áp dụng Canny với ngưỡng [canny_low, canny_high]
    └─ Kết quả: Binary edge image
    │
    ▼
Bước 3: Hough Transform để tìm đường thẳng
    │
    ├─ HoughLinesP với tham số:
    │   ├─ rho = 1
    │   ├─ theta = π/180
    │   ├─ threshold = hough_threshold
    │   ├─ minLineLength = 40
    │   └─ maxLineGap = 100
    └─ Kết quả: Danh sách các đoạn thẳng
    │
    ▼
Bước 4: Phân loại đường (trái/phải)
    │
    ├─ Tính slope của mỗi đoạn thẳng
    ├─ Đường bên trái: slope < 0 (trong hệ tọa độ ảnh)
    ├─ Đường bên phải: slope > 0
    ├─ Nhóm các đoạn thẳng cùng phía (dựa trên vị trí x)
    └─ Nội suy đường cuối cùng (average/extrapolate)
    │
    ▼
Bước 5: Tính confidence và lọc nhiễu
    │
    ├─ Loại bỏ các đường có confidence thấp
    ├─ Smooth kết quả với các frame trước (moving average)
    └─ Trả về kết quả cuối cùng
```

---

## 3.1.6 Các trường hợp đặc biệt

| Trường hợp | Xử lý |
|------------|-------|
| Không phát hiện được đường nào | Trả về `None`, sử dụng kết quả từ frame trước |
| Chỉ phát hiện được 1 đường | Giả định đường còn lại song song với đường đã có |
| Nhiều đường cùng phía | Chọn đường có confidence cao nhất hoặc nhóm lại |
| Đường bị che khuất | Sử dụng Kalman Filter để dự đoán |
| Điều kiện ánh sáng kém | Tăng ngưỡng Canny hoặc chuyển sang dùng model DL |

---

## 3.1.7 Thông báo/Kết quả trả về

| Trạng thái | Mã | Mô tả |
|------------|-----|-------|
| Thành công | `200` | Phát hiện đầy đủ làn đường |
| Cảnh báo | `201` | Chỉ phát hiện được 1 đường |
| Cảnh báo | `202` | Confidence thấp (< 0.5) |
| Thất bại | `400` | Không phát hiện được đường nào |
| Thất bại | `401` | Frame đầu vào không hợp lệ |

---

## 3.1.8 Hàm/Module liên quan

| Module | Đường dẫn | Mô tả |
|--------|-----------|-------|
| `preprocess_frame()` | `preprocessing/image_processor.py` | Tiền xử lý ảnh |
| `apply_roi()` | `preprocessing/roi_extractor.py` | Trích xuất vùng quan tâm |
| `LaneSmoother` | `lane_detection/smoother.py` | Làm mượt kết quả theo thời gian |

---

## 3.1.9 Ví dụ

**Input:**
```python
frame = cv2.imread("test_image.jpg")  # Shape: (720, 1280, 3)
roi_vertices = [(0, 720), (500, 400), (780, 400), (1280, 720)]
```

**Output:**
```python
{
    "left_lane": {
        "start": (230, 720),
        "end": (500, 400),
        "slope": -0.72,
        "confidence": 0.89
    },
    "right_lane": {
        "start": (1050, 720),
        "end": (780, 400),
        "slope": 0.68,
        "confidence": 0.92
    },
    "all_lines": [(230, 720, 500, 400), (1050, 720, 780, 400), ...],
    "processing_time_ms": 12.5
}
```

---

## 3.1.10 Ghi chú

- **Threshold tuning:** Ngưỡng Canny và Hough cần được điều chỉnh theo từng dataset
- **ROI configuration:** Vùng quan tâm nên được điều chỉnh theo vị trí gắn camera
- **Performance:** Phương pháp này nhanh nhưng kém chính xác trong điều kiện phức tạp

---

## 3.1.11 Checklist

```markdown
- [ ] Tạo class `LaneDetector`
- [ ] Implement `detect_lanes(frame, roi)` method
- [ ] Implement `apply_canny_edge_detection(image)` method
- [ ] Implement `hough_line_detection(edges)` method
- [ ] Implement `classify_lines_by_slope(lines)` method
- [ ] Implement `extrapolate_lane_lines(lines)` method
- [ ] Thêm moving average smoothing
- [ ] Viết unit tests cho từng method
- [ ] Tối ưu performance (vectorization, numba)
- [ ] Test trên dataset thực tế
```

---

## Related

- [1-overview.md](./1-overview.md) - Tổng quan
- [8-checklist.md](./8-checklist.md) - Checklist tổng hợp

---

**Section:** 3.1. Lane Detection
