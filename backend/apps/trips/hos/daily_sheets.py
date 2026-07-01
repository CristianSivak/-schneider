"""Splits a flat list of DutySegments into one FMCSA-style daily log sheet per
calendar day, padding implicit Off Duty time before the trip starts and after
it ends within a day so every sheet's row totals always sum to 24 hours.
"""

from collections import defaultdict
from datetime import date as date_cls
from datetime import datetime, time, timedelta

from .types import DutySegment

STATUS_ORDER = ["OFF", "SB", "D", "ON"]


def _split_segment_by_day(seg: DutySegment) -> list[DutySegment]:
    pieces: list[DutySegment] = []
    cursor = seg.start
    span_hr = seg.duration_hr

    while cursor < seg.end:
        day_end = datetime.combine(cursor.date() + timedelta(days=1), time.min, tzinfo=cursor.tzinfo)
        piece_end = min(seg.end, day_end)

        if span_hr <= 0:
            start_mile, end_mile = seg.start_mile, seg.end_mile
        else:
            frac_start = (cursor - seg.start).total_seconds() / 3600.0 / span_hr
            frac_end = (piece_end - seg.start).total_seconds() / 3600.0 / span_hr
            start_mile = seg.start_mile + frac_start * (seg.end_mile - seg.start_mile)
            end_mile = seg.start_mile + frac_end * (seg.end_mile - seg.start_mile)

        pieces.append(DutySegment(
            status=seg.status, start=cursor, end=piece_end, location=seg.location,
            start_mile=start_mile, end_mile=end_mile, remark=seg.remark,
            cycle_used_after=seg.cycle_used_after,
        ))
        cursor = piece_end

    return pieces


def _pad_day_with_off_duty(pieces: list[DutySegment], date: date_cls, current_location_name: str, dropoff_location_name: str, total_distance_mi: float) -> list[DutySegment]:
    pieces = sorted(pieces, key=lambda p: p.start)
    day_start = datetime.combine(date, time.min, tzinfo=pieces[0].start.tzinfo)
    day_end = day_start + timedelta(days=1)
    first_piece, last_piece = pieces[0], pieces[-1]

    if first_piece.start > day_start:
        pieces.insert(0, DutySegment(
            status="OFF", start=day_start, end=first_piece.start,
            location=current_location_name, start_mile=0.0, end_mile=0.0,
            remark="Off duty", cycle_used_after=first_piece.cycle_used_after,
        ))
    if last_piece.end < day_end:
        pieces.append(DutySegment(
            status="OFF", start=last_piece.end, end=day_end,
            location=dropoff_location_name, start_mile=total_distance_mi, end_mile=total_distance_mi,
            remark="Off duty", cycle_used_after=last_piece.cycle_used_after,
        ))
    return pieces


def _describe_position(mile: float, pickup_mile: float, total_distance_mi: float, current_location_name: str, pickup_location_name: str, dropoff_location_name: str) -> str:
    if abs(mile) < 0.5:
        return current_location_name
    if abs(mile - pickup_mile) < 0.5:
        return pickup_location_name
    if abs(mile - total_distance_mi) < 0.5:
        return dropoff_location_name
    return f"En route (mile {mile:.0f})"


def split_into_daily_sheets(
    segments: list[DutySegment],
    pickup_mile: float,
    total_distance_mi: float,
    current_location_name: str,
    pickup_location_name: str,
    dropoff_location_name: str,
) -> list[dict]:
    by_date: dict[date_cls, list[DutySegment]] = defaultdict(list)

    for seg in segments:
        for piece in _split_segment_by_day(seg):
            by_date[piece.start.date()].append(piece)

    if not by_date:
        return []

    for date in by_date:
        by_date[date] = _pad_day_with_off_duty(
            by_date[date], date, current_location_name, dropoff_location_name, total_distance_mi,
        )

    sheets = []
    for day_index, date in enumerate(sorted(by_date.keys()), start=1):
        day_segments = by_date[date]
        totals = {status: 0.0 for status in STATUS_ORDER}
        for piece in day_segments:
            totals[piece.status] += piece.duration_hr

        driving_miles = sum(
            piece.end_mile - piece.start_mile for piece in day_segments if piece.status == "D"
        )
        cycle_used_end_of_day = day_segments[-1].cycle_used_after

        sheets.append({
            "date": date.isoformat(),
            "day_index": day_index,
            "from_location": _describe_position(
                day_segments[0].start_mile, pickup_mile, total_distance_mi,
                current_location_name, pickup_location_name, dropoff_location_name,
            ),
            "to_location": _describe_position(
                day_segments[-1].end_mile, pickup_mile, total_distance_mi,
                current_location_name, pickup_location_name, dropoff_location_name,
            ),
            "total_miles_driving_today": round(driving_miles, 1),
            "total_mileage_today": round(driving_miles, 1),
            "segments": [
                {
                    "status": piece.status,
                    "start": piece.start.isoformat(),
                    "end": piece.end.isoformat(),
                    "location": piece.location,
                    "remark": piece.remark,
                }
                for piece in day_segments
            ],
            "totals": {k: round(v, 2) for k, v in totals.items()},
            "recap": {
                "on_duty_hours_today": round(totals["D"] + totals["ON"], 2),
                "total_lines_3_and_4": round(totals["D"] + totals["ON"], 2),
                "cycle_used_hours_end_of_day": round(cycle_used_end_of_day, 2),
                "hours_available_tomorrow": round(max(0.0, 70.0 - cycle_used_end_of_day), 2),
                "hours_available_after_restart": 70.0,
            },
        })

    return sheets
