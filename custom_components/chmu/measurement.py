"""Element-level observations; raw source quality is not a confidence score."""

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from .const import MEASUREMENT_STALE_AFTER, MEASUREMENT_UNUSABLE_AFTER


@dataclass(frozen=True)
class MeasurementValue:
    """One latest source row, including unavailable rows for diagnostics."""

    value: float | None
    measured_at: datetime | None
    quality: Any = None
    flag: Any = None
    state: str = "fresh"

    @property
    def usable(self) -> bool:
        return self.state in ("fresh", "stale")

    def at(self, now: datetime) -> "MeasurementValue":
        """Classify this row against an aware UTC poll instant."""
        if self.measured_at is None:
            return replace(self, state="invalid_timestamp")
        if self.value is None or self.quality == 4:
            return replace(self, state="missing")
        # Official meta4: 2 = Poor, do not use yet; 5 = Unknown, not bad.
        if self.quality == 2:
            return replace(self, state="invalid_quality")
        age = now - self.measured_at
        if age.total_seconds() < 0:
            return replace(self, state="future")
        if age > MEASUREMENT_UNUSABLE_AFTER:
            return replace(self, state="unusable")
        if age > MEASUREMENT_STALE_AFTER:
            return replace(self, state="stale")
        return replace(self, state="fresh")
