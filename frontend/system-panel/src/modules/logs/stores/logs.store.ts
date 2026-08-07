import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError, type PagerMeta } from '@/infra/http'

import { logsService } from '../services/logs.service'
import type { LogBucket, LogChartOut, LogLevel, LogMeta, LogOut } from '../types'

/** The filter set, kept apart from the results so a reset is one assignment. */
export interface LogFilters {
  q: string
  levels: LogLevel[]
  loggers: string[]
  containers: string[]
  requestId: string
  fromTime: string
  toTime: string
}

function emptyFilters(): LogFilters {
  return { q: '', levels: [], loggers: [], containers: [], requestId: '', fromTime: '', toTime: '' }
}

/** A facet map turned into the sorted, count-bearing list the filter bar renders. */
function facets(counts: Record<string, number> | undefined): { value: string; count: number }[] {
  return Object.entries(counts ?? {})
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value))
}

export const useLogsStore = defineStore('logs', () => {
  const filters = ref<LogFilters>(emptyFilters())
  const page = ref(1)
  const perPage = ref(20)

  const entries = ref<LogOut[]>([])
  const meta = ref<LogMeta | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const loadedAt = ref<string | null>(null)

  const chart = ref<LogChartOut | null>(null)
  const chartContainers = ref<string[]>([])
  const chartBuckets = ref<LogBucket[]>([])
  const chartBucket = ref<LogBucket>('1h')
  const chartContainer = ref('')
  const chartLevel = ref<LogLevel | ''>('')
  const chartLoading = ref(false)
  const chartError = ref<string | null>(null)

  const pager = computed<PagerMeta | null>(() => meta.value?.pager ?? null)
  const levelFacets = computed(() => facets(meta.value?.levels))
  const loggerFacets = computed(() => facets(meta.value?.loggers))
  const containerFacets = computed(() => facets(meta.value?.containers))

  const activeFilterCount = computed(() => {
    const current = filters.value
    return (
      (current.q ? 1 : 0) +
      current.levels.length +
      current.loggers.length +
      current.containers.length +
      (current.requestId ? 1 : 0) +
      (current.fromTime ? 1 : 0) +
      (current.toTime ? 1 : 0)
    )
  })

  function message(cause: unknown, fallback: string): string {
    return cause instanceof ApiError ? cause.message : fallback
  }

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    const current = filters.value
    try {
      const result = await logsService.search({
        q: current.q.trim() || undefined,
        levels: current.levels.length ? current.levels : undefined,
        loggers: current.loggers.length ? current.loggers : undefined,
        containers: current.containers.length ? current.containers : undefined,
        request_id: current.requestId.trim() || undefined,
        from_time: current.fromTime ? new Date(current.fromTime).toISOString() : undefined,
        to_time: current.toTime ? new Date(current.toTime).toISOString() : undefined,
        page: page.value,
        per_page: perPage.value,
      })
      entries.value = result.data
      meta.value = result.meta
      loadedAt.value = new Date().toISOString()
      // The chart needs a container and the search response is what knows which
      // ones exist, so seed it from the first read rather than a second call.
      if (!chartContainer.value) {
        chartContainer.value = containerFacets.value[0]?.value ?? ''
      }
    } catch (cause) {
      error.value = message(cause, 'The logs could not be read.')
      entries.value = []
      meta.value = null
    } finally {
      loading.value = false
    }
  }

  /** Any filter change resets to page one — page 4 of a different query is noise. */
  async function apply(next: Partial<LogFilters>): Promise<void> {
    filters.value = { ...filters.value, ...next }
    page.value = 1
    await load()
  }

  async function reset(): Promise<void> {
    filters.value = emptyFilters()
    page.value = 1
    await load()
  }

  async function goToPage(next: number): Promise<void> {
    if (next === page.value) return
    page.value = next
    await load()
  }

  async function setPerPage(next: number): Promise<void> {
    if (next === perPage.value) return
    perPage.value = next
    page.value = 1
    await load()
  }

  async function loadChart(): Promise<void> {
    if (!chartContainer.value) {
      chart.value = null
      return
    }
    chartLoading.value = true
    chartError.value = null
    try {
      const result = await logsService.chart({
        bucket: chartBucket.value,
        container: chartContainer.value,
        level: chartLevel.value || undefined,
      })
      chart.value = result.data[0] ?? null
      if (result.meta?.containers?.length) chartContainers.value = result.meta.containers
      if (result.meta?.buckets?.length) chartBuckets.value = result.meta.buckets
    } catch (cause) {
      chartError.value = message(cause, 'The log chart could not be read.')
      chart.value = null
    } finally {
      chartLoading.value = false
    }
  }

  return {
    filters,
    page,
    perPage,
    entries,
    meta,
    loading,
    error,
    loadedAt,
    pager,
    levelFacets,
    loggerFacets,
    containerFacets,
    activeFilterCount,
    chart,
    chartContainers,
    chartBuckets,
    chartBucket,
    chartContainer,
    chartLevel,
    chartLoading,
    chartError,
    load,
    apply,
    reset,
    goToPage,
    setPerPage,
    loadChart,
  }
})
