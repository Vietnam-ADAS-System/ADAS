"""Small geometry and normalization helpers for Fusion."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any, List, Optional, Tuple

from .data_models import BoundingBox


Point = Tuple[float, float]


def bbox_from_any(value: Any) -> Optional[BoundingBox]:
    """Convert common detector bbox formats to BoundingBox."""

    if value is None:
        return None

    if isinstance(value, BoundingBox):
        return value

    if hasattr(value, "bbox"):
        return bbox_from_any(getattr(value, "bbox"))

    if isinstance(value, dict):
        if "bbox" in value:
            return bbox_from_any(value.get("bbox"))
        keys = ("x1", "y1", "x2", "y2")
        if all(key in value for key in keys):
            return BoundingBox(
                float(value["x1"]),
                float(value["y1"]),
                float(value["x2"]),
                float(value["y2"]),
            )

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) >= 4:
            return BoundingBox(float(value[0]), float(value[1]), float(value[2]), float(value[3]))

    return None


def bbox_iou(box_a: BoundingBox, box_b: BoundingBox) -> float:
    xi1 = max(box_a.x1, box_b.x1)
    yi1 = max(box_a.y1, box_b.y1)
    xi2 = min(box_a.x2, box_b.x2)
    yi2 = min(box_a.y2, box_b.y2)
    intersection = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
    area_a = box_a.width * box_a.height
    area_b = box_b.width * box_b.height
    union = area_a + area_b - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def center_from_bbox(box: BoundingBox) -> Point:
    return box.center


def points_to_x(value: Any) -> Optional[float]:
    """Extract a representative x-coordinate from lane points or scalar values."""

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, dict):
        for key in ("x", "lane_center", "center", "lane_left", "lane_right"):
            if key in value:
                extracted = points_to_x(value[key])
                if extracted is not None:
                    return extracted
        return None

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if not value:
            return None
        if len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
            return float(value[0])
        xs: List[float] = []
        for item in value:
            extracted = points_to_x(item)
            if extracted is not None:
                xs.append(extracted)
        if xs:
            return sum(xs) / len(xs)

    return None


def lane_bounds_from_mask(mask: Any) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Return left, right and center x from a binary lane mask when available."""

    if mask is None:
        return None, None, None

    try:
        import numpy as np
    except ImportError:
        return None, None, None

    array = np.asarray(mask)
    if array.size == 0:
        return None, None, None

    nonzero = np.argwhere(array > 0)
    if nonzero.size == 0:
        return None, None, None

    x_values = nonzero[:, 1].astype(float)
    left = float(x_values.min())
    right = float(x_values.max())
    center = (left + right) / 2.0
    return left, right, center


def normalize_vehicle_type(value: Any) -> str:
    label = str(value or "vehicle").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "class": "vehicle",
        "class_name": "vehicle",
        "auto": "car",
        "automobile": "car",
        "vehicle_car": "car",
        "xe_hoi": "car",
        "motorbike": "motorcycle",
        "motor_cycle": "motorcycle",
        "xe_may": "motorcycle",
        "person": "person",
        "pedestrian": "person",
    }
    return aliases.get(label, label)


def parse_speed_limit_value(*values: Any) -> Optional[int]:
    for value in values:
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return int(value)
        match = re.search(r"(\d{2,3})", str(value))
        if match:
            return int(match.group(1))
    return None


def normalize_traffic_rule_type(label: Any) -> str:
    normalized = str(label or "").strip().lower()
    ascii_like = (
        normalized.replace("_", " ")
        .replace("-", " ")
        .replace("cam", "cam")
        .replace("gioi", "gioi")
        .replace("han", "han")
    )

    if "stop" in ascii_like:
        return "STOP"
    if "no entry" in ascii_like or "nguoc chieu" in ascii_like or "cam di" in ascii_like:
        return "NO_ENTRY"
    if "speed" in ascii_like or "toc do" in ascii_like or "gioi han" in ascii_like:
        return "Speed Limit"
    if "yield" in ascii_like or "nhuong duong" in ascii_like:
        return "YIELD"
    if "parking" in ascii_like:
        return "PARKING"
    if not normalized:
        return "UNKNOWN"
    return str(label).strip()


def format_timestamp(frame_index: int, fps: Optional[float]) -> Optional[str]:
    if not fps or fps <= 0:
        return None
    total_seconds = max(0.0, frame_index / fps)
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int(round((total_seconds - int(total_seconds)) * 1000))
    return f"00:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
