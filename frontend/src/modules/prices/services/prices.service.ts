import { api } from '@/infra/http'
import type { Instrument, PriceHistory, PriceHistoryQuery, PriceQuote } from '../types'

/** Backend paths this module owns. */
const endpoints = {
  instruments: '/instruments',
  instrument: (id: string) => `/instruments/${id}`,
  latest: '/prices/latest',
  history: '/prices/history',
} as const

export const pricesService = {
  listInstruments: () => api.get<Instrument[]>(endpoints.instruments),

  getInstrument: (id: string) => api.get<Instrument>(endpoints.instrument(id)),

  /** Latest quote per symbol. Omit `symbols` for everything tracked. */
  latest: (symbols?: string[]) =>
    api.get<PriceQuote[]>(endpoints.latest, symbols ? { symbols: symbols.join(',') } : undefined),

  history: (query: PriceHistoryQuery) => api.get<PriceHistory>(endpoints.history, query),
}
