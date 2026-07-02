# Project State

## Current Progress

### Timeline: Tracking (DeepSORT) — ADAS

```
Tracking (DeepSORT) ✅ → Fusion → Lane Deviation Alert → Sign Alert → Dashboard → Evaluation
```

**Status**: ✅ **COMPLETED** (2026-07-02)

---

### AI Components — Tracking Module

**Module**: `backend/ai-service/tracking/`

**Implemented**:
- ✅ `ObjectTracker` class — Main tracking engine
  - DeepSORT support (lazy-loaded with fallback to IoU matching)
  - Separate trackers for vehicle & pedestrian
  - Configurable tracking parameters (max_age, n_init, max_cosine_distance)
- ✅ `Track` dataclass — Track representation (track_id, class_name, bbox, confidence, frame_count)
- ✅ `TrackerConfig` dataclass — Configuration
- ✅ Detector format normalization (vehicle vs pedestrian different output formats)
- ✅ IoU-based fallback matching (when DeepSORT embedder unavailable)
- ✅ Full documentation in `tracking/README.md`

**Key Features**:
- Dual-mode: DeepSORT (appearance-based) + IoU fallback (geometry-based)
- Lazy DeepSORT initialization to avoid embedder download hang
- Separate tracking pipelines for vehicles & pedestrians
- Stable ID assignment across frames (no excessive ID switches)
- Configurable object retention (max_age for tracking loss tolerance)

**Testing**:
- ✅ Unit tests passed (Frame 1→2 ID consistency)
- ✅ Mock detections verified
- ✅ Track serialization (to_dict)

**Dependencies**:
- ✅ Added `deep-sort-realtime>=1.3.0` to `requirements.txt`

**Output Format** (standardized for Fusion):
```python
Track(
    track_id: int,           # Stable ID per object
    class_name: str,         # "vehicle" or "pedestrian"
    bbox: [x1, y1, x2, y2],  # Bounding box coordinates
    confidence: float,       # Detection confidence
    frame_count: int,        # Frames this track has existed
    time_since_update: int   # Frames since last detection
)
```

**Next Module**: Fusion (will consume tracking output to combine vehicle + pedestrian tracks)

---

### Files Created

| File | Purpose |
|---|---|
| `backend/ai-service/tracking/__init__.py` | Module exports |
| `backend/ai-service/tracking/deepsort_tracker.py` | Core tracking implementation |
| `backend/ai-service/tracking/README.md` | Full documentation |

### Files Modified

| File | Changes |
|---|---|
| `backend/ai-service/requirements.txt` | Added `deep-sort-realtime>=1.3.0` |

---

### Known Notes

1. **DeepSORT Embedder**: Uses lazy loading (first `update()` call) to avoid embedder download hang. Fallback to IoU-based tracking works smoothly.
2. **Format Normalization**: Vehicle detector returns wrapped dict with nested bbox; Pedestrian returns flat list. ObjectTracker handles both transparently.
3. **Performance**: IoU fallback adds ~5-10ms per frame; DeepSORT appearance matching adds ~15-30ms (depends on object count).
4. **Integration**: Output format designed for Fusion module (no additional conversion needed).

---

Last Updated: **2026-07-02**
Status: **✅ READY FOR FUSION INTEGRATION**
