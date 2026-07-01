from datetime import datetime, timezone

from apps.trips.hos.engine import plan_trip


def test_short_trip_single_sheet_no_stops():
    trip_start = datetime(2026, 7, 1, 8, 0, tzinfo=timezone.utc)

    plan = plan_trip(
        leg1_distance_mi=0.0,
        leg1_duration_hr=0.0,
        leg2_distance_mi=185.0,
        leg2_duration_hr=3.0,
        current_cycle_used_hr=10.0,
        trip_start=trip_start,
        pickup_location_name="Chicago, IL",
        dropoff_location_name="Indianapolis, IN",
        current_location_name="Chicago, IL",
    )

    assert len(plan.daily_logs_json) == 1

    statuses = [seg.status for seg in plan.segments]
    assert statuses == ["ON", "D", "ON"]
    assert plan.segments[0].remark == "Pickup"
    assert plan.segments[-1].remark == "Dropoff"

    total_on_duty = sum(seg.duration_hr for seg in plan.segments if seg.status in ("D", "ON"))
    assert abs(total_on_duty - 5.0) < 1e-6  # 1h pickup + 3h drive + 1h dropoff

    sheet = plan.daily_logs_json[0]
    assert abs(sum(sheet["totals"].values()) - 24.0) < 1e-6
    assert sheet["totals"]["OFF"] > 18.0  # most of the day off duty
    assert sheet["totals"]["D"] == 3.0
    assert sheet["total_miles_driving_today"] == 185.0
