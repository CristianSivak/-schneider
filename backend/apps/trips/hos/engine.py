"""Pure-Python HOS (Hours of Service) / ELD daily-log simulation engine.

Models a property-carrying driver's trip as a sequence of activities
(drive -> on-duty pickup -> drive -> on-duty dropoff) and walks the driving
legs in constraint-bound chunks, inserting the FMCSA-required stop whenever a
rule limit is reached: 11-hour driving limit, 14-hour on-duty window, 30-minute
break after 8 cumulative driving hours, 1,000-mile fueling interval, and the
70-hour/8-day cycle limit (resolved here via a 34-hour restart since we are
only given a single current_cycle_used_hr snapshot, not a full rolling 8-day
history).

Known simplifications (documented, not bugs):
- The sleeper-berth split-duty provision is out of scope; all mandatory rest
  is modeled as Off Duty (row 2 "Sleeper Berth" is always empty).
- The 1-hour pickup/dropoff activities are not themselves re-checked against
  the 14-hour window (only against the 70-hour cycle cap) -- a real dispatch
  would ensure a delivery appointment falls inside the remaining window.
"""

from datetime import datetime, timedelta

from .daily_sheets import split_into_daily_sheets
from .types import DutySegment, TripPlan

EPS = 1e-6

DRIVING_LIMIT_HR = 11.0
WINDOW_LIMIT_HR = 14.0
BREAK_AFTER_DRIVING_HR = 8.0
CYCLE_LIMIT_HR = 70.0
RESTART_HR = 34.0
OFF_DUTY_RESET_HR = 10.0
BREAK_DURATION_HR = 0.5

# If a mandatory rest is triggered this close to the fuel threshold, assume
# the driver fuels during the stop instead of forcing a near-zero-length
# driving chunk immediately after resuming.
FUEL_COINCIDENCE_BUFFER_MI = 50.0

_STOP_TYPE_MAP = {
    ("ON", "Pickup"): "pickup",
    ("ON", "Dropoff"): "dropoff",
    ("ON", "Fuel stop"): "fuel",
    ("OFF", "10-hour off-duty rest"): "rest_10hr",
    ("OFF", "34-hour restart"): "restart_34hr",
    ("OFF", "Required 30-minute break"): "break_30min",
}


