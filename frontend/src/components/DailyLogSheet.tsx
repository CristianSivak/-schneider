import DailyLogSheetGrid from './DailyLogSheetGrid'
import type { DailyLog, Trip } from '../types/trip'

function formatDate(dateStr: string): { month: string; day: string; year: string } {
  const [year, month, day] = dateStr.split('-')
  return { month, day, year }
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })
}

export default function DailyLogSheet({ trip, day }: { trip: Trip; day: DailyLog }) {
  const { month, day: dayOfMonth, year } = formatDate(day.date)

  const remarks = day.segments
    .filter((seg) => seg.remark)
    .map((seg) => `${formatTime(seg.start)} — ${seg.remark}${seg.location ? ` (${seg.location})` : ''}`)

  return (
    <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
      <div className="mb-4 flex items-baseline justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          Day {day.day_index} — Driver's Daily Log (24 hours)
        </h3>
        <span className="text-sm text-gray-500">
          {month} / {dayOfMonth} / {year}
        </span>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-4">
        <Field label="From" value={day.from_location} />
        <Field label="To" value={day.to_location} />
        <Field label="Total Miles Driving Today" value={day.total_miles_driving_today.toFixed(1)} />
        <Field label="Total Mileage Today" value={day.total_mileage_today.toFixed(1)} />
        <Field label="Driver" value={trip.driver_name} />
        <Field label="Carrier" value={trip.carrier_name} />
        <Field label="Truck/Tractor No." value={trip.truck_number} />
      </div>

      <DailyLogSheetGrid date={day.date} segments={day.segments} totals={day.totals} />

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">Remarks</h4>
          <ul className="space-y-0.5 text-xs text-gray-700">
            {remarks.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg bg-gray-50 p-3">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            70-Hour / 8-Day Recap
          </h4>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-700">
            <RecapRow label="On-duty hours today (lines 3+4)" value={day.recap.on_duty_hours_today} />
            <RecapRow label="Total cycle hours used" value={day.recap.cycle_used_hours_end_of_day} />
            <RecapRow label="Hours available tomorrow" value={day.recap.hours_available_tomorrow} />
            <RecapRow label="Hours available after 34-hr restart" value={day.recap.hours_available_after_restart} />
          </dl>
        </div>
      </div>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</div>
      <div className="text-gray-900">{value}</div>
    </div>
  )
}

function RecapRow({ label, value }: { label: string; value: number }) {
  return (
    <>
      <dt className="col-span-1">{label}</dt>
      <dd className="text-right font-semibold text-gray-900">{value.toFixed(1)}</dd>
    </>
  )
}
