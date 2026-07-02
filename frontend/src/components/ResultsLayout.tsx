import DailyLogSheet from './DailyLogSheet'
import RouteMap from './RouteMap'
import type { Trip } from '../types/trip'

export default function ResultsLayout({ trip }: { trip: Trip }) {
  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {trip.pickup_location} → {trip.dropoff_location}
            </h2>
            <p className="text-sm text-gray-500">Current location: {trip.current_location}</p>
          </div>
          <div className="flex gap-6 text-right text-sm">
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-400">Distance</div>
              <div className="font-semibold text-gray-900">
                {trip.total_distance_miles != null ? `${trip.total_distance_miles.toFixed(0)} mi` : '—'}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-400">Total trip time</div>
              <div className="font-semibold text-gray-900">
                {trip.total_duration_hours != null
                  ? `${trip.total_duration_hours.toFixed(1)} hr (${(trip.total_duration_hours / 24).toFixed(1)} days)`
                  : '—'}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-400">Daily logs</div>
              <div className="font-semibold text-gray-900">{trip.daily_logs?.length ?? 0}</div>
            </div>
          </div>
        </div>
      </div>

      <RouteMap trip={trip} />

      <div className="space-y-6">
        {trip.daily_logs?.map((day) => <DailyLogSheet key={day.day_index} trip={trip} day={day} />)}
      </div>
    </div>
  )
}
