"""Utility helpers for ADAS modules."""

from __future__ import annotations

from typing import Any, Dict


def as_dict(value: Any) -> Dict[str, Any]:
    return value.to_dict() if hasattr(value, "to_dict") else dict(value or {})

