import L from 'leaflet'
import { useEffect } from 'react'
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, useMap } from 'react-leaflet'
import type { RouteStop, StopType, Trip } from '../types/trip'

const STOP_COLORS: Record<StopType, string> = {
  pickup: '#16a34a',
  dropoff: '#dc2626',
  fuel: '#f97316',
  rest_10hr: '#2563eb',
  restart_34hr: '#7c3aed',
  break_30min: '#eab308',
}

const STOP_LABELS: Record<StopType, string> = {
  pickup: 'Pickup',
  dropoff: 'Dropoff',
  fuel: 'Fuel stop',
  rest_10hr: '10-hour rest',
  restart_34hr: '34-hour restart',
  break_30min: '30-minute break',
}

function FitBounds({ positions }: { positions: [number, number][] }) {
  const map = useMap()
  useEffect(() => {
    if (positions.length === 0) return
    map.fitBounds(L.latLngBounds(positions), { padding: [40, 40] })
  }, [positions, map])
  return null
}

// Fuel/rest/break stops aren't independently geocoded (only pickup/dropoff are)
// -- interpolate their position along the route polyline using mile_marker.
function stopPosition(stop: RouteStop, trip: Trip): [number, number] | null {
  if (stop.type === 'pickup' && trip.pickup_location_lat != null && trip.pickup_location_lng != null) {
    return [trip.pickup_location_lat, trip.pickup_location_lng]
  }
  if (stop.type === 'dropoff' && trip.dropoff_location_lat != null && trip.dropoff_location_lng != null) {
    return [trip.dropoff_location_lat, trip.dropoff_location_lng]
  }
  if (!trip.route_geometry || !trip.total_distance_miles) return null
  const coords = trip.route_geometry.coordinates
  if (coords.length === 0) return null
  const fraction = Math.min(1, Math.max(0, stop.mile_marker / trip.total_distance_miles))
  const idx = Math.round(fraction * (coords.length - 1))
  const [lng, lat] = coords[idx]
  return [lat, lng]
}

export default function RouteMap({ trip }: { trip: Trip }) {
  if (!trip.route_geometry || !trip.route_summary) return null

  const routePositions: [number, number][] = trip.route_geometry.coordinates.map(([lng, lat]) => [lat, lng])
  const allPositions: [number, number][] = [...routePositions]
  if (trip.current_location_lat != null && trip.current_location_lng != null) {
    allPositions.push([trip.current_location_lat, trip.current_location_lng])
  }
  const center = routePositions[Math.floor(routePositions.length / 2)] ?? [39.8283, -98.5795]

  return (
    <div className="overflow-hidden rounded-xl shadow-sm ring-1 ring-gray-200">
      <MapContainer center={center} zoom={5} style={{ height: '420px', width: '100%' }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={routePositions} pathOptions={{ color: '#2563eb', weight: 4 }} />

        {trip.current_location_lat != null && trip.current_location_lng != null && (
          <CircleMarker
            center={[trip.current_location_lat, trip.current_location_lng]}
            radius={8}
            pathOptions={{ color: '#111827', fillColor: '#111827', fillOpacity: 1 }}
          >
            <Popup>
              <div className="text-sm">
                <div className="font-semibold">Current location</div>
                <div>{trip.current_location}</div>
              </div>
            </Popup>
          </CircleMarker>
        )}

        {trip.route_summary.stops.map((stop, i) => {
          const position = stopPosition(stop, trip)
          if (!position) return null
          const color = STOP_COLORS[stop.type]
          return (
            <CircleMarker
              key={i}
              center={position}
              radius={7}
              pathOptions={{ color, fillColor: color, fillOpacity: 1 }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-semibold">{STOP_LABELS[stop.type]}</div>
                  <div>{stop.location}</div>
                  <div>Mile {stop.mile_marker.toFixed(0)}</div>
                  <div>{new Date(stop.arrival).toLocaleString()}</div>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}

        <FitBounds positions={allPositions} />
      </MapContainer>
    </div>
  )
}
