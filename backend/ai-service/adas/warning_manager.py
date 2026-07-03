"""Warning de-duplication and prioritization."""

from __future__ import annotations

from typing import Any, Iterable, List, Tuple

from .data_models import PRIORITY_RANK, Warning, normalize_priority, warning_from_any


class WarningManager:
    def organize(self, warnings: Iterable[Any]) -> List[Warning]:
        deduped = {}
        for raw_warning in warnings:
            warning = warning_from_any(raw_warning)
            priority = normalize_priority(warning.priority)
            key: Tuple[str, object] = (warning.type, warning.track_id)
            current = deduped.get(key)
            current_priority = normalize_priority(current.priority) if current is not None else "INFO"
            if current is None or PRIORITY_RANK[priority] > PRIORITY_RANK[current_priority]:
                if priority != warning.priority:
                    warning = Warning(
                        type=warning.type,
                        priority=priority,
                        message=warning.message,
                        action=warning.action,
                        value=warning.value,
                        track_id=warning.track_id,
                    )
                deduped[key] = warning

        return sorted(
            deduped.values(),
            key=lambda warning: PRIORITY_RANK[normalize_priority(warning.priority)],
            reverse=True,
        )
