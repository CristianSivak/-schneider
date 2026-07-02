import axios from 'axios'
import { useEffect, useState } from 'react'
import { getTrip, listTrips, planTrip } from './api/client'
import ResultsLayout from './components/ResultsLayout'
import TripForm from './components/TripForm'
import TripHistory from './components/TripHistory'
import type { ApiError, Trip, TripListItem, TripPlanRequest } from './types/trip'

function App() {
  const [trip, setTrip] = useState<Trip | null>(null)
  const [history, setHistory] = useState<TripListItem[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<{ field?: string; message: string } | undefined>()

  useEffect(() => {
    refreshHistory()
  }, [])

  async function refreshHistory() {
    setIsLoadingHistory(true)
    try {
      setHistory(await listTrips())
    } catch {
      // History is a convenience feature; failing to load it shouldn't block trip planning.
    } finally {
      setIsLoadingHistory(false)
    }
  }

  async function handleSubmit(payload: TripPlanRequest) {
    setIsSubmitting(true)
    setError(undefined)
    try {
      const result = await planTrip(payload)
      setTrip(result)
      refreshHistory()
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data) {
        const data = err.response.data as ApiError
        setError({ field: data.field, message: data.message ?? 'Something went wrong.' })
      } else {
        setError({ message: 'Could not reach the server. Please try again.' })
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleSelectHistoryTrip(id: string) {
    try {
      setTrip(await getTrip(id))
    } catch {
      setError({ message: 'Could not load that trip.' })
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b-4 border-brand-500 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center gap-3">
          <img src="/schneider-logo.png" alt="Schneider" className="h-10 w-10 rounded" />
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              ELD Trip Planner
            </h1>
            <p className="text-sm text-gray-500">Route planning and FMCSA daily log sheets for property-carrying drivers</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl p-6">
        <TripForm onSubmit={handleSubmit} isSubmitting={isSubmitting} fieldError={error} />

        <div className="mt-6 grid gap-6 lg:grid-cols-[260px_1fr]">
          <TripHistory trips={history} selectedId={trip?.id} onSelect={handleSelectHistoryTrip} isLoading={isLoadingHistory} />

          <div>
            {isSubmitting && (
              <div className="flex items-center justify-center rounded-xl bg-white p-12 shadow-sm ring-1 ring-gray-200">
                <p className="text-sm text-gray-500">Planning trip — geocoding locations and computing HOS schedule…</p>
              </div>
            )}
            {!isSubmitting && trip && <ResultsLayout trip={trip} />}
            {!isSubmitting && !trip && (
              <div className="flex items-center justify-center rounded-xl bg-white p-12 shadow-sm ring-1 ring-gray-200">
                <p className="text-sm text-gray-500">Plan a trip above to see the route map and daily log sheets.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
