# 3.2 Lane Segmentation - Phân đoạn làn đường

> **File:** `backend/ai-service/ai_models/lane_segmentation/segmenter.py`
> **Class:** `LaneSegmenter`
> **Model:** DeepLabV3+ (pretrained trên Cityscapes + custom fine-tuned)

---

## 3.2.1 Mục đích

Phân đoạn làn đường sử dụng Deep Learning (DeepLabV3+), cho phép:

- Xác định chính xác vùng làn đường (pixel-level)
- Phân biệt các loại vạch kẻ đường (đường liền, đường đứt)
- Hoạt động tốt trong điều kiện ánh sáng phức tạp

---

## 3.2.2 Đầu vào (Input)

| Tham số | Kiểu | Mô tả | Ví dụ |
|---------|------|--------|-------|
| `frame` | `numpy.ndarray` | Frame video (BGR) | Shape: (H, W, 3) |
| `model_path` | `str` | Đường dẫn pretrained model | `./models/lane_deeplabv3plus.pth` |
| `input_size` | `tuple` | Kích thước input model | (512, 512) |

---

## 3.2.3 Đầu ra (Output)

```python
{
    "lane_mask": numpy.ndarray,     # Binary mask làn đường (H, W)
    "colored_mask": numpy.ndarray,  # Mask màu để visualize (H, W, 3)
    "lane_boundaries": {
        "left": [(x, y), ...],      # Tọa độ biên trái
        "right": [(x, y), ...]      # Tọa độ biên phải
    },
    "confidence": float,            # Độ tin cậy trung bình
    "processing_time_ms": float
}
```

---

## 3.2.4 Điều kiện tiên quyết

- [ ] Model đã được load vào memory
- [ ] Frame đầu vào có shape hợp lệ
- [ ] GPU/CUDA available (khuyến nghị) hoặc CPU fallback

---

## 3.2.5 Luồng xử lý

```
Bước 1: Tiền xử lý cho model
    │
    ├─ Resize frame về input_size (512x512)
    ├─ Normalize pixel values (ImageNet stats)
    ├─ Chuyển BGR → RGB
    └─ Convert sang tensor [1, 3, H, W]
    │
    ▼
Bước 2: Inference với DeepLabV3+
    │
    ├─ Load model nếu chưa load
    ├─ Set model sang eval mode
    ├─ Forward pass: input_tensor → model
    ├─ Post-process output: logits → segmentation mask
    └─ Apply softmax để lấy xác suất
    │
    ▼
Bước 3: Post-processing mask
    │
    ├─ Resize mask về kích thước gốc
    ├─ Apply threshold (0.5) để binary hóa
    ├─ Morphological operations (remove noise)
    │   ├─ Opening (erode → dilate)
    │   └─ Closing (dilate → erode)
    └─ Connected component analysis
    │
    ▼
Bước 4: Trích xuất biên làn đường
    │
    ├─ Tìm contours từ binary mask
    ├─ Phân loại contours (left/right lane)
    ├─ Fit polynomial (2nd order) cho mỗi biên
    └─ Smooth theo thời gian
    │
    ▼
Bước 5: Tạo overlay cho visualize
    │
    ├─ Tạo colored mask (lane = màu xanh lá)
    ├─ Alpha blend với frame gốc
    └─ Vẽ lane boundaries lên frame
```

---

## 3.2.6 Các trường hợp đặc biệt

| Trường hợp | Xử lý |
|------------|-------|
| Model inference fail | Fallback sang Traditional CV |
| GPU out of memory | Xử lý từng crop nhỏ hoặc giảm resolution |
| Mask rỗng hoàn toàn | Trả về empty mask, warning |
| Nhiều disconnected regions | Chọn region lớn nhất hoặc gần tâm ảnh |

---

## 3.2.7 Thông báo/Kết quả trả về

| Trạng thái | Mã | Mô tả |
|------------|-----|-------|
| Thành công | `200` | Segmentation hoàn chỉnh |
| Cảnh báo | `201` | Low confidence regions |
| Thất bại | `400` | Model inference failed |
| Thất bại | `401` | Invalid input dimensions |

---

## 3.2.8 Hàm/Module liên quan

| Module | Đường dẫn | Mô tả |
|--------|-----------|-------|
| `DeepLabV3Plus` | `ai_models/lane_segmentation/model.py` | Model architecture |
| `SegmentationPostProcessor` | `ai_models/lane_segmentation/postprocess.py` | Post-processing logic |
| `BoundaryExtractor` | `ai_models/lane_segmentation/boundary.py` | Trích xuất biên làn |

---

## 3.2.9 Ví dụ

**Input:**
```python
frame = cv2.imread("road_image.jpg")  # Shape: (720, 1280, 3)
```

**Output:**
```python
{
    "lane_mask": numpy.ndarray,  # Shape: (720, 1280), dtype: uint8
    "colored_mask": numpy.ndarray,  # Shape: (720, 1280, 3)
    "lane_boundaries": {
        "left": [(250, 720), (280, 600), (320, 480), ...],
        "right": [(1030, 720), (1000, 600), (960, 480), ...]
    },
    "confidence": 0.94,
    "processing_time_ms": 45.2
}
```

---

## 3.2.10 Ghi chú

- **Model training:** Cần dataset Vietnamese roads để fine-tune
- **Classes:** Lane (1 class) hoặc Lane + Road markings (2 classes)
- **Augmentation:** Random crop, brightness, contrast để tăng robustness

---

## 3.2.11 Checklist

```markdown
## Model Setup
- [ ] Tạo class `LaneSegmenter`
- [ ] Load pretrained DeepLabV3+ weights
- [ ] Implement `segment(frame)` method
- [ ] Implement `preprocess_input(frame)` method
- [ ] Implement `postprocess_output(logits)` method

## Post-processing
- [ ] Implement morphological operations
- [ ] Implement contour extraction
- [ ] Implement polynomial fitting cho boundaries
- [ ] Implement temporal smoothing

## Visualization
- [ ] Implement `create_overlay(frame, mask)` method
- [ ] Implement `draw_lane_boundaries(frame, boundaries)` method

## Optimization
- [ ] Enable TorchScript optimization
- [ ] Enable ONNX export nếu cần
- [ ] Test inference time trên GPU/CPU

## Testing
- [ ] Unit tests cho preprocessing
- [ ] Unit tests cho postprocessing
- [ ] Integration tests với full pipeline
- [ ] Benchmark trên test dataset
```

---

## Related

- [1-overview.md](./1-overview.md) - Tổng quan
- [8-checklist.md](./8-checklist.md) - Checklist tổng hợp

---

**Section:** 3.2. Lane Segmentation
