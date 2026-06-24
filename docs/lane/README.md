# Nhận diện làn đường (Lane Detection)

> **Phiên bản:** 1.0.0
> **Ngày tạo:** 2026-06-16
> **Trạng thái:** 🟡 Đang phát triển
> **Phụ trách:** [Tên thành viên]

---

## 📚 Mục lục

| File | Nội dung |
|------|----------|
| [1-overview.md](./1-overview.md) | Tổng quan & Kiến trúc module |
| [2-detection.md](./2-detection.md) | Lane Detection - Nhận diện làn đường |
| [3-segmentation.md](./3-segmentation.md) | Lane Segmentation - Phân đoạn làn đường |
| [4-warning.md](./4-warning.md) | Lane Departure Warning - Cảnh báo chệch làn |
| [5-integration.md](./5-integration.md) | Tích hợp hệ thống |
| [6-testing.md](./6-testing.md) | Testing |
| [7-metrics.md](./7-metrics.md) | Benchmark & Metrics |
| [8-checklist.md](./8-checklist.md) | Checklist tổng hợp |

---

## 🎯 3 Module chính

```ascii
┌─────────────────────────────────────────────────────────────────┐
│                      INPUT: Video Frame                         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PREPROCESSING LAYER                         │
│              Resize → Crop ROI → Color Space                    │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
          ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
          │    LANE      │ │    LANE      │ │    LANE      │
          │  DETECTION   │ │ SEGMENTATION │ │ DEPARTURE    │
          │  (Traditional │ │   (Deep     │ │   WARNING    │
          │     CV)      │ │  LabV3+)    │ │   (Logic)    │
          └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 📁 Cấu trúc file code tương ứng

```
backend/ai-service/
├── preprocessing/
│   └── image_processor.py
├── traditional_cv/
│   └── lane_detection/
│       └── detector.py
├── ai_models/
│   └── lane_segmentation/
│       └── segmenter.py
└── adas/
    └── departure_warning.py
```

---

## ⚡ Quick Links

- **Checklist:** [8-checklist.md](./8-checklist.md)
- **Integration:** [5-integration.md](./5-integration.md)
- **Testing:** [6-testing.md](./6-testing.md)

---

## Quy tắc làm việc

### Phạm vi được phép

- Được phép đọc và phân tích code hiện có
- Được phép tạo file mới trong thư mục này
- Được phép viết code theo template đã có

### Ràng buộc AI

- **Không được tự suy đoán** khi thiếu dữ liệu
- **Không được sửa file** ngoài phạm vi yêu cầu
- **Luôn ưu tiên code hiện có** trước khi đề xuất viết lại

### Quy tắc phản hồi

- Trả lời **ngắn gọn**
- **Giải thích trước** khi thực hiện thay đổi
- Nếu không chắc chắn, **hỏi lại**

---

**Version:** 1.0.0 | **Last Updated:** 2026-06-16
