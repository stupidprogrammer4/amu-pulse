import { api } from '@/infra/http'
import type { ChartWindow } from '@/modules/prices/types'
import type { Analysis, AnalysisFeedback } from '../types'

const endpoints = {
  latest: '/analysis/latest',
  list: '/analysis',
  detail: (id: string) => `/analysis/${id}`,
  feedback: (id: string) => `/analysis/${id}/feedback`,
} as const

export const analysisService = {
  latest: (symbol: string, window: ChartWindow = '7d') =>
    api.get<Analysis>(endpoints.latest, { symbol, window }),

  history: (symbol: string, limit = 20) => api.get<Analysis[]>(endpoints.list, { symbol, limit }),

  detail: (id: string) => api.get<Analysis>(endpoints.detail(id)),

  /** Records whether a past read-out matched reality; feeds the evaluation loop. */
  sendFeedback: (feedback: AnalysisFeedback) =>
    api.post<void>(endpoints.feedback(feedback.analysis_id), {
      accurate: feedback.accurate,
      note: feedback.note,
    }),
}
