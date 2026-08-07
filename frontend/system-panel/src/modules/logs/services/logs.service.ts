import { requestPaged, type Paged } from '@/infra/http'

import type {
  LogChartMeta,
  LogChartOut,
  LogChartQuery,
  LogMeta,
  LogOut,
  LogSearchQuery,
} from '../types'

/** Drops empty filters so the backend sees an absent parameter, not an empty one. */
function pruned(query: LogSearchQuery): Record<string, unknown> {
  const params: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === '') continue
    if (Array.isArray(value) && value.length === 0) continue
    params[key] = value
  }
  return params
}

export const logsService = {
  /** One page of the log index, with the facet counts the filter bar renders from. */
  search(query: LogSearchQuery): Promise<Paged<LogOut, LogMeta>> {
    return requestPaged<LogOut, LogMeta>({
      method: 'get',
      url: '/panel/logs',
      params: pruned(query),
      // Repeated keys — `levels=error&levels=critical` — are what FastAPI reads.
      paramsSerializer: { indexes: null },
    })
  },

  /** Log volume over time for one container, bucketed by the backend. */
  chart({ bucket, container, level }: LogChartQuery): Promise<Paged<LogChartOut, LogChartMeta>> {
    return requestPaged<LogChartOut, LogChartMeta>({
      method: 'get',
      url: `/panel/logs/chart/${bucket}`,
      params: { container, ...(level ? { level } : {}) },
    })
  },

  /**
   * Every line the backend emitted under one request id. Read through the paged
   * helper because the envelope allows a bare object where a single line came
   * back, and the trace view only ever wants a list.
   */
  async trace(requestId: string): Promise<LogOut[]> {
    const { data } = await requestPaged<LogOut, null>({
      method: 'get',
      url: `/panel/logs/traces/${encodeURIComponent(requestId)}`,
    })
    return data
  },
}