class _EngineState:
    def __init__(self, trip_start: datetime, current_cycle_used_hr: float, current_location_name: str):
        self.t = trip_start
        self.position_mi = 0.0
        self.cycle_used = current_cycle_used_hr
        self.miles_since_fuel = 0.0
        self.drive_hrs_since_break = 0.0
        self.window_start: datetime | None = None
        self.drive_hrs_in_window = 0.0
        self.segments: list[DutySegment] = []
        self.current_location_name = current_location_name

    def append_segment(self, status: str, duration_hr: float, location: str, remark: str, distance_mi: float = 0.0) -> DutySegment:
        start = self.t
        end = start + timedelta(hours=duration_hr)
        start_mile = self.position_mi
        end_mile = self.position_mi + distance_mi
        if status in ("D", "ON"):
            self.cycle_used += duration_hr
        seg = DutySegment(
            status=status, start=start, end=end, location=location,
            start_mile=start_mile, end_mile=end_mile, remark=remark,
            cycle_used_after=self.cycle_used,
        )
        self.segments.append(seg)
        self.t = end
        self.position_mi = end_mile
        return seg

    def hours_since_window_open(self) -> float:
        if self.window_start is None:
            return 0.0
        return (self.t - self.window_start).total_seconds() / 3600.0

    def _maybe_clear_fuel_counter_on_stop(self, fuel_stop_interval_mi: float):
        if self.miles_since_fuel >= fuel_stop_interval_mi - FUEL_COINCIDENCE_BUFFER_MI:
            self.miles_since_fuel = 0.0

    def insert_34hr_restart(self, fuel_stop_interval_mi: float = 1000.0):
        # Reset the cycle *before* appending so the segment's cycle_used_after
        # correctly reflects the post-restart state (0 hours used).
        self.cycle_used = 0.0
        self.append_segment("OFF", RESTART_HR, "en route", "34-hour restart")
        self.window_start = None
        self.drive_hrs_in_window = 0.0
        self.drive_hrs_since_break = 0.0
        self._maybe_clear_fuel_counter_on_stop(fuel_stop_interval_mi)

    def insert_10hr_reset(self, fuel_stop_interval_mi: float = 1000.0):
        self.append_segment("OFF", OFF_DUTY_RESET_HR, "en route", "10-hour off-duty rest")
        self.window_start = None
        self.drive_hrs_in_window = 0.0
        self.drive_hrs_since_break = 0.0
        self._maybe_clear_fuel_counter_on_stop(fuel_stop_interval_mi)

    def insert_30min_break(self):
        self.append_segment("OFF", BREAK_DURATION_HR, "en route", "Required 30-minute break")
        self.drive_hrs_since_break = 0.0

    def insert_fuel_stop(self, fuel_stop_duration_hr: float):
        self.maybe_insert_restart(fuel_stop_duration_hr)
        location = f"mile {self.position_mi:.0f}"
        self.append_segment("ON", fuel_stop_duration_hr, location, "Fuel stop")
        self.miles_since_fuel = 0.0

    def maybe_insert_restart(self, upcoming_duration_hr: float):
        if self.cycle_used + upcoming_duration_hr > CYCLE_LIMIT_HR + EPS:
            self.insert_34hr_restart()

    def do_on_activity(self, duration_hr: float, location: str, remark: str):
        self.maybe_insert_restart(duration_hr)
        if self.window_start is None:
            self.window_start = self.t
        self.append_segment("ON", duration_hr, location, remark)

    def do_drive_activity(self, distance_mi: float, duration_hr: float, fuel_stop_interval_mi: float, fuel_stop_duration_hr: float):
        if distance_mi <= EPS or duration_hr <= EPS:
            return

        avg_speed_mph = distance_mi / duration_hr
        remaining_hr = duration_hr

        while remaining_hr > EPS:
            if self.window_start is None:
                self.window_start = self.t
                self.drive_hrs_in_window = 0.0

            c_11hr = DRIVING_LIMIT_HR - self.drive_hrs_in_window
            c_14hr = WINDOW_LIMIT_HR - self.hours_since_window_open()
            c_break = BREAK_AFTER_DRIVING_HR - self.drive_hrs_since_break
            c_fuel = (fuel_stop_interval_mi - self.miles_since_fuel) / avg_speed_mph
            c_cycle = CYCLE_LIMIT_HR - self.cycle_used
            c_dist = remaining_hr

            chunk = min(c_11hr, c_14hr, c_break, c_fuel, c_cycle, c_dist)

            if chunk <= EPS:
                self._resolve_zero_chunk(c_11hr, c_14hr, c_break, c_fuel, c_cycle, fuel_stop_interval_mi, fuel_stop_duration_hr)
                continue

            distance = chunk * avg_speed_mph
            self.append_segment("D", chunk, "en route", "Driving", distance_mi=distance)
            self.drive_hrs_in_window += chunk
            self.drive_hrs_since_break += chunk
            self.miles_since_fuel += distance
            remaining_hr -= chunk

            if remaining_hr <= EPS:
                break  # leg complete, no stop needed

            binding = self._determine_binding(c_11hr, c_14hr, c_break, c_fuel, c_cycle, chunk)
            self._apply_binding(binding, fuel_stop_interval_mi, fuel_stop_duration_hr)

    def _determine_binding(self, c_11hr, c_14hr, c_break, c_fuel, c_cycle, chunk) -> str | None:
        # Precedence: cycle > window (11hr/14hr) > break > fuel.
        if abs(c_cycle - chunk) <= EPS:
            return "cycle"
        if abs(c_11hr - chunk) <= EPS or abs(c_14hr - chunk) <= EPS:
            return "window"
        if abs(c_break - chunk) <= EPS:
            return "break"
        if abs(c_fuel - chunk) <= EPS:
            return "fuel"
        return None

    def _resolve_zero_chunk(self, c_11hr, c_14hr, c_break, c_fuel, c_cycle, fuel_stop_interval_mi, fuel_stop_duration_hr):
        # A constraint is already exhausted before any driving could occur
        # this iteration (e.g. cycle capacity used up by the preceding
        # on-duty activity). Resolve it without advancing the clock.
        if c_cycle <= EPS:
            self.insert_34hr_restart(fuel_stop_interval_mi)
        elif c_11hr <= EPS or c_14hr <= EPS:
            self.insert_10hr_reset(fuel_stop_interval_mi)
        elif c_break <= EPS:
            self.insert_30min_break()
        elif c_fuel <= EPS:
            self.insert_fuel_stop(fuel_stop_duration_hr)
        else:
            # Floating point guard: should not happen in practice.
            self.insert_30min_break()

    def _apply_binding(self, binding: str | None, fuel_stop_interval_mi: float, fuel_stop_duration_hr: float):
        if binding == "cycle":
            self.insert_34hr_restart(fuel_stop_interval_mi)
        elif binding == "window":
            self.insert_10hr_reset(fuel_stop_interval_mi)
        elif binding == "break":
            self.insert_30min_break()
        elif binding == "fuel":
            self.insert_fuel_stop(fuel_stop_duration_hr)
        # binding is None only when c_dist was the sole minimum, which is
        # already handled by the `remaining_hr <= EPS: break` above.


