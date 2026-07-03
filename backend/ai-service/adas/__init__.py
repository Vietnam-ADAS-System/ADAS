"""ADAS decision layer public API."""

from __future__ import annotations

import importlib
import inspect
import sys

importlib.invalidate_caches()
_stale_lane_departure = sys.modules.get(f"{__name__}.lane_departure")
if _stale_lane_departure is not None and not hasattr(_stale_lane_departure, "__path__"):
    sys.modules.pop(f"{__name__}.lane_departure", None)

_stale_data_models = sys.modules.get(f"{__name__}.data_models")
_stale_output_class = getattr(_stale_data_models, "ADASOutput", None)
try:
    _output_params = inspect.signature(_stale_output_class).parameters
except (AttributeError, TypeError, ValueError):
    _output_params = {}
if _stale_output_class is not None and "lane_departure" not in _output_params:
    sys.modules.pop(f"{__name__}.data_models", None)
    sys.modules.pop(f"{__name__}.decision_engine", None)

_stale_decision_engine = sys.modules.get(f"{__name__}.decision_engine")
_stale_engine_class = getattr(_stale_decision_engine, "ADASDecisionEngine", None)
try:
    _engine_params = inspect.signature(_stale_engine_class.evaluate).parameters
except (AttributeError, TypeError, ValueError):
    _engine_params = {}
if _stale_engine_class is not None and "frame_size" not in _engine_params:
    sys.modules.pop(f"{__name__}.decision_engine", None)

from .config import ADASConfig
from .data_models import ADASOutput, Warning
from .decision_engine import ADASDecisionEngine

__all__ = [
    "ADASConfig",
    "ADASDecisionEngine",
    "ADASOutput",
    "Warning",
]
