import { useState, type FormEvent } from 'react'
import LocationAutocomplete from './LocationAutocomplete'
import type { TripPlanRequest } from '../types/trip'

interface FieldError {
  field?: string
  message: string
}

interface TripFormProps {
  onSubmit: (payload: TripPlanRequest) => void
  isSubmitting: boolean
  fieldError?: FieldError
}

export default function TripForm({ onSubmit, isSubmitting, fieldError }: TripFormProps) {
  const [currentLocation, setCurrentLocation] = useState('')
  const [pickupLocation, setPickupLocation] = useState('')
  const [dropoffLocation, setDropoffLocation] = useState('')
  const [cycleUsed, setCycleUsed] = useState('')
  const [driverName, setDriverName] = useState('')
  const [carrierName, setCarrierName] = useState('')
  const [truckNumber, setTruckNumber] = useState('')
  const [validationError, setValidationError] = useState('')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setValidationError('')

    if (!currentLocation.trim() || !pickupLocation.trim() || !dropoffLocation.trim()) {
      setValidationError('All three location fields are required.')
      return
    }

    const cycle = parseFloat(cycleUsed)
    if (Number.isNaN(cycle) || cycle < 0 || cycle > 70) {
      setValidationError('Current Cycle Used must be a number between 0 and 70.')
      return
    }

    onSubmit({
      current_location: currentLocation.trim(),
      pickup_location: pickupLocation.trim(),
      dropoff_location: dropoffLocation.trim(),
      current_cycle_used_hrs: cycle,
      ...(driverName.trim() && { driver_name: driverName.trim() }),
      ...(carrierName.trim() && { carrier_name: carrierName.trim() }),
      ...(truckNumber.trim() && { truck_number: truckNumber.trim() }),
    })
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-auto max-w-2xl space-y-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200"
    >
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Plan a Trip</h2>
        <p className="text-sm text-gray-500">
          Enter trip details to get route stops and daily ELD log sheets.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <LocationAutocomplete
          label="Current Location"
          value={currentLocation}
          onChange={setCurrentLocation}
          placeholder="Chicago, IL"
          error={fieldError?.field === 'current_location' ? fieldError.message : undefined}
        />
        <LocationAutocomplete
          label="Pickup Location"
          value={pickupLocation}
          onChange={setPickupLocation}
          placeholder="Chicago, IL"
          error={fieldError?.field === 'pickup_location' ? fieldError.message : undefined}
        />
        <LocationAutocomplete
          label="Dropoff Location"
          value={dropoffLocation}
          onChange={setDropoffLocation}
          placeholder="Indianapolis, IN"
          error={fieldError?.field === 'dropoff_location' ? fieldError.message : undefined}
        />
        <Field
          label="Current Cycle Used (Hrs)"
          value={cycleUsed}
          onChange={setCycleUsed}
          type="number"
          placeholder="10"
        />
      </div>

      <details className="rounded-lg border border-gray-200 p-3">
        <summary className="cursor-pointer text-sm font-medium text-gray-700">
          Optional: driver &amp; carrier details
        </summary>
        <div className="mt-3 grid gap-4 sm:grid-cols-3">
          <Field label="Driver Name" value={driverName} onChange={setDriverName} placeholder="Driver" />
          <Field label="Carrier Name" value={carrierName} onChange={setCarrierName} placeholder="N/A" />
          <Field label="Truck Number" value={truckNumber} onChange={setTruckNumber} placeholder="N/A" />
        </div>
      </details>

      {validationError && <p className="text-sm text-red-600">{validationError}</p>}
      {fieldError && !fieldError.field && <p className="text-sm text-red-600">{fieldError.message}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? 'Planning trip…' : 'Plan Trip'}
      </button>
    </form>
  )
}

function Field({
  label,
  value,
  onChange,
  error,
  placeholder,
  type = 'text',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  error?: string
  placeholder?: string
  type?: string
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-gray-700">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? 'border-red-400' : 'border-gray-300'
        }`}
      />
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  )
}
