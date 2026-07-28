/** Instruments amu-pulse tracks. Extend as source adapters land. */
export type InstrumentSymbol = 'XAU' | 'GOLD_18K' | 'GOLD_24K' | 'COIN_EMAMI' | 'USD'

export interface Instrument {
  id: string
  symbol: InstrumentSymbol | string
  name: string
  unit: string
  purity?: number | null
}

export interface Price {
  instrument_id: string
  symbol: string
  /** Buy-side quote, in the instrument's currency. */
  buy: number
  /** Sell-side quote. */
  sell: number
  /** Local premium over the global-derived price ("حباب"), as a ratio. */
  premium?: number | null
  source: string
  /** ISO-8601 UTC timestamp. */
  observed_at: string
}

export interface PriceChange {
  absolute: number
  /** Fractional change, e.g. 0.031 for +3.1%. */
  percent: number
}

export interface PriceQuote extends Price {
  change_24h?: PriceChange | null
}

/** A single point on a history chart. */
export interface PricePoint {
  t: string
  open: number
  high: number
  low: number
  close: number
}

export type ChartWindow = '1d' | '7d' | '30d' | '90d' | '1y' | 'max'

export interface PriceHistoryQuery {
  symbol: string
  window: ChartWindow
  /** Bucket size, e.g. '1h' or '1d'. The backend picks a default when omitted. */
  interval?: string
}

export interface PriceHistory {
  symbol: string
  window: ChartWindow
  interval: string
  points: PricePoint[]
}

/** Persian display names, kept beside the symbols they label. */
export const symbolLabels: Record<string, string> = {
  GOLD_18K: 'طلای ۱۸ عیار',
  GOLD_24K: 'طلای ۲۴ عیار',
  COIN_EMAMI: 'سکه امامی',
  XAU: 'انس جهانی',
  USD: 'دلار',
}

export const chartWindowLabels: Record<ChartWindow, string> = {
  '1d': '۱ روز',
  '7d': '۷ روز',
  '30d': '۳۰ روز',
  '90d': '۹۰ روز',
  '1y': '۱ سال',
  max: 'کل',
}
