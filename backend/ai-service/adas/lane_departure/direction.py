"""Offset direction classification."""

from __future__ import annotations


def determine_direction(offset: float) -> str:
    if offset < 0:
        return "LEFT"
    if offset > 0:
        return "RIGHT"
    return "CENTER"

