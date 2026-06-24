# 6. Benchmark & Metrics

---

## 6.1 Performance Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| FPS | ≥ 24 | TBD | 🔴 |
| Latency (per frame) | < 100ms | TBD | 🔴 |
| Detection accuracy | > 85% | TBD | 🔴 |
| False positive rate | < 5% | TBD | 🔴 |
| Memory usage | < 2GB | TBD | 🔴 |

### Performance Targets Breakdown

| Module | Latency Target | Method |
|--------|---------------|--------|
| Preprocessing | < 5ms | Vectorization, SIMD |
| Lane Detection (Traditional CV) | < 15ms | NumPy, OpenCV optimized |
| Lane Segmentation (DL) | < 50ms | GPU inference |
| Departure Warning | < 5ms | Simple math |
| **Total** | **< 100ms** | - |

---

## 6.2 Evaluation Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| IoU (Lane) | Intersection over Union for lane region | (Intersection / Union) × 100% |
| Boundary Error | Mean distance to GT boundaries | Mean(\|predicted - GT\|) |
| Departure Accuracy | Correct departure detection | TP / (TP + FP + FN) |
| TTC Error | Error in TTC prediction | \|predicted_TTC - GT_TTC\| |

### Metric Definitions

```python
# IoU Calculation
def calculate_iou(pred_mask, gt_mask):
    intersection = np.logical_and(pred_mask, gt_mask).sum()
    union = np.logical_or(pred_mask, gt_mask).sum()
    return intersection / union if union > 0 else 0

# Boundary Error
def calculate_boundary_error(pred_lines, gt_lines):
    errors = []
    for pred, gt in zip(pred_lines, gt_lines):
        errors.append(np.linalg.norm(np.array(pred) - np.array(gt)))
    return np.mean(errors)
```

---

## 6.3 Logging & Monitoring

### Metrics to Log Per Frame

```python
LOG_FIELDS = [
    "timestamp",
    "frame_id",
    "fps",
    "detection_time_ms",
    "segmentation_time_ms",
    "warning_time_ms",
    "total_time_ms",
    "lane_confidence",
    "warning_level",
    "ttlc"
]
```

### Logging Format (JSON)

```json
{
  "timestamp": "2026-06-16T10:30:00.000Z",
  "frame_id": 1234,
  "fps": 28.5,
  "detection_time_ms": 12.3,
  "segmentation_time_ms": 45.2,
  "warning_time_ms": 2.1,
  "total_time_ms": 59.6,
  "lane_confidence": 0.89,
  "warning_level": 0,
  "ttlc": null
}
```

---

## 6.4 Benchmark Script

```python
# benchmark.py
import time
import cv2
from traditional_cv.lane_detection import LaneDetector
from ai_models.lane_segmentation import LaneSegmenter
from adas.departure_warning import LaneDepartureWarning

def benchmark():
    detector = LaneDetector()
    segmenter = LaneSegmenter()
    warning = LaneDepartureWarning()
    
    # Load test video
    cap = cv2.VideoCapture("test_video.mp4")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    times = {"detection": [], "segmentation": [], "warning": []}
    
    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break
            
        # Benchmark detection
        start = time.time()
        lanes = detector.detect_lanes(frame)
        times["detection"].append(time.time() - start)
        
        # Benchmark segmentation
        start = time.time()
        mask = segmenter.segment(frame)
        times["segmentation"].append(time.time() - start)
        
        # Benchmark warning
        start = time.time()
        warning.check(lanes, (frame.shape[1]//2, frame.shape[0]//2))
        times["warning"].append(time.time() - start)
    
    cap.release()
    
    # Print results
    for method, t in times.items():
        avg_ms = np.mean(t) * 1000
        print(f"{method}: {avg_ms:.2f}ms avg, {np.min(t)*1000:.2f}ms min")
```

---

## Related

- [6-testing.md](./6-testing.md) - Testing chi tiết

---

**Section:** 6. Benchmark & Metrics
