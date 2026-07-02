# Fusion Layer

Fusion is a logic-only layer between AI models and ADAS.

It receives normalized outputs from detection, lane, sign and tracking modules,
then produces one `SceneContext` object for ADAS:

```python
{
    "frame": 152,
    "vehicles": [
        {
            "track_id": 5,
            "type": "car",
            "lane": "center",
            "lane_status": "inside_lane",
            "offset": 25,
            "center": [350, 420],
            "speed": None,
            "tracking": True,
        }
    ],
    "traffic_rule": {"type": "Speed Limit", "value": 40},
    "timestamp": "00:00:05.233",
}
```

Fusion does not run YOLO, segmentation, tracking, dashboard rendering or warning
logic. Those responsibilities belong to the AI layer, ADAS layer and UI.

