import axios from 'axios'
import type { Trip, TripListItem, TripPlanRequest } from '../types/trip'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

const client = axios.create({ baseURL: API_URL })

export async function planTrip(payload: TripPlanRequest): Promise<Trip> {
  const { data } = await client.post<Trip>('/trips/plan/', payload)
  return data
}

export async function listTrips(): Promise<TripListItem[]> {
  const { data } = await client.get<TripListItem[]>('/trips/')
  return data
}

export async function getTrip(id: string): Promise<Trip> {
  const { data } = await client.get<Trip>(`/trips/${id}/`)
  return data
}
