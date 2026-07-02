"""STOP sign decision."""

from __future__ import annotations

from .data_models import Warning


class StopWarningDecision:
    def evaluate(self) -> Warning:
        return Warning(
            type="STOP",
            priority="HIGH",
            message="Prepare to stop",
            action="Prepare To Stop",
        )

