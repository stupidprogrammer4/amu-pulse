import { CURRENCY_LABEL, GLOBAL_CURRENCY, LOCALE } from '@/core/config/locale'

export function formatNumber(value: number, fractionDigits = 0, locale = LOCALE): string {
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value)
}

/** Toman amounts: grouped Persian digits plus the unit, e.g. `۳٬۴۵۰٬۰۰۰ تومان`. */
export function formatToman(value: number, locale = LOCALE): string {
  return `${formatNumber(value, 0, locale)} ${CURRENCY_LABEL}`
}

/** Global quotes stay in dollars — used for the ounce price and the USD rate. */
export function formatUsd(value: number, locale = LOCALE): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: GLOBAL_CURRENCY,
    maximumFractionDigits: 2,
  }).format(value)
}

/** `0.031` → `‎+۳٫۱۰٪`. The sign is always shown so direction reads at a glance. */
export function formatPercent(ratio: number, fractionDigits = 2, locale = LOCALE): string {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    signDisplay: 'exceptZero',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(ratio)
}

/** Jalali date + time, which `fa-IR` gives us by default. */
export function formatDateTime(iso: string, locale = LOCALE): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(
    new Date(iso),
  )
}

export function formatTime(iso: string, locale = LOCALE): string {
  return new Intl.DateTimeFormat(locale, { timeStyle: 'short' }).format(new Date(iso))
}

/** «۵ دقیقه پیش» — relative wording, handled natively by Intl. */
export function formatRelativeTime(iso: string, locale = LOCALE): string {
  const deltaSeconds = (new Date(iso).getTime() - Date.now()) / 1000
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ['year', 31536000],
    ['month', 2592000],
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
    ['second', 1],
  ]

  const formatter = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })
  for (const [unit, seconds] of units) {
    if (Math.abs(deltaSeconds) >= seconds || unit === 'second') {
      return formatter.format(Math.round(deltaSeconds / seconds), unit)
    }
  }
  return formatter.format(0, 'second')
}
