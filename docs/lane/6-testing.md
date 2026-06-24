# 5. Testing

---

## 5.1 Test Strategy

| Level | Scope | Tools |
|-------|-------|-------|
| Unit | Single method/module | pytest, unittest |
| Integration | Module interactions | pytest, fixtures |
| System | End-to-end pipeline | Integration test suite |
| Performance | FPS, latency | timeit, profiling |
| Regression | Pre-release | CI/CD pipeline |

---

## 5.2 Test Datasets

| Dataset | Purpose | Size | Source |
|---------|---------|------|--------|
| Highway day | Basic lane detection | 1000 frames | Synthetic + Real |
| Urban roads | Complex scenarios | 500 frames | Real |
| Night driving | Low light conditions | 300 frames | Real |
| Rainy weather | Adverse conditions | 200 frames | Real |
| Vietnam roads | Local context | TBD | To be collected |

---

## 5.3 Test Cases Priority

```markdown
## P0 - Critical (Must Pass)
- [ ] Lane detection on clear highway
- [ ] Lane departure alert when crossing line
- [ ] No false positive on straight road

## P1 - High (Should Pass)
- [ ] Lane detection in urban environment
- [ ] Handle missing frames gracefully
- [ ] Performance meets 24 FPS target

## P2 - Medium (Nice to Have)
- [ ] Detection on curved roads
- [ ] Night time detection
- [ ] Multi-lane detection (3+ lanes)

## P3 - Low (Future)
- [ ] Rain/fog conditions
- [ ] Shadow handling
- [ ] Construction zone detection
```

---

## 5.4 Unit Test Examples

### Test LaneDetector

```python
# tests/test_lane_detector.py
import pytest
import numpy as np

def test_detect_lanes_with_valid_frame():
    """Test với frame hợp lệ"""
    from detector import LaneDetector
    detector = LaneDetector()
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    result = detector.detect_lanes(frame)
    assert result is not None
    assert "left_lane" in result
    assert "right_lane" in result

def test_detect_lanes_with_empty_frame():
    """Test với frame rỗng"""
    from detector import LaneDetector
    detector = LaneDetector()
    with pytest.raises(ValueError):
        detector.detect_lanes(None)
```

### Test LaneDepartureWarning

```python
# tests/test_departure_warning.py
def test_warning_level_safe():
    """Test SAFE status"""
    warning = LaneDepartureWarning()
    result = warning.check(
        lane_boundaries={"left": [...], "right": [...]},
        vehicle_position=(640, 500),
        offset=0.05
    )
    assert result["status"] == "SAFE"
    assert result["warning_level"] == 0

def test_warning_level_alert():
    """Test ALERT status"""
    warning = LaneDepartureWarning()
    result = warning.check(
        lane_boundaries={"left": [...], "right": [...]},
        vehicle_position=(640, 500),
        offset=0.35
    )
    assert result["status"] == "ALERT"
    assert result["warning_level"] == 2
```

---

## Related

- [8-checklist.md](./8-checklist.md) - Checklist tổng hợp

---

**Section:** 5. Testing
