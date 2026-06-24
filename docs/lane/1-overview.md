# 1. Tổng quan

## 1.1 Mục đích chung

Nhận diện làn đường là chức năng cốt lõi của hệ thống ADAS, cho phép:

- Phát hiện và định vị các làn đường trên đường
- Phân đoạn vùng làn đường (road lane segmentation)
- Tính toán vị trí xe so với làn đường
- Đưa ra cảnh báo khi xe chệch khỏi làn đường

## 1.2 Phạm vi (Scope)

| STT | Module | Mô tả | Ưu tiên |
|-----|--------|--------|----------|
| 1 | Lane Detection | Phát hiện đường biên làn (edge detection + Hough Transform) | Cao |
| 2 | Lane Segmentation | Phân đoạn làn đường (DeepLabV3+) | Cao |
| 3 | Lane Departure Warning | Cảnh báo khi xe chệch làn | Cao |

## 1.3 Giả định (Assumptions)

- Video đầu vào có độ phân giải tối thiểu 720p
- Camera được gắn cố định ở phía trước xe
- Điều kiện ánh sáng: ban ngày, đủ sáng
- Đường có vạch kẻ phân làn rõ ràng

## 1.4 Ràng buộc (Constraints)

| Ràng buộc | Giá trị |
|-----------|---------|
| FPS tối thiểu | 24 FPS |
| Latency | < 100ms/frame |
| Độ phân giải tối đa hỗ trợ | 1920x1080 |
| Số làn đường tối đa | 6 (3 làn mỗi bên) |

---

## 2. Kiến trúc module

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT: Video Frame                       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PREPROCESSING LAYER                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Resize    │→ │   Crop      │→ │   Color Space Convert   │  │
│  │  640x384    │  │  Region of  │  │   RGB → HLS/HSV         │  │
│  │             │  │   Interest  │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
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
                    │             │             │
                    └─────────────┼─────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FUSION MODULE                              │
│            Kết hợp kết quả từ multiple sources                  │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Lane Edges  │  │Lane Mask    │  │   Departure Status       │  │
│  │ Coordinates │  │Overlay      │  │   (Safe/Warning/Alert)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Related Files

- [2-detection.md](./2-detection.md) - Lane Detection chi tiết
- [3-segmentation.md](./3-segmentation.md) - Lane Segmentation chi tiết
- [4-warning.md](./4-warning.md) - Departure Warning chi tiết

---

**Section:** 1. Overview
