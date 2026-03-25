from __future__ import annotations

import math


DEFAULT_DRAFT_TEMPERATURE = 1.0
INVALID_DRAFT_TEMPERATURE_MESSAGE = (
    "draft temperature must be a finite number between 0.0 and 2.0"
)


def normalize_draft_temperature(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(INVALID_DRAFT_TEMPERATURE_MESSAGE)

    temperature = float(value)
    if not math.isfinite(temperature) or temperature < 0.0 or temperature > 2.0:
        raise ValueError(INVALID_DRAFT_TEMPERATURE_MESSAGE)

    return temperature


__all__ = [
    "DEFAULT_DRAFT_TEMPERATURE",
    "INVALID_DRAFT_TEMPERATURE_MESSAGE",
    "normalize_draft_temperature",
]
