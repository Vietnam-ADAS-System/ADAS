"""No-entry decision."""

from __future__ import annotations

from .data_models import Warning


class NoEntryWarningDecision:
    def evaluate(self) -> Warning:
        return Warning(
            type="No Entry",
            priority="HIGH",
            message="No entry warning",
        )

