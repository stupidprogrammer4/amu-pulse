/** The console is English-only, and operators compare timestamps across hosts. */
const dateTime = new Intl.DateTimeFormat('en-GB', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
})

const timeOnly = new Intl.DateTimeFormat('en-GB', {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
})

const relative = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : dateTime.format(date)
}

export function formatTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : timeOnly.format(date)
}

/** Milliseconds matter when two log lines share a second. */
export function formatMillis(value: string | null | undefined): string {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : `.${String(date.getMilliseconds()).padStart(3, '0')}`
}

const spans: [Intl.RelativeTimeFormatUnit, number][] = [
  ['second', 60],
  ['minute', 60],
  ['hour', 24],
  ['day', 30],
  ['month', 12],
  ['year', Number.POSITIVE_INFINITY],
]

export function formatRelative(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'

  let delta = (date.getTime() - Date.now()) / 1000
  for (const [unit, step] of spans) {
    if (Math.abs(delta) < step) return relative.format(Math.round(delta), unit)
    delta /= step
  }
  return relative.format(Math.round(delta), 'year')
}

export function formatNumber(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString('en-US') : '—'
}
