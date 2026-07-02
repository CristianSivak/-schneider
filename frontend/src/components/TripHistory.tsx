import type { TripListItem } from '../types/trip'

export default function TripHistory({
  trips,
  selectedId,
  onSelect,
  isLoading,
}: {
  trips: TripListItem[]
  selectedId?: string
  onSelect: (id: string) => void
  isLoading: boolean
}) {
  return (
    <aside className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">Recent Trips</h2>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      {!isLoading && trips.length === 0 && <p className="text-sm text-gray-400">No trips planned yet.</p>}
      <ul className="space-y-1">
        {trips.map((t) => (
          <li key={t.id}>
            <button
              type="button"
              onClick={() => onSelect(t.id)}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-gray-50 ${
                selectedId === t.id ? 'bg-brand-50 ring-1 ring-brand-200' : ''
              }`}
            >
              <div className="font-medium text-gray-900">
                {t.pickup_location} → {t.dropoff_location}
              </div>
              <div className="text-xs text-gray-500">
                {new Date(t.created_at).toLocaleDateString()}
                {t.total_distance_miles != null && ` · ${t.total_distance_miles.toFixed(0)} mi`}
              </div>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  )
}
