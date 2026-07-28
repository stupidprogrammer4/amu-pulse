import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import type { ApiRequestError } from '@/infra/http/api-error'
import type { ChartWindow } from '@/modules/prices/types'
import { analysisService } from '../services/analysis.service'
import type { Analysis } from '../types'
import { toVerdict } from '../utils/score'

export const useAnalysisStore = defineStore('analysis', () => {
  const current = ref<Analysis | null>(null)
  const isLoading = ref(false)
  const error = ref<ApiRequestError | null>(null)
  /** Analysis ids the user has already rated, so the form isn't offered twice. */
  const ratedIds = ref<Set<string>>(new Set())

  const verdict = computed(() => (current.value ? toVerdict(current.value.score) : null))
  const canRate = computed(() => !!current.value && !ratedIds.value.has(current.value.id))

  async function fetchLatest(symbol: string, window: ChartWindow = '7d'): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      current.value = await analysisService.latest(symbol, window)
    } catch (caught) {
      error.value = caught as ApiRequestError
    } finally {
      isLoading.value = false
    }
  }

  async function submitFeedback(accurate: boolean, note?: string): Promise<boolean> {
    if (!current.value) return false
    const analysisId = current.value.id
    try {
      await analysisService.sendFeedback({ analysis_id: analysisId, accurate, note })
      ratedIds.value = new Set(ratedIds.value).add(analysisId)
      return true
    } catch (caught) {
      error.value = caught as ApiRequestError
      return false
    }
  }

  return { current, isLoading, error, ratedIds, verdict, canRate, fetchLatest, submitFeedback }
})
