import axios from 'axios'
import type { LocationSuggestion, Trip, TripListItem, TripPlanRequest } from '../types/trip'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

const client = axios.create({ baseURL: API_URL })

export async function planTrip(payload: TripPlanRequest): Promise<Trip> {
  const { data } = await client.post<Trip>('/trips/plan/', payload)
  return data
}

export async function searchLocations(query: string, signal?: AbortSignal): Promise<LocationSuggestion[]> {
  const { data } = await client.get<{ results: LocationSuggestion[] }>('/locations/search/', {
    params: { q: query },
    signal,
  })
  return data.results
}

export async function listTrips(): Promise<TripListItem[]> {
  const { data } = await client.get<TripListItem[]>('/trips/')
  return data
}

export async function getTrip(id: string): Promise<Trip> {
  const { data } = await client.get<Trip>(`/trips/${id}/`)
  return data
}
