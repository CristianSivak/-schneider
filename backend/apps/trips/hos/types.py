from dataclasses import dataclass
from datetime import datetime


@dataclass
class DutySegment:
    status: str  # "OFF" | "SB" | "D" | "ON"
    start: datetime
    end: datetime
    location: str
    start_mile: float
    end_mile: float
    remark: str
    cycle_used_after: float

    @property
    def duration_hr(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0


@dataclass
class TripPlan:
    segments: list[DutySegment]
    daily_logs_json: list[dict]
    stops_summary: dict
    total_distance_miles: float
    total_duration_hours: float
