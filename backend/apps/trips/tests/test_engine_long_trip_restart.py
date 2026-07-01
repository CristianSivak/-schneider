from datetime import datetime, timezone

from apps.trips.hos.engine import plan_trip


def test_long_trip_forces_restart_and_multiple_sheets():
    trip_start = datetime(2026, 7, 1, 8, 0, tzinfo=timezone.utc)
    total_distance = 2790.0
    total_duration = 41.5  # hours

    plan = plan_trip(
        leg1_distance_mi=0.0,
        leg1_duration_hr=0.0,
        leg2_distance_mi=total_distance,
        leg2_duration_hr=total_duration,
        current_cycle_used_hr=60.0,  # only 10 hrs of cycle capacity left
        trip_start=trip_start,
        pickup_location_name="Los Angeles, CA",
        dropoff_location_name="New York, NY",
        current_location_name="Los Angeles, CA",
    )

    assert len(plan.daily_logs_json) >= 5

    restart_segments = [s for s in plan.segments if s.remark == "34-hour restart"]
    assert len(restart_segments) >= 1
    assert restart_segments[0].cycle_used_after < 1e-6

    fuel_segments = [s for s in plan.segments if s.remark == "Fuel stop"]
    assert len(fuel_segments) >= 2

    driving_segments = [s for s in plan.segments if s.status == "D"]
    total_drive_hr = sum(s.duration_hr for s in driving_segments)
    assert abs(total_drive_hr - total_duration) < 0.01

    total_drive_miles = sum(s.end_mile - s.start_mile for s in driving_segments)
    assert abs(total_drive_miles - total_distance) < 0.5

    for sheet in plan.daily_logs_json:
        assert abs(sum(sheet["totals"].values()) - 24.0) < 1e-6

    # The 11-hour limit applies per duty *window* (between qualifying rests),
    # not per calendar day -- a single day's log can legitimately show more
    # than 11 hours of driving if it spans the tail of one window and the
    # start of the next. Verify the real constraint at the window level:
    # split plan.segments into windows at each qualifying rest (>=10 hrs off)
    # and assert no window's total driving time exceeds 11 hours.
    windows: list[list] = [[]]
    for seg in plan.segments:
        if seg.status == "OFF" and seg.duration_hr >= 10.0:
            windows.append([])
        else:
            windows[-1].append(seg)
    for window in windows:
        window_drive_hr = sum(s.duration_hr for s in window if s.status == "D")
        assert window_drive_hr <= 11.0 + 1e-6
