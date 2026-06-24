# 4. Tích hợp hệ thống

---

## 4.1 Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │ Video    │───▶│ Upload   │───▶│ Display  │                   │
│  │ Capture  │    │ to API   │    │ Results  │                   │
│  └──────────┘    └──────────┘    └──────────┘                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP/WS
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      NODE.JS BACKEND                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │ Upload   │───▶│ Route    │───▶│ Response │                   │
│  │ Handler  │    │ Handler  │    │ Handler  │                   │
│  └──────────┘    └──────────┘    └──────────┘                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Internal
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      AI SERVICE (FastAPI)                         │
│                                                                  │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│  │ Frame   │───▶│ Pre     │───▶│ Lane    │───▶│ Departure │     │
│  │ Extract │    │ process │    │ Detect  │    │ Warning   │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘        │
│                      │            │              │               │
│                      └────────────┴──────────────┘               │
│                               │                                  │
│                               ▼                                  │
│                      ┌─────────────────┐                         │
│                      │   Fusion &     │                         │
│                      │   Output Gen    │                         │
│                      └─────────────────┘                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4.2 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/api/detection/lane` | Detect lane từ image |
| `POST` | `/api/detection/segment` | Segment lane từ image |
| `POST` | `/api/adas/departure` | Check lane departure |
| `POST` | `/api/video/lane-analysis` | Analyze full video |

---

## 4.3 Module Dependencies

```
LaneDetection (this project)
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

Dependencies:
    └── VehicleDetection (sibling project)
        └── tracking/
            └── vehicle_tracker.py
```

---

## 4.4 Input/Output Format

### Request Format (JSON)
```json
{
  "image_url": "string (URL hoặc base64)",
  "options": {
    "detect_method": "traditional" | "dl" | "fusion",
    "return_overlay": true | false
  }
}
```

### Response Format (JSON)
```json
{
  "status": "success" | "error",
  "data": {
    "lanes": {
      "left": [[x1, y1], [x2, y2], ...],
      "right": [[x1, y1], [x2, y2], ...]
    },
    "departure": {
      "status": "SAFE" | "WARNING" | "ALERT",
      "ttlc": 2.8
    },
    "overlay_url": "string (URL ảnh đã annotate)",
    "processing_time_ms": 45.2
  },
  "error": null
}
```

---

## Related

- [2-detection.md](./2-detection.md) - Lane Detection
- [3-segmentation.md](./3-segmentation.md) - Lane Segmentation
- [4-warning.md](./4-warning.md) - Departure Warning

---

**Section:** 4. Integration
