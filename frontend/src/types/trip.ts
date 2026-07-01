export type DutyStatus = 'OFF' | 'SB' | 'D' | 'ON'

export interface DailyLogSegment {
  status: DutyStatus
  start: string
  end: string
  location: string
  remark: string
}

export interface DailyLogRecap {
  on_duty_hours_today: number
  total_lines_3_and_4: number
  cycle_used_hours_end_of_day: number
  hours_available_tomorrow: number
  hours_available_after_restart: number
}

export interface DailyLog {
  date: string
  day_index: number
  from_location: string
  to_location: string
  total_miles_driving_today: number
  total_mileage_today: number
  segments: DailyLogSegment[]
  totals: Record<DutyStatus, number>
  recap: DailyLogRecap
}

export type StopType = 'pickup' | 'dropoff' | 'fuel' | 'rest_10hr' | 'restart_34hr' | 'break_30min'

export interface RouteStop {
  type: StopType
  location: string
  arrival: string
  departure: string
  mile_marker: number
}

export interface RouteLeg {
  from: string
  to: string
  distance_miles: number
  duration_hours: number
}

export interface RouteSummary {
  legs: RouteLeg[]
  stops: RouteStop[]
}

export interface RouteGeometry {
  type: string
  coordinates: [number, number][] // [lng, lat]
}

export interface Trip {
  id: string
  created_at: string
  current_location: string
  current_location_lat: number | null
  current_location_lng: number | null
  pickup_location: string
  pickup_location_lat: number | null
  pickup_location_lng: number | null
  dropoff_location: string
  dropoff_location_lat: number | null
  dropoff_location_lng: number | null
  current_cycle_used_hrs: number
  driver_name: string
  carrier_name: string
  truck_number: string
  total_distance_miles: number | null
  total_duration_hours: number | null
  route_geometry: RouteGeometry | null
  route_summary: RouteSummary | null
  daily_logs: DailyLog[] | null
  status: 'pending' | 'completed' | 'failed'
  error_message: string
}

export interface TripListItem {
  id: string
  created_at: string
  current_location: string
  pickup_location: string
  dropoff_location: string
  total_distance_miles: number | null
  total_duration_hours: number | null
  status: string
}

export interface TripPlanRequest {
  current_location: string
  pickup_location: string
  dropoff_location: string
  current_cycle_used_hrs: number
  driver_name?: string
  carrier_name?: string
  truck_number?: string
}

export interface ApiError {
  error: string
  message: string
  field?: string
}
