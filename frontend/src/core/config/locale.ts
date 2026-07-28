/**
 * The app is Persian-only: one locale, RTL, Jalali dates.
 * `fa-IR` makes Intl emit Persian digits (۱۲۳) and the Persian calendar
 * without any extra configuration.
 */
export const LOCALE = 'fa-IR'
export const DIRECTION = 'rtl'

/** Prices are quoted in Toman, which has no ISO code — hence the manual suffix. */
export const CURRENCY_LABEL = 'تومان'
export const GLOBAL_CURRENCY = 'USD'