def plan_trip(
    leg1_distance_mi: float,
    leg1_duration_hr: float,
    leg2_distance_mi: float,
    leg2_duration_hr: float,
    current_cycle_used_hr: float,
    trip_start: datetime,
    pickup_location_name: str,
    dropoff_location_name: str,
    current_location_name: str = "Start",
    fuel_stop_interval_mi: float = 1000.0,
    fuel_stop_duration_hr: float = 0.5,
    pickup_duration_hr: float = 1.0,
    dropoff_duration_hr: float = 1.0,
) -> TripPlan:
    state = _EngineState(trip_start, current_cycle_used_hr, current_location_name)

    state.do_drive_activity(leg1_distance_mi, leg1_duration_hr, fuel_stop_interval_mi, fuel_stop_duration_hr)
    state.do_on_activity(pickup_duration_hr, pickup_location_name, "Pickup")
    state.do_drive_activity(leg2_distance_mi, leg2_duration_hr, fuel_stop_interval_mi, fuel_stop_duration_hr)
    state.do_on_activity(dropoff_duration_hr, dropoff_location_name, "Dropoff")

    total_distance_miles = leg1_distance_mi + leg2_distance_mi
    total_duration_hours = (state.t - trip_start).total_seconds() / 3600.0

    daily_logs_json = split_into_daily_sheets(
        state.segments,
        pickup_mile=leg1_distance_mi,
        total_distance_mi=total_distance_miles,
        current_location_name=current_location_name,
        pickup_location_name=pickup_location_name,
        dropoff_location_name=dropoff_location_name,
    )
    stops_summary = _build_stops_summary(
        state.segments, leg1_distance_mi, leg1_duration_hr, leg2_distance_mi, leg2_duration_hr,
    )

    return TripPlan(
        segments=state.segments,
        daily_logs_json=daily_logs_json,
        stops_summary=stops_summary,
        total_distance_miles=total_distance_miles,
        total_duration_hours=total_duration_hours,
    )


def _build_stops_summary(segments, leg1_distance_mi, leg1_duration_hr, leg2_distance_mi, leg2_duration_hr) -> dict:
    stops = []
    for seg in segments:
        stop_type = _STOP_TYPE_MAP.get((seg.status, seg.remark))
        if stop_type is None:
            continue
        stops.append({
            "type": stop_type,
            "location": seg.location,
            "arrival": seg.start.isoformat(),
            "departure": seg.end.isoformat(),
            "mile_marker": round(seg.start_mile, 1),
        })
    return {
        "legs": [
            {"from": "current", "to": "pickup", "distance_miles": round(leg1_distance_mi, 1), "duration_hours": round(leg1_duration_hr, 2)},
            {"from": "pickup", "to": "dropoff", "distance_miles": round(leg2_distance_mi, 1), "duration_hours": round(leg2_duration_hr, 2)},
        ],
        "stops": stops,
    }
