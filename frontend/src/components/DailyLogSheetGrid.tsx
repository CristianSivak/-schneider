import type { DailyLogSegment, DutyStatus } from '../types/trip'

const ROW_ORDER: DutyStatus[] = ['OFF', 'SB', 'D', 'ON']
const ROW_LABELS: Record<DutyStatus, string> = {
  OFF: '1. Off Duty',
  SB: '2. Sleeper Berth',
  D: '3. Driving',
  ON: '4. On Duty (Not Driving)',
}

const LABEL_WIDTH = 190
const HOUR_WIDTH = 50
const GRID_WIDTH = 24 * HOUR_WIDTH
const ROW_HEIGHT = 36
const GRID_TOP = 28
const GRID_HEIGHT = ROW_ORDER.length * ROW_HEIGHT
const TOTALS_WIDTH = 56
const SVG_WIDTH = LABEL_WIDTH + GRID_WIDTH + TOTALS_WIDTH
const SVG_HEIGHT = GRID_TOP + GRID_HEIGHT + 6

const HOUR_LABELS = [
  'Mid-\nnight', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
  'Noon', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', 'Mid-\nnight',
]

function minutesFromMidnight(iso: string, dateStr: string): number {
  const t = new Date(iso).getTime()
  const dayStart = new Date(`${dateStr}T00:00:00Z`).getTime()
  return (t - dayStart) / 60000
}

function xForMinutes(minutes: number): number {
  const clamped = Math.min(1440, Math.max(0, minutes))
  return LABEL_WIDTH + (clamped / 1440) * GRID_WIDTH
}

function yForStatus(status: DutyStatus): number {
  return GRID_TOP + ROW_ORDER.indexOf(status) * ROW_HEIGHT + ROW_HEIGHT / 2
}

function buildStepPath(segments: DailyLogSegment[], dateStr: string): string {
  if (segments.length === 0) return ''
  const commands: string[] = []
  segments.forEach((seg, i) => {
    const xStart = xForMinutes(minutesFromMidnight(seg.start, dateStr))
    const xEnd = xForMinutes(minutesFromMidnight(seg.end, dateStr))
    const y = yForStatus(seg.status)
    if (i === 0) commands.push(`M ${xStart} ${y}`)
    commands.push(`L ${xEnd} ${y}`)
    const next = segments[i + 1]
    if (next) {
      const yNext = yForStatus(next.status)
      if (yNext !== y) commands.push(`L ${xEnd} ${yNext}`)
    }
  })
  return commands.join(' ')
}

export default function DailyLogSheetGrid({
  date,
  segments,
  totals,
}: {
  date: string
  segments: DailyLogSegment[]
  totals: Record<DutyStatus, number>
}) {
  const stepPath = buildStepPath(segments, date)

  return (
    <svg
      viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
      width="100%"
      className="select-none"
      role="img"
      aria-label={`Driver's daily log grid for ${date}`}
    >
      {/* Hour gridlines + labels */}
      {Array.from({ length: 25 }, (_, h) => {
        const x = LABEL_WIDTH + h * HOUR_WIDTH
        return (
          <g key={h}>
            <line x1={x} y1={GRID_TOP} x2={x} y2={GRID_TOP + GRID_HEIGHT} stroke="#374151" strokeWidth={1} />
            {HOUR_LABELS[h].split('\n').map((line, li) => (
              <text
                key={li}
                x={x}
                y={GRID_TOP - 16 + li * 9}
                fontSize={8}
                textAnchor="middle"
                fill="#374151"
              >
                {line}
              </text>
            ))}
          </g>
        )
      })}

      {/* Quarter-hour tick marks */}
      {Array.from({ length: 24 * 4 + 1 }, (_, q) => q)
        .filter((q) => q % 4 !== 0)
        .map((q) => {
          const x = LABEL_WIDTH + q * (HOUR_WIDTH / 4)
          const major = q % 2 === 0
          return (
            <line
              key={q}
              x1={x}
              y1={GRID_TOP}
              x2={x}
              y2={GRID_TOP + GRID_HEIGHT}
              stroke="#d1d5db"
              strokeWidth={major ? 0.75 : 0.5}
            />
          )
        })}

      {/* Row bands + labels */}
      {ROW_ORDER.map((status, i) => {
        const y = GRID_TOP + i * ROW_HEIGHT
        return (
          <g key={status}>
            <rect x={LABEL_WIDTH} y={y} width={GRID_WIDTH} height={ROW_HEIGHT} fill="none" stroke="#374151" strokeWidth={1} />
            <text x={LABEL_WIDTH - 8} y={y + ROW_HEIGHT / 2 + 4} fontSize={11} textAnchor="end" fill="#111827">
              {ROW_LABELS[status]}
            </text>
            <text
              x={LABEL_WIDTH + GRID_WIDTH + TOTALS_WIDTH - 8}
              y={y + ROW_HEIGHT / 2 + 4}
              fontSize={11}
              textAnchor="end"
              fill="#111827"
              fontWeight={600}
            >
              {totals[status].toFixed(2)}
            </text>
          </g>
        )
      })}

      <rect
        x={LABEL_WIDTH + GRID_WIDTH}
        y={GRID_TOP}
        width={TOTALS_WIDTH}
        height={GRID_HEIGHT}
        fill="none"
        stroke="#374151"
        strokeWidth={1}
      />
      <text
        x={LABEL_WIDTH + GRID_WIDTH + TOTALS_WIDTH / 2}
        y={GRID_TOP - 10}
        fontSize={8}
        textAnchor="middle"
        fill="#374151"
      >
        Total Hours
      </text>

      {/* Duty-status step line */}
      <path d={stepPath} fill="none" stroke="#1d4ed8" strokeWidth={2.5} strokeLinejoin="round" />
    </svg>
  )
}
