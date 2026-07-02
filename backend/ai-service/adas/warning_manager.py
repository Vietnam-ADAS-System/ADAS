"""Warning de-duplication and prioritization."""

from __future__ import annotations

from typing import Iterable, List, Tuple

from .data_models import PRIORITY_RANK, Warning


class WarningManager:
    def organize(self, warnings: Iterable[Warning]) -> List[Warning]:
        deduped = {}
        for warning in warnings:
            key: Tuple[str, object] = (warning.type, warning.track_id)
            current = deduped.get(key)
            if current is None or PRIORITY_RANK[warning.priority] > PRIORITY_RANK[current.priority]:
                deduped[key] = warning

        return sorted(
            deduped.values(),
            key=lambda warning: PRIORITY_RANK[warning.priority],
            reverse=True,
        )

