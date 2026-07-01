from datetime import datetime, timezone

from apps.trips.hos.engine import plan_trip


def test_cycle_already_near_limit_forces_restart_before_pickup():
    trip_start = datetime(2026, 7, 1, 8, 0, tzinfo=timezone.utc)

    plan = plan_trip(
        leg1_distance_mi=0.0,
        leg1_duration_hr=0.0,
        leg2_distance_mi=185.0,
        leg2_duration_hr=3.0,
        current_cycle_used_hr=69.5,  # 1hr pickup would push past 70
        trip_start=trip_start,
        pickup_location_name="Chicago, IL",
        dropoff_location_name="Indianapolis, IN",
        current_location_name="Chicago, IL",
    )

    assert plan.segments[0].remark == "34-hour restart"
    assert plan.segments[0].start == trip_start
    assert plan.segments[0].cycle_used_after == 0.0


def test_zero_distance_first_leg_is_skipped():
    trip_start = datetime(2026, 7, 1, 8, 0, tzinfo=timezone.utc)

    plan = plan_trip(
        leg1_distance_mi=0.0,
        leg1_duration_hr=0.0,
        leg2_distance_mi=100.0,
        leg2_duration_hr=2.0,
        current_cycle_used_hr=0.0,
        trip_start=trip_start,
        pickup_location_name="Denver, CO",
        dropoff_location_name="Boulder, CO",
        current_location_name="Denver, CO",
    )

    assert plan.segments[0].status == "ON"
    assert plan.segments[0].remark == "Pickup"
    assert plan.segments[0].start_mile == 0.0


def test_totals_always_sum_to_24_hours_per_day():
    trip_start = datetime(2026, 7, 1, 8, 0, tzinfo=timezone.utc)

    plan = plan_trip(
        leg1_distance_mi=50.0,
        leg1_duration_hr=1.0,
        leg2_distance_mi=650.0,
        leg2_duration_hr=10.5,
        current_cycle_used_hr=20.0,
        trip_start=trip_start,
        pickup_location_name="Dallas, TX",
        dropoff_location_name="Atlanta, GA",
        current_location_name="Fort Worth, TX",
    )

    assert len(plan.daily_logs_json) >= 2
    for sheet in plan.daily_logs_json:
        assert abs(sum(sheet["totals"].values()) - 24.0) < 1e-6
