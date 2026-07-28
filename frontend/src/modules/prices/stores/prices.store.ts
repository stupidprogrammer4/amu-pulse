import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import type { ApiRequestError } from '@/infra/http/api-error'
import { pricesService } from '../services/prices.service'
import type { ChartWindow, PriceHistory, PriceQuote } from '../types'

export const usePricesStore = defineStore('prices', () => {
  const quotes = ref<PriceQuote[]>([])
  const histories = ref<Record<string, PriceHistory>>({})
  const isLoading = ref(false)
  const error = ref<ApiRequestError | null>(null)
  const lastUpdatedAt = ref<string | null>(null)

  const quoteBySymbol = computed(
    () => (symbol: string) => quotes.value.find((quote) => quote.symbol === symbol) ?? null,
  )

  const hasQuotes = computed(() => quotes.value.length > 0)

  function historyKey(symbol: string, window: ChartWindow): string {
    return `${symbol}:${window}`
  }

  async function fetchQuotes(symbols?: string[]): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      quotes.value = await pricesService.latest(symbols)
      lastUpdatedAt.value = new Date().toISOString()
    } catch (caught) {
      error.value = caught as ApiRequestError
    } finally {
      isLoading.value = false
    }
  }

  /** Cached per symbol+window; pass `force` to refetch after a range change. */
  async function fetchHistory(
    symbol: string,
    window: ChartWindow,
    force = false,
  ): Promise<PriceHistory | null> {
    const key = historyKey(symbol, window)
    if (!force && histories.value[key]) return histories.value[key]

    try {
      const history = await pricesService.history({ symbol, window })
      histories.value = { ...histories.value, [key]: history }
      return history
    } catch (caught) {
      error.value = caught as ApiRequestError
      return null
    }
  }

  function getHistory(symbol: string, window: ChartWindow): PriceHistory | null {
    return histories.value[historyKey(symbol, window)] ?? null
  }

  return {
    quotes,
    histories,
    isLoading,
    error,
    lastUpdatedAt,
    quoteBySymbol,
    hasQuotes,
    fetchQuotes,
    fetchHistory,
    getHistory,
  }
})
