# Checklist Tổng hợp

> Tổng hợp tất cả checklist từ các module để dễ tracking tiến độ

---

## 🚦 Tổng quan tiến độ

| Module | Checklist | Hoàn thành |
|--------|-----------|------------|
| Lane Detection | [3.1](#31-lane-detection) | 0/10 |
| Lane Segmentation | [3.2](#32-lane-segmentation) | 0/14 |
| Lane Departure Warning | [3.3](#33-lane-departure-warning) | 0/15 |
| Integration | [4](#4-tích-hợp-hệ-thống) | 0/5 |
| Testing | [5](#5-testing) | 0/5 |

---

## 3.1 Lane Detection

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

## 3.2 Lane Segmentation

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

## 3.3 Lane Departure Warning

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

## 4. Tích hợp hệ thống

```markdown
- [ ] Tạo API endpoint `/api/detection/lane`
- [ ] Tạo API endpoint `/api/detection/segment`
- [ ] Tạo API endpoint `/api/adas/departure`
- [ ] Implement request/response format
- [ ] Kết nối frontend với backend
```

---

## 5. Testing

```markdown
## P0 - Critical (Must Pass)
- [ ] Lane detection on clear highway
- [ ] Lane departure alert when crossing line
- [ ] No false positive on straight road

## P1 - High (Should Pass)
- [ ] Lane detection in urban environment
- [ ] Handle missing frames gracefully
- [ ] Performance meets 24 FPS target
```

---

## 📁 File Structure cần tạo

```
backend/ai-service/
├── preprocessing/
│   ├── image_processor.py      # ✓ Cần tạo
│   └── roi_extractor.py        # ✓ Cần tạo
│
├── traditional_cv/
│   └── lane_detection/
│       ├── detector.py         # ✓ Module 3.1
│       ├── smoother.py         # ✓ Cần tạo
│       └── test_detector.py    # ✓ Cần tạo
│
├── ai_models/
│   └── lane_segmentation/
│       ├── segmenter.py        # ✓ Module 3.2
│       ├── model.py            # ✓ Cần tạo
│       ├── postprocess.py      # ✓ Cần tạo
│       └── test_segmenter.py   # ✓ Cần tạo
│
├── adas/
│   ├── departure_warning.py    # ✓ Module 3.3
│   ├── alert_manager.py        # ✓ Cần tạo
│   └── test_warning.py         # ✓ Cần tạo
│
├── config/
│   └── lane_config.py         # ✓ Cần tạo
│
└── main.py                     # ✓ Cần tạo
```

---

## 📅 Timeline đề xuất

| Tuần | Mục tiêu |
|------|----------|
| Tuần 1 | Hoàn thành Module 3.1 (Lane Detection) |
| Tuần 2 | Hoàn thành Module 3.2 (Lane Segmentation) |
| Tuần 3 | Hoàn thành Module 3.3 (Departure Warning) |
| Tuần 4 | Integration + Testing |

---

**Last Updated:** 2026-06-16
